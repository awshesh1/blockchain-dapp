import os
from web3 import Web3
import streamlit as st
import requests
import pandas as pd
from datetime import datetime
import matplotlib.pyplot as plt

# Streamlit setup
st.set_page_config(page_title="Wallet Inspector", layout="centered")

# Connect to Web3 using secret API key
w3 = Web3(Web3.HTTPProvider(st.secrets["WEB3_PROVIDER_URI"]))

# Load contract
contract_address = "0xE8a4d857ABA06af12850131cD047c9Ce73160C2c"
abi = [
    {
        "inputs": [],
        "name": "get",
        "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [{"internalType": "uint256", "name": "_num", "type": "uint256"}],
        "name": "set",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    }
]
contract = w3.eth.contract(address=contract_address, abi=abi)

# UI Title
st.title("📦 SimpleStorage on Sepolia")
st.write("🔌 Connected to Web3:", w3.is_connected())
st.write("📬 Contract Address:", contract_address)

# Show stored value
stored_value = contract.functions.get().call()
st.metric("Stored Value", stored_value)

# Allow user to enter private key and submit transaction
st.markdown("---")
st.subheader("🔐 Submit a New Value")
new_value = st.number_input("Enter a new number to store", min_value=0, step=1)
private_key = st.text_input("Enter your private key", type="password")
submit_clicked = st.button("Submit Transaction")

if submit_clicked:
    if not private_key:
        st.warning("Please enter your private key to submit a transaction.")
        st.stop()

    try:
        account = w3.eth.account.from_key(private_key)
        st.success(f"Wallet loaded: {account.address}")

        with st.spinner("Sending transaction..."):
            nonce = w3.eth.get_transaction_count(account.address)
            tx = contract.functions.set(new_value).build_transaction({
                "from": account.address,
                "nonce": nonce,
                "gas": 100000,
                "gasPrice": w3.to_wei("1", "gwei")
            })

            signed_tx = w3.eth.account.sign_transaction(tx, private_key)
            tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
            receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

            st.success("Transaction confirmed!")
            st.write("🔗 Transaction Hash:", f"https://sepolia.etherscan.io/tx/{tx_hash.hex()}")

            # Log interaction
            log_data = {
                "Block Number": [receipt.blockNumber],
                "Stored Value": [new_value],
                "Timestamp": [datetime.now()],
                "Tx Hash": [tx_hash.hex()]
            }

            log_file = "contract_data_log.xlsx"
            log_df = pd.DataFrame(log_data)
            if os.path.exists(log_file):
                old_df = pd.read_excel(log_file)
                log_df = pd.concat([old_df, log_df], ignore_index=True)
            log_df.to_excel(log_file, index=False)

    except Exception as e:
        st.error(f"❌ Invalid private key: {e}")
        st.stop()

# Show log
st.markdown("---")
st.subheader("📊 Interaction Log")
log_file = "contract_data_log.xlsx"
if os.path.exists(log_file):
    df_log = pd.read_excel(log_file)
    st.dataframe(df_log, use_container_width=True)
    csv = df_log.to_csv(index=False).encode('utf-8')
    st.download_button("⬇️ Download CSV", csv, "contract_log.csv", "text/csv")
else:
    st.info("No log data available yet.")

# NFT Viewer
st.markdown("---")
st.subheader("🖼 NFT Viewer")

def fetch_nfts(owner_address, alchemy_key):
    url = f"https://eth-mainnet.g.alchemy.com/v2/{alchemy_key}/getNFTs?owner={owner_address}"
    response = requests.get(url)
    try:
        return response.json().get("ownedNfts", [])
    except Exception as e:
        st.error(f"Failed to load NFT data: {e}")
        return []

wallet_to_check = st.text_input("Enter wallet address to view NFTs")
if wallet_to_check:
    with st.spinner("Fetching NFTs..."):
        nfts = fetch_nfts(wallet_to_check, st.secrets["ALCHEMY_API_KEY"])
        if isinstance(nfts, list) and nfts:
            for nft in nfts[:10]:
                media = nft.get("media", [{}])
                image_url = media[0].get("gateway", "")
                st.image(image_url, width=200)
                st.write(f"**Name:** {nft.get('title')}")
                st.write(f"**Contract:** {nft.get('contractAddress')}")
                st.write(f"**Token ID:** {nft.get('id', {}).get('tokenId')}")
                st.markdown("---")
        else:
            st.warning("No NFTs found or failed to fetch from Alchemy.")

# Wallet Summary
st.markdown("---")
st.subheader("💰 Wallet Summary")
wallet_summary_addr = st.text_input("Enter wallet address for summary", key="summary")
if wallet_summary_addr:
    with st.spinner("Fetching wallet details..."):
        try:
            # ETH balance
            checksum_address = w3.to_checksum_address(wallet_summary_addr.strip())
            balance_wei = w3.eth.get_balance(checksum_address)
            balance_eth = w3.from_wei(balance_wei, 'ether')
            st.metric("ETH Balance", f"{balance_eth:.4f} ETH")

            # Token balances using Etherscan API
            ETHERSCAN_API_KEY = st.secrets["ETHERSCAN_API_KEY"]
            url = f"https://api.etherscan.io/api?module=account&action=tokentx&address={checksum_address}&sort=desc&apikey={ETHERSCAN_API_KEY}"
            res = requests.get(url)
            tokens = {}
            token_transactions = []

            if res.status_code == 200:
                try:
                    data = res.json()
                    if isinstance(data.get("result"), list):
                        for tx in data["result"][:50]:
                            if isinstance(tx, dict):
                                token = tx.get("tokenName")
                                value = int(tx.get("value")) / (10 ** int(tx.get("tokenDecimal", 18)))
                                if token:
                                    tokens[token] = tokens.get(token, 0) + value
                                    token_transactions.append({
                                        "Token": token,
                                        "Value": value,
                                        "From": tx.get("from"),
                                        "To": tx.get("to"),
                                        "Hash": tx.get("hash"),
                                        "TimeStamp": tx.get("timeStamp")
                                    })
                    else:
                        st.warning("Etherscan returned an unexpected structure.")
                        st.json(data)
                except Exception as parse_err:
                    st.error(f"Failed to parse Etherscan response: {parse_err}")

            if tokens:
                st.subheader("🔹 Token Holdings")
                token_df = pd.DataFrame(tokens.items(), columns=["Token", "Approx. Total"])
                st.dataframe(token_df, use_container_width=True)

                # Pie chart
                fig, ax = plt.subplots()
                ax.pie(token_df["Approx. Total"], labels=token_df["Token"], autopct='%1.1f%%', startangle=90)
                ax.axis('equal')
                st.pyplot(fig)
            else:
                st.info("No token transactions found.")

            if token_transactions:
                st.subheader("Recent Token Transactions")
                tx_df = pd.DataFrame(token_transactions)
                tx_df["TimeStamp"] = pd.to_datetime(tx_df["TimeStamp"], unit='s')
                st.dataframe(tx_df[["TimeStamp", "Token", "Value", "From", "To", "Hash"]], use_container_width=True)

            # NFT count via Alchemy
            alchemy_key = st.secrets["ALCHEMY_API_KEY"]
            nft_url = f"https://eth-mainnet.g.alchemy.com/v2/{alchemy_key}/getNFTs?owner={checksum_address}"
            nft_res = requests.get(nft_url)
            if nft_res.status_code == 200:
                nft_data = nft_res.json()
                nft_count = len(nft_data.get("ownedNfts", []))
                st.metric("NFTs Owned", nft_count)

        except Exception as e:
            st.error(f"Error: {e}")

# Next step: Add ERC-20 Token Transfer History Viewer

# Add this below your Wallet Summary section

st.markdown("---")
st.subheader("🔁 ERC-20 Token Transfer History")

wallet_history_addr = st.text_input("Enter wallet address to view token transfers", key="history")

if wallet_history_addr:
    with st.spinner("Fetching token transfers..."):
        try:
            ETHERSCAN_API_KEY = st.secrets["ETHERSCAN_API_KEY"]
            url = f"https://api.etherscan.io/api?module=account&action=tokentx&address={wallet_history_addr}&sort=desc&apikey={ETHERSCAN_API_KEY}"
            res = requests.get(url)
            if res.status_code == 200:
                data = res.json()
                result = data.get("result", [])
                if isinstance(result, list) and result:
                    df_history = pd.DataFrame(result)

                    # Clean and format
                    df_history["TimeStamp"] = pd.to_datetime(df_history["timeStamp"], unit='s')
                    df_history["Value"] = df_history.apply(lambda x: int(x["value"]) / (10 ** int(x.get("tokenDecimal", 18))), axis=1)
                    df_history = df_history[["TimeStamp", "tokenName", "Value", "from", "to", "hash"]]
                    df_history.columns = ["TimeStamp", "Token", "Value", "From", "To", "Tx Hash"]

                    # Token filter
                    unique_tokens = df_history["Token"].unique().tolist()
                    selected_tokens = st.multiselect("Filter by token name", options=unique_tokens, default=unique_tokens)

                    filtered_df = df_history[df_history["Token"].isin(selected_tokens)]
                    st.dataframe(filtered_df, use_container_width=True)

                    # CSV download
                    csv = filtered_df.to_csv(index=False).encode("utf-8")
                    st.download_button("⬇️ Download CSV", csv, "token_transfers.csv", "text/csv")

                else:
                    st.info("No token transfer history available for this address.")
            else:
                st.error("Failed to fetch data from Etherscan.")

        except Exception as e:
            st.error(f"Error fetching token transfers: {e}")

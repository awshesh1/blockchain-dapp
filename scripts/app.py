import os
from web3 import Web3
import streamlit as st
import requests
import pandas as pd
from datetime import datetime

# Streamlit setup
st.set_page_config(page_title="SimpleStorage dApp", layout="centered")

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

new_value = st.number_input("Enter a new number to store", min_value=0, step=1)
submit_clicked = st.button("Submit")

if submit_clicked:
    private_key = st.text_input("🔐 Enter your private key", type="password")

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

# Optional: Private Key


# Allow writing only if key is valid

# Only require private key if user clicks Submit
if st.button("Submit",key="submit_set_value"):
    private_key = st.text_input("🔐 Enter your private key", type="password")
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
            from datetime import datetime
            log_data = {
                "Block Number": [receipt.blockNumber],
                "Stored Value": [new_value],
                "Timestamp": [datetime.now()],
                "Tx Hash": [tx_hash.hex()]
            }

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
    if response.status_code == 200:
        return response.json().get("ownedNfts", [])
    return []

wallet_to_check = st.text_input("Enter wallet address to view NFTs")
if wallet_to_check:
    with st.spinner("Fetching NFTs..."):
        nfts = fetch_nfts(wallet_to_check, st.secrets["ALCHEMY_API_KEY"])
        if not nfts:
            st.warning("No NFTs found or failed to fetch.")
        else:
            for nft in nfts[:10]:
                media = nft.get("media", [{}])
                image_url = media[0].get("gateway", "")
                st.image(image_url, width=200)
                st.write(f"**Name:** {nft.get('title')}")
                st.write(f"**Contract:** {nft.get('contractAddress')}")
                st.write(f"**Token ID:** {nft.get('id', {}).get('tokenId')}")
                st.markdown("---")


st.markdown("---")
st.subheader("💰 Wallet Summary")

wallet_summary_addr = st.text_input("Enter wallet address for summary", key="summary")

if wallet_summary_addr:
    with st.spinner("Fetching wallet details..."):
        try:
            # ETH balance
            balance_wei = w3.eth.get_balance(wallet_summary_addr)
            balance_eth = w3.from_wei(balance_wei, 'ether')
            st.metric("ETH Balance", f"{balance_eth:.4f} ETH")

            # Token balances using Etherscan API
            ETHERSCAN_API_KEY = st.secrets["ETHERSCAN_API_KEY"]
            url = f"https://api.etherscan.io/api?module=account&action=tokentx&address={wallet_summary_addr}&sort=desc&apikey={ETHERSCAN_API_KEY}"
            res = requests.get(url)
            tokens = {}
            if res.status_code == 200:
                data = res.json()
                for tx in data.get("result", [])[:50]:
                    token = tx.get("tokenName")
                    value = int(tx.get("value")) / (10 ** int(tx.get("tokenDecimal", 18)))
                    if token:
                        tokens[token] = tokens.get(token, 0) + value

            if tokens:
                st.subheader("🔹 Token Holdings")
                token_df = pd.DataFrame(tokens.items(), columns=["Token", "Approx. Total"])
                st.dataframe(token_df, use_container_width=True)
            else:
                st.info("No token transactions found.")

        except Exception as e:
            st.error(f"Error: {e}")

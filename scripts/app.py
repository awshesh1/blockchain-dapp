import os
from web3 import Web3
import streamlit as st
import requests
import pandas as pd
from datetime import datetime
import matplotlib.pyplot as plt
import json

# Streamlit setup
st.set_page_config(page_title="Wallet Inspector", layout="centered")

# Connect to Web3 using secret API key
w3 = Web3(Web3.HTTPProvider(st.secrets["WEB3_PROVIDER_URI"]))

# Load contract
contract_address = "0xE8a4d857ABA06af12850131cD047c9Ce73160C2c"
abi = [
    {"inputs": [], "name": "get", "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}], "stateMutability": "view", "type": "function"},
    {"inputs": [{"internalType": "uint256", "name": "_num", "type": "uint256"}], "name": "set", "outputs": [], "stateMutability": "nonpayable", "type": "function"}
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

# --- NFT Viewer Section ---
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
                title = nft.get("title", "N/A")
                contract_address = nft.get("contractAddress", "N/A")
                token_id = nft.get("id", {}).get("tokenId", "N/A")

                st.image(image_url, width=200)
                st.write(f"**Name:** {title}")
                st.write(f"**Contract:** {contract_address}")
                st.write(f"**Token ID:** {token_id}")

                # Expandable metadata view
                with st.expander("📋 View Metadata"):
                    metadata = nft.get("metadata", {})
                    desc = metadata.get("description", "No description available.")
                    attrs = metadata.get("attributes", [])
                    st.write(f"**Description:** {desc}")
                    if attrs:
                        attr_df = pd.DataFrame(attrs)
                        st.write("**Attributes:**")
                        st.dataframe(attr_df)
                    else:
                        st.info("No attributes found.")
                    external_url = metadata.get("external_url")
                    if external_url:
                        st.markdown(f"[🔗 External Link]({external_url})")
                st.markdown("---")
        else:
            st.warning("No NFTs found or failed to fetch from Alchemy.")

# --- Import next enhancements as separate modular blocks after this line in new updates ---
# Wallet Snapshot Timeline Graph
st.markdown("---")
st.subheader("📈 Wallet Snapshot Timeline Graph")

timeline_addr = st.text_input("Enter wallet address for timeline graph", key="snapshot_graph")

if timeline_addr:
    with st.spinner("Generating timeline graph..."):
        try:
            ETHERSCAN_API_KEY = st.secrets["ETHERSCAN_API_KEY"]
            url = f"https://api.etherscan.io/api?module=account&action=tokentx&address={timeline_addr}&sort=asc&apikey={ETHERSCAN_API_KEY}"
            res = requests.get(url)

            if res.status_code == 200:
                data = res.json().get("result", [])
                if data:
                    df = pd.DataFrame(data)
                    df["TimeStamp"] = pd.to_datetime(df["timeStamp"], unit="s")
                    df["tokenDecimal"] = pd.to_numeric(df["tokenDecimal"], errors="coerce").fillna(18).astype(int)
                    df["Value"] = df.apply(lambda x: int(x["value"]) / (10 ** x["tokenDecimal"]), axis=1)
                    df["tokenName"] = df["tokenName"].fillna("Unknown Token")

                    # Group by date and token
                    df["Date"] = df["TimeStamp"].dt.date
                    daily_summary = df.groupby(["Date", "tokenName"])["Value"].sum().reset_index()

                    # Pivot for stacked area chart
                    pivot_df = daily_summary.pivot(index="Date", columns="tokenName", values="Value").fillna(0)

                    # Plot
                    st.line_chart(pivot_df)

                    # CSV export
                    csv = pivot_df.reset_index().to_csv(index=False).encode("utf-8")
                    st.download_button("⬇️ Download Timeline Data", csv, "wallet_snapshot_timeline.csv", "text/csv", key="wallet_snapshot_csv")

                else:
                    st.info("No token transfers found for this address.")
            else:
                st.error("Failed to fetch data from Etherscan.")

        except Exception as e:
            st.error(f"Error generating snapshot timeline: {e}")


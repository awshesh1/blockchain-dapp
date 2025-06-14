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

# Submit new value
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
st.subheader("🔁 ERC-20 Token Transfer History")
wallet_history_addr = st.text_input("Enter wallet address to view token transfers", key="history")

if wallet_history_addr:
    with st.spinner("Fetching token transfers..."):
        st.subheader("📊 Interaction Log")
log_file = "contract_data_log.xlsx"
if os.path.exists(log_file):
    df_log = pd.read_excel(log_file)
    st.dataframe(df_log, use_container_width=True)
    csv = df_log.to_csv(index=False).encode('utf-8')
    st.download_button("⬇️ Download CSV", csv, "contract_log.csv", "text/csv", key="download_wallet_history_button")
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

# Wallet Snapshot Timeline Graph
st.markdown("---")
st.subheader("📅 Wallet Snapshot Timeline Graph")
snapshot_dir = "wallet_snapshots"
os.makedirs(snapshot_dir, exist_ok=True)

def load_all_snapshots():
    snapshots = []
    for file in os.listdir(snapshot_dir):
        if file.endswith(".json"):
            path = os.path.join(snapshot_dir, file)
            with open(path, "r") as f:
                data = json.load(f)
                data["Timestamp"] = datetime.fromtimestamp(os.path.getmtime(path))
                snapshots.append(data)
    return pd.DataFrame(snapshots) if snapshots else pd.DataFrame()

if st.button("👀 Show Timeline Graph"):
    df_snapshots = load_all_snapshots()
    if df_snapshots.empty:
        st.info("No wallet snapshots found.")
    else:
        df_snapshots.sort_values("Timestamp", inplace=True)
        fig, ax1 = plt.subplots()
        ax1.plot(df_snapshots["Timestamp"], df_snapshots["eth_balance"].str.replace(" ETH", "").astype(float), marker='o')
        ax1.set_xlabel("Timestamp")
        ax1.set_ylabel("ETH Balance")
        ax1.set_title("ETH Balance Over Time")
        ax1.grid(True)
        st.pyplot(fig)
        st.dataframe(df_snapshots)
        csv = df_snapshots.to_csv(index=False).encode("utf-8")
        st.download_button("⬇️ Download Timeline CSV", csv, "wallet_snapshot_timeline.csv", "text/csv")

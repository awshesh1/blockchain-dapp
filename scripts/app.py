import os
from web3 import Web3
import streamlit as st
import requests

from dotenv import load_dotenv
import pandas as pd

load_dotenv()

st.set_page_config(page_title="SimpleStorage dApp", layout="centered")

# Connect to Web3
#w3 = Web3(Web3.HTTPProvider(os.getenv("WEB3_PROVIDER_URI")))

# Connect to Ethereum
w3 = Web3(Web3.HTTPProvider(f"https://eth-sepolia.g.alchemy.com/v2/st.secrets{['GVu7Zjue3tFE8u8-_ZcvJXjljnVw0DL0']}"))

# Get private key from user
# This block is ONLY for interacting with contract
private_key = st.text_input("🔐 Enter your private key", type="password")

if private_key:
    try:
        account = w3.eth.account.from_key(private_key)
        st.success(f"Wallet loaded: {account.address}")
        
        # ... build transaction and submit code here ...
        
    except Exception as e:
        st.error(f"❌ Invalid private key: {e}")


contract_address = "0xE8a4d857ABA06af12850131cD047c9Ce73160C2c"

# SimpleStorage ABI
abi = [{
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
}]

contract = w3.eth.contract(address=contract_address, abi=abi)

# UI
st.title("📦 SimpleStorage on Sepolia")

st.write("🔌 Connected to Web3:", w3.is_connected())
st.write("📬 Address:", contract_address)
st.write("📦 Contract:", contract.functions)



# Display current stored value
stored_value = contract.functions.get().call()
st.metric("Stored Value", stored_value)

# Input for new value
new_value = st.number_input("Enter a new number to store", min_value=0, step=1)
log_file = "contract_data_log.xlsx"

if st.button("Submit"):
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
        # Log interaction to Excel
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

        st.write("🔗 Transaction Hash:", f"https://sepolia.etherscan.io/tx/{tx_hash.hex()}")

import pandas as pd

st.markdown("---")
st.subheader("📊 Interaction Log")



if os.path.exists(log_file):
    df_log = pd.read_excel(log_file)
    st.dataframe(df_log, use_container_width=True)

    # CSV download
    csv = df_log.to_csv(index=False).encode('utf-8')
    st.download_button("⬇️ Download CSV", csv, "contract_log.csv", "text/csv")
else:
    st.info("No log data available yet.")


def fetch_nfts(owner_address, alchemy_key):
    url = f"https://eth-mainnet.g.alchemy.com/v2/{alchemy_key}/getNFTs?owner={owner_address}"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json().get("ownedNfts", [])
    else:
        return []


st.markdown("---")
st.subheader("🖼 NFT Viewer")

wallet_to_check = st.text_input("Enter wallet address to view NFTs")
if wallet_to_check:
    with st.spinner("Fetching NFTs..."):
        nfts = fetch_nfts(wallet_to_check, st.secrets["ALCHEMY_API_KEY"])
        if not nfts:
            st.warning("No NFTs found or failed to fetch.")
        else:
            for nft in nfts[:10]:  # show top 10
                media = nft.get("media", [{}])
                image_url = media[0].get("gateway", "")
                st.image(image_url, width=200)
                st.write(f"**Name:** {nft.get('title')}")
                st.write(f"**Contract:** {nft.get('contractAddress')}")
                st.write(f"**Token ID:** {nft.get('id', {}).get('tokenId')}")
                st.markdown("---")

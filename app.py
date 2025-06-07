import os
from web3 import Web3
import streamlit as st


from dotenv import load_dotenv
import pandas as pd

load_dotenv()

st.set_page_config(page_title="SimpleStorage dApp", layout="centered")

# Connect to Web3
w3 = Web3(Web3.HTTPProvider(os.getenv("WEB3_PROVIDER_URI")))

# Connect to Ethereum
w3 = Web3(Web3.HTTPProvider("https://eth-sepolia.g.alchemy.com/v2/GVu7Zjue3tFE8u8-_ZcvJXjljnVw0DL0"))

# Get private key from user
private_key = st.text_input("🔐 Enter your private key", type="password")

if private_key:
    try:
        account = w3.eth.account.from_key(private_key)
        st.success(f"Wallet loaded: {account.address}")
    except Exception as e:
        st.error(f"❌ Invalid private key: {e}")
        st.stop()
else:
    st.warning("Please enter your private key to continue.")
    st.stop()


contract_address = "0x1c5afd90714E2a40547246DDD92668F2715caF78"

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

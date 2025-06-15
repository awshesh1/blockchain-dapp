import os
import json
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
from moralis_sdk import evm_api
from cachetools import TTLCache
from web3 import Web3

# Initialize Streamlit
st.set_page_config(page_title="Wallet Inspector Pro", layout="centered")

# Initialize Moralis (replace with your API key)
MORALIS_API_KEY = st.secrets["MORALIS_API_KEY"]
evm_api.api_key = MORALIS_API_KEY

# Initialize Web3 (fallback)
w3 = Web3(Web3.HTTPProvider(st.secrets["WEB3_PROVIDER_URI"]))

# Cache setup (5-minute TTL)
cache = TTTCache(maxsize=1000, ttl=300)

# Tab structure
st.title("🚀 Wallet Inspector Pro")
tabs = st.tabs([
    "📊 Dashboard",
    "🔍 NFT Explorer",
    "📈 Token Analytics",
    "🛡️ Security Scan",
    "⚙️ Settings"
])

# Helper functions
@st.cache_data
def get_wallet_balance(address, chain="eth"):
    try:
        result = evm_api.balance.get_native_balance(address=address, chain=chain)
        return int(result["balance"])
    except Exception as e:
        st.error(f"Moralis error: {e}")
        return w3.eth.get_balance(address)

def get_token_transfers(address, chain="eth"):
    cache_key = f"token_transfers_{address}_{chain}"
    if cache_key in cache:
        return cache[cache_key]
    
    try:
        result = evm_api.token.get_wallet_token_transfers(address=address, chain=chain)
        cache[cache_key] = result
        return result
    except Exception as e:
        st.error(f"Failed to fetch token transfers: {e}")
        return []

# 1. Dashboard Tab
with tabs[0]:
    st.header("📊 Wallet Dashboard")
    wallet_address = st.text_input("Enter Wallet Address", key="dashboard_addr")
    chain = st.selectbox("Select Chain", ["eth", "polygon", "bsc"], key="chain_select")
    
    if wallet_address:
        col1, col2 = st.columns(2)
        
        with col1:
            with st.spinner("Fetching balance..."):
                balance = get_wallet_balance(wallet_address, chain)
                st.metric(f"{chain.upper()} Balance", f"{balance / 10**18:.4f}")
                
        with col2:
            with st.spinner("Checking NFTs..."):
                nft_count = len(evm_api.nft.get_wallet_nfts(address=wallet_address, chain=chain))
                st.metric("NFT Count", nft_count)
        
        st.subheader("Recent Activity")
        transfers = get_token_transfers(wallet_address, chain)[:20]
        if transfers:
            df = pd.DataFrame([{
                "Date": datetime.fromtimestamp(int(tx["block_timestamp"])),
                "Token": tx.get("token_name", "Unknown"),
                "Value": int(tx["value"]) / (10 ** int(tx.get("token_decimals", 18))),
                "Direction": "IN" if tx["to_address"].lower() == wallet_address.lower() else "OUT",
                "Tx Hash": tx["transaction_hash"]
            } for tx in transfers])
            st.dataframe(df, use_container_width=True)
        else:
            st.warning("No recent activity found")

# 2. NFT Explorer Tab
with tabs[1]:
    st.header("🖼 NFT Explorer")
    nft_address = st.text_input("Enter Wallet Address", key="nft_addr")
    nft_chain = st.selectbox("Select Chain", ["eth", "polygon", "bsc"], key="nft_chain")
    
    if nft_address:
        with st.spinner("Loading NFTs..."):
            nfts = evm_api.nft.get_wallet_nfts(address=nft_address, chain=nft_chain)
            if nfts:
                cols = st.columns(3)
                for i, nft in enumerate(nfts[:9]):
                    with cols[i%3]:
                        st.image(nft["normalized_metadata"].get("image", ""), width=150)
                        st.caption(nft["name"])
            else:
                st.info("No NFTs found")

# 3. Token Analytics Tab
with tabs[2]:
    st.header("📈 Token Analytics")
    token_address = st.text_input("Enter Wallet Address", key="token_addr")
    
    if token_address:
        with st.spinner("Analyzing tokens..."):
            tokens = evm_api.token.get_wallet_token_balances(address=token_address, chain="eth")
            if tokens:
                df = pd.DataFrame([{
                    "Token": t["name"],
                    "Symbol": t["symbol"],
                    "Balance": int(t["balance"]) / (10 ** int(t["decimals"])),
                    "Value (USD)": float(t.get("usd_price", 0)) * (int(t["balance"]) / (10 ** int(t["decimals"])))
                } for t in tokens if int(t["balance"]) > 0])
                
                if not df.empty:
                    st.dataframe(df, use_container_width=True)
                    
                    fig, ax = plt.subplots()
                    df.plot.pie(y="Value (USD)", labels=df["Symbol"], ax=ax)
                    st.pyplot(fig)
                else:
                    st.warning("No token balances found")
            else:
                st.warning("Failed to fetch token data")

# 4. Security Scan Tab
with tabs[3]:
    st.header("🛡️ Security Scan")
    scan_address = st.text_input("Enter Wallet Address", key="scan_addr")
    
    if scan_address:
        with st.spinner("Running security checks..."):
            # Check for token approvals
            approvals = evm_api.token.get_token_allowances(
                address=scan_address,
                chain="eth"
            )
            
            risky_approvals = [a for a in approvals if int(a["value"]) > 0]
            
            if risky_approvals:
                st.warning(f"⚠️ Found {len(risky_approvals)} token approvals")
                for approval in risky_approvals[:5]:
                    st.error(f"Approval to {approval['to_address']} for {approval['symbol']}")
            else:
                st.success("✅ No risky token approvals found")

# 5. Settings Tab
with tabs[4]:
    st.header("⚙️ Settings")
    
    if st.button("Clear Cache"):
        cache.clear()
        st.success("Cache cleared!")
    
    st.subheader("API Status")
    st.code(f"Moralis: {'✅ Active' if MORALIS_API_KEY else '❌ Inactive'}")
    st.code(f"Web3: {'✅ Connected' if w3.is_connected() else '❌ Disconnected'}")
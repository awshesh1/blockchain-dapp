import os
import json
import requests
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
from web3 import Web3
from cachetools import TTLCache

# Initialize with caching
cache = TTLCache(maxsize=1000, ttl=300)
st.set_page_config(page_title="Wallet Inspector Pro", layout="centered")

# Initialize Web3
w3 = Web3(Web3.HTTPProvider(st.secrets["WEB3_PROVIDER_URI"]))

# Moralis API Helper
def moralis_api(endpoint, params={}, chain="eth"):
    cache_key = f"{endpoint}_{chain}_{str(params)}"
    if cache_key in cache:
        return cache[cache_key]
    
    url = f"https://deep-index.moralis.io/api/v2/{endpoint}"
    headers = {"X-API-Key": st.secrets["MORALIS_API_KEY"]}
    params["chain"] = chain
    
    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        data = response.json()
        cache[cache_key] = data
        return data
    except Exception as e:
        st.error(f"API Error: {str(e)}")
        return None

# Tab Structure
tabs = st.tabs([
    "📦 SimpleStorage", 
    "📜 Transaction History",
    "🖼 NFT Viewer",
    "💰 Wallet Summary",
    "🔁 Token Transfers",
    "⏳ Activity Timeline"
])

# 1. SimpleStorage Contract (UNCHANGED)
with tabs[0]:
    # ... [Keep your existing SimpleStorage code] ...

# 2. Transaction History (Modified)
with tabs[1]:
    wallet_address = st.text_input("Enter Wallet Address", key="history_addr")
    if wallet_address:
        data = moralis_api(f"{wallet_address}/erc20/transfers", {"limit": 50})
        if data:
            df = pd.DataFrame(data["result"])
            st.dataframe(df[["block_number", "to_address", "value", "token_symbol"]])
            
# 3. NFT Viewer (Modified)
with tabs[2]:
    nft_address = st.text_input("Enter Wallet Address", key="nft_addr")
    if nft_address:
        nfts = moralis_api(f"{nft_address}/nft", {"limit": 12})
        if nfts:
            cols = st.columns(3)
            for i, nft in enumerate(nfts["result"][:12]):
                with cols[i%3]:
                    st.image(nft.get("normalized_metadata", {}).get("image"), width=150)
                    st.caption(nft.get("name"))

# 4. Wallet Summary (Modified)
with tabs[3]:
    wallet_address = st.text_input("Enter Wallet Address", key="summary_addr")
    if wallet_address:
        # Native Balance
        balance = moralis_api(f"{wallet_address}/balance")
        st.metric("Native Balance", f"{int(balance['balance'])/10**18:.4f} ETH")
        
        # Token Balances
        tokens = moralis_api(f"{wallet_address}/erc20")
        if tokens:
            token_df = pd.DataFrame(tokens["result"])
            st.dataframe(token_df[["symbol", "balance", "decimals"]])

# 5. Token Transfers (Modified)
with tabs[4]:
    wallet_address = st.text_input("Enter Wallet Address", key="token_addr")
    if wallet_address:
        transfers = moralis_api(f"{wallet_address}/erc20/transfers")
        if transfers:
            st.area_chart(pd.DataFrame(transfers["result"]).set_index("block_number"))

# 6. Activity Timeline (Modified)
with tabs[5]:
    wallet_address = st.text_input("Enter Wallet Address", key="timeline_addr")
    if wallet_address:
        logs = moralis_api(f"{wallet_address}/logs", {"limit": 50})
        if logs:
            timeline_df = pd.DataFrame(logs["result"])
            st.line_chart(timeline_df.set_index("block_timestamp"))
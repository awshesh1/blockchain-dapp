import requests
import os
from dotenv import load_dotenv

load_dotenv()

ETHERSCAN_API_KEY = os.getenv("ETHERSCAN_API_KEY")
CONTRACT_ADDRESS = "0x1c5afd90714E2a40547246DDD92668F2715caF78"  # Replace with your deployed contract
FUNCTION_SIG = "0x6d4ce63c"  # This is the function selector for `get()` in SimpleStorage

def read_value_from_etherscan():
    url = f"https://api-sepolia.etherscan.io/api"
    params = {
        "module": "proxy",
        "action": "eth_call",
        "to": CONTRACT_ADDRESS,
        "data": FUNCTION_SIG,
        "tag": "latest",
        "apikey": ETHERSCAN_API_KEY
    }

    response = requests.get(url, params=params)
    result = response.json()

    if result.get("result"):
        value_hex = result["result"]
        value_int = int(value_hex, 16)
        print(f"📦 Stored value from Etherscan: {value_int}")
    else:
        print("❌ Error fetching data:", result)

if __name__ == "__main__":
    read_value_from_etherscan()

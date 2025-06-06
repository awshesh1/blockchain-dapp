import os
import pandas as pd
from dotenv import load_dotenv
from web3 import Web3

load_dotenv()

w3 = Web3(Web3.HTTPProvider(os.getenv("WEB3_PROVIDER_URI")))
contract_address = "0x1c5afd90714E2a40547246DDD92668F2715caF78"
abi = [{
    "inputs": [],
    "name": "get",
    "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
    "stateMutability": "view",
    "type": "function"
}]

def log_to_excel():
    contract = w3.eth.contract(address=contract_address, abi=abi)
    value = contract.functions.get().call()

    block = w3.eth.get_block("latest")
    tx_count = w3.eth.get_block_transaction_count(block.number)

    data = {
        "Block Number": [block.number],
        "Stored Value": [value],
        "Timestamp": [pd.to_datetime(block.timestamp, unit='s')],
        "Tx Count in Block": [tx_count]
    }

    df = pd.DataFrame(data)

    file_name = "contract_data_log.xlsx"

    if os.path.exists(file_name):
        old_df = pd.read_excel(file_name)
        df = pd.concat([old_df, df], ignore_index=True)

    df.to_excel(file_name, index=False)
    print(f"✅ Logged to {file_name}")

if __name__ == "__main__":
    log_to_excel()

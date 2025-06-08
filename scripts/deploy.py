from brownie import SimpleStorage, accounts
import os
from dotenv import load_dotenv

load_dotenv()

def main():
    acct = accounts.add(os.getenv("PRIVATE_KEY"))
    contract = SimpleStorage.deploy({"from": acct})
    print(f"Contract deployed at: {contract.address}")

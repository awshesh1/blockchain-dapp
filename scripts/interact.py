from brownie import SimpleStorage, accounts
import os
from dotenv import load_dotenv

load_dotenv()

def main():
    # Load your deployer account
    acct = accounts.add(os.getenv("PRIVATE_KEY"))

    # Load most recent deployed instance of SimpleStorage
    contract = SimpleStorage[-1]
    print(f"🔗 Contract at: {contract.address}")

    # Step 1: Read the current value
    current_value = contract.get()
    print(f"📦 Current stored value: {current_value}")

    # Step 2: Set a new value (e.g., 42)
    tx = contract.set(42, {"from": acct})
    tx.wait(1)
    print("✅ Value updated.")

    # Step 3: Read updated value
    new_value = contract.get()
    print(f"📦 New stored value: {new_value}")

"""Seed Cosmos DB with mock banking data for all 3 personas."""
import asyncio
import json
from azure.cosmos.aio import CosmosClient
from azure.identity.aio import DefaultAzureCredential
from backend.shared.mock_data.generator import generate_all_mock_data

COSMOS_ENDPOINT = "https://bnb-cosmos-db2026.documents.azure.com:443/"


async def seed():
    credential = DefaultAzureCredential()
    client = CosmosClient(COSMOS_ENDPOINT, credential=credential)
    db = client.get_database_client("bnb-db")
    data = generate_all_mock_data()

    # Seed accounts + customers
    acct_container = db.get_container_client("accounts")
    for acct in data["accounts"]:
        doc = acct.model_dump(mode="json")
        doc["id"] = doc["account_id"]
        doc["type"] = "account"
        await acct_container.upsert_item(doc)
        print(f"  Account: {doc['id']}")

    for cust in data["customers"]:
        doc = cust.model_dump(mode="json")
        doc["id"] = doc["customer_id"]
        doc["type"] = "customer"
        doc["created_at"] = str(doc["created_at"])
        await acct_container.upsert_item(doc)
        print(f"  Customer: {doc['id']} ({doc['name']})")

    # Seed transactions
    txn_container = db.get_container_client("transactions")
    total_txn = 0
    for cust_id, txns in data["transactions"].items():
        for txn in txns:
            doc = txn.model_dump(mode="json")
            doc["id"] = doc["transaction_id"]
            doc["date"] = str(doc["date"])
            await txn_container.upsert_item(doc)
            total_txn += 1
        print(f"  {cust_id}: {len(txns)} transactions")

    print(f"\nTotal: {len(data['customers'])} customers, {len(data['accounts'])} accounts, {total_txn} transactions")
    await client.close()
    await credential.close()
    print("Cosmos DB seeded successfully!")


if __name__ == "__main__":
    asyncio.run(seed())

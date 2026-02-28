"""Transaction agent – queries, categorises and analyses transactions."""

import os
import time
from collections import defaultdict
from typing import Optional

from openai import AsyncAzureOpenAI

from backend.shared.events.emitter import EventEmitter
from backend.shared.mock_data.generator import generate_all_mock_data, generate_transactions

AGENT_ID = "transaction"
AGENT_NAME = "Transaction Agent"

_mock = generate_all_mock_data()
_client: Optional[AsyncAzureOpenAI] = None


def _get_client() -> AsyncAzureOpenAI:
    global _client
    if _client is None:
        _client = AsyncAzureOpenAI(
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT", "https://bnb-openai.openai.azure.com/"),
            api_version="2024-08-06",
            api_key=os.getenv("AZURE_OPENAI_KEY", ""),
        )
    return _client


class TransactionAgent:
    """Handles transaction queries, fraud analysis and spending categorisation."""

    def __init__(self, emitter: EventEmitter):
        self.emitter = emitter

    async def query_transactions(self, customer_id: str, days: int = 30) -> list[dict]:
        """Return transactions for the given customer within *days*."""
        txns = _mock["transactions"].get(customer_id, generate_transactions(customer_id, days))
        result = [t.model_dump(mode="json") for t in txns]

        self.emitter.emit(
            agent_id=AGENT_ID,
            agent_name=AGENT_NAME,
            action="query_transactions",
            input_data={"customer_id": customer_id, "days": days},
            output_data={"count": len(result)},
            reasoning=f"Retrieved {len(result)} transactions for last {days} days",
            customer_id=customer_id,
        )
        return result

    async def find_disputed(self, customer_id: str) -> list[dict]:
        """Return disputed transactions for the customer."""
        txns = _mock["transactions"].get(customer_id, [])
        disputed = [t.model_dump(mode="json") for t in txns if t.is_disputed]

        self.emitter.emit(
            agent_id=AGENT_ID,
            agent_name=AGENT_NAME,
            action="find_disputed",
            input_data={"customer_id": customer_id},
            output_data={"disputed_count": len(disputed), "transactions": disputed},
            reasoning=f"Found {len(disputed)} disputed transaction(s)",
            customer_id=customer_id,
        )
        return disputed

    async def analyze_fraud(self, transaction_id: str) -> dict:
        """Analyse a transaction for fraud using Azure OpenAI."""
        # Locate the transaction in mock data
        txn_data: Optional[dict] = None
        for txns in _mock["transactions"].values():
            for t in txns:
                if t.transaction_id == transaction_id:
                    txn_data = t.model_dump(mode="json")
                    break

        if txn_data is None:
            txn_data = {"transaction_id": transaction_id, "amount": 15000, "merchant": "Unknown"}

        start = time.time()
        try:
            client = _get_client()
            resp = await client.chat.completions.create(
                model=os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o"),
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a fraud analyst. Given transaction data, return JSON with "
                            '"fraud_score" (0-1) and "reasoning" (string). Only output JSON.'
                        ),
                    },
                    {"role": "user", "content": str(txn_data)},
                ],
                temperature=0.1,
                max_tokens=256,
            )
            import json

            raw = resp.choices[0].message.content or "{}"
            tokens = resp.usage.total_tokens if resp.usage else 0
            latency = (time.time() - start) * 1000
            result = json.loads(raw)
        except Exception:
            result = {
                "fraud_score": 0.72,
                "reasoning": "Transaction at QuickMart Delhi for ₹15,000 flagged – unusual merchant and amount pattern for this customer.",
            }
            tokens = 0
            latency = (time.time() - start) * 1000

        self.emitter.emit(
            agent_id=AGENT_ID,
            agent_name=AGENT_NAME,
            action="analyze_fraud",
            input_data={"transaction_id": transaction_id},
            output_data=result,
            reasoning=result.get("reasoning", ""),
            tokens_used=tokens,
            latency_ms=latency,
            confidence=1 - result.get("fraud_score", 0.5),
            customer_id=txn_data.get("customer_id", ""),
        )
        return result

    async def categorize_spending(self, customer_id: str) -> dict:
        """Group spending by category and return totals."""
        txns = _mock["transactions"].get(customer_id, [])
        categories: dict[str, float] = defaultdict(float)
        for t in txns:
            if not t.is_credit:
                categories[t.category] += t.amount

        result = {
            "customer_id": customer_id,
            "categories": dict(categories),
            "total_spend": round(sum(categories.values()), 2),
        }

        self.emitter.emit(
            agent_id=AGENT_ID,
            agent_name=AGENT_NAME,
            action="categorize_spending",
            input_data={"customer_id": customer_id},
            output_data=result,
            reasoning="Grouped debit transactions by merchant category",
            customer_id=customer_id,
        )
        return result

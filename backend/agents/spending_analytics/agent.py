"""Spending analytics agent – analyses spending patterns and detects anomalies (UC3)."""

import os
import time
from collections import defaultdict
from typing import Optional

from openai import AsyncAzureOpenAI

from backend.shared.events.emitter import EventEmitter
from backend.shared.mock_data.generator import generate_all_mock_data

AGENT_ID = "spending_analytics"
AGENT_NAME = "Spending Analytics Agent"

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


class SpendingAnalyticsAgent:
    """Analyses customer spending patterns for proactive insights (UC3)."""

    def __init__(self, emitter: EventEmitter):
        self.emitter = emitter

    async def analyze_spending(self, customer_id: str, days: int = 7) -> dict:
        """Analyse transactions by category and compare with historical averages."""
        txns = _mock["transactions"].get(customer_id, [])
        debits = [t for t in txns if not t.is_credit]

        by_category: dict[str, float] = defaultdict(float)
        for t in debits:
            by_category[t.category] += t.amount

        # Mock historical averages (30-day monthly average scaled to period)
        historical_avg: dict[str, float] = {
            "Food": 4500.0,
            "Shopping": 6000.0,
            "Utilities": 3000.0,
            "Transport": 2000.0,
            "Groceries": 3500.0,
            "Travel": 2500.0,
            "Health": 1500.0,
            "Entertainment": 1000.0,
            "Tax": 5000.0,
        }

        comparisons = {}
        for cat, total in by_category.items():
            avg = historical_avg.get(cat, 3000.0)
            pct_change = round(((total - avg) / avg) * 100, 1) if avg else 0.0
            comparisons[cat] = {
                "current": round(total, 2),
                "historical_avg": avg,
                "pct_change": pct_change,
                "status": "over" if pct_change > 20 else ("under" if pct_change < -20 else "normal"),
            }

        result = {
            "customer_id": customer_id,
            "period_days": days,
            "total_spend": round(sum(by_category.values()), 2),
            "categories": comparisons,
        }

        self.emitter.emit(
            agent_id=AGENT_ID,
            agent_name=AGENT_NAME,
            action="analyze_spending",
            input_data={"customer_id": customer_id, "days": days},
            output_data=result,
            reasoning=f"Analysed {len(debits)} debit transactions across {len(by_category)} categories",
            customer_id=customer_id,
        )
        return result

    async def detect_anomalies(self, customer_id: str) -> list[dict]:
        """Find unusual spending patterns."""
        txns = _mock["transactions"].get(customer_id, [])
        anomalies: list[dict] = []

        for t in txns:
            if t.is_disputed:
                anomalies.append({
                    "transaction_id": t.transaction_id,
                    "type": "disputed",
                    "description": t.description,
                    "amount": t.amount,
                    "reason": "Transaction flagged as disputed by customer",
                })
            elif t.amount > 10000 and not t.is_credit:
                anomalies.append({
                    "transaction_id": t.transaction_id,
                    "type": "high_value",
                    "description": t.description,
                    "amount": t.amount,
                    "reason": f"High-value debit of ₹{t.amount:,.2f} exceeds typical pattern",
                })

        self.emitter.emit(
            agent_id=AGENT_ID,
            agent_name=AGENT_NAME,
            action="detect_anomalies",
            input_data={"customer_id": customer_id},
            output_data={"anomaly_count": len(anomalies), "anomalies": anomalies},
            reasoning=f"Detected {len(anomalies)} anomalies (disputed or high-value)",
            customer_id=customer_id,
        )
        return anomalies

    async def generate_summary(self, customer_id: str) -> str:
        """Create a spending summary using Azure OpenAI."""
        analysis = await self.analyze_spending(customer_id)
        start = time.time()

        try:
            client = _get_client()
            resp = await client.chat.completions.create(
                model=os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o"),
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a financial advisor at BNB Bank India. "
                            "Summarise the customer's spending in 3-4 sentences. "
                            "Mention notable categories and suggest one improvement. Use ₹ for amounts."
                        ),
                    },
                    {"role": "user", "content": str(analysis)},
                ],
                temperature=0.4,
                max_tokens=300,
            )
            summary = resp.choices[0].message.content or ""
            tokens = resp.usage.total_tokens if resp.usage else 0
            latency = (time.time() - start) * 1000
        except Exception:
            summary = (
                f"This week you spent ₹{analysis['total_spend']:,.2f} across "
                f"{len(analysis['categories'])} categories. "
                "Food and Shopping are your top spends. Consider setting a weekly budget to save more."
            )
            tokens = 0
            latency = (time.time() - start) * 1000

        self.emitter.emit(
            agent_id=AGENT_ID,
            agent_name=AGENT_NAME,
            action="generate_summary",
            input_data={"customer_id": customer_id},
            output_data={"summary": summary},
            tokens_used=tokens,
            latency_ms=latency,
            customer_id=customer_id,
        )
        return summary

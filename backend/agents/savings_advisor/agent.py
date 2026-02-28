"""Savings advisor agent – identifies saving opportunities and recommends FDs (UC3)."""

import os
import time
from typing import Optional

from openai import AsyncAzureOpenAI

from backend.shared.events.emitter import EventEmitter
from backend.shared.mock_data.generator import generate_all_mock_data

AGENT_ID = "savings_advisor"
AGENT_NAME = "Savings Advisor Agent"

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


class SavingsAdvisorAgent:
    """Provides personalised savings recommendations for UC3."""

    def __init__(self, emitter: EventEmitter):
        self.emitter = emitter

    async def identify_opportunities(self, customer_id: str) -> list[dict]:
        """Find saving opportunities based on spending patterns."""
        txns = _mock["transactions"].get(customer_id, [])
        food_spend = sum(t.amount for t in txns if t.category == "Food" and not t.is_credit)
        shopping_spend = sum(t.amount for t in txns if t.category == "Shopping" and not t.is_credit)

        opportunities: list[dict] = []
        if food_spend > 3000:
            opportunities.append({
                "category": "Food",
                "current_spend": round(food_spend, 2),
                "suggested_budget": 3000.0,
                "potential_saving": round(food_spend - 3000, 2),
                "tip": "Consider meal prepping on weekends to cut food delivery costs.",
            })
        if shopping_spend > 5000:
            opportunities.append({
                "category": "Shopping",
                "current_spend": round(shopping_spend, 2),
                "suggested_budget": 5000.0,
                "potential_saving": round(shopping_spend - 5000, 2),
                "tip": "Try a 24-hour rule: wait a day before making non-essential purchases.",
            })

        # Always suggest FD for idle balance
        for acct in _mock["accounts"]:
            if acct.customer_id == customer_id and acct.balance > 50000:
                surplus = round(acct.balance - 50000, 2)
                opportunities.append({
                    "category": "Idle Balance",
                    "current_balance": round(acct.balance, 2),
                    "suggested_fd_amount": surplus,
                    "potential_annual_return": round(surplus * 0.075, 2),
                    "tip": f"Move ₹{surplus:,.2f} to a 12-month FD at 7.5% p.a.",
                })

        self.emitter.emit(
            agent_id=AGENT_ID,
            agent_name=AGENT_NAME,
            action="identify_opportunities",
            input_data={"customer_id": customer_id},
            output_data={"opportunity_count": len(opportunities), "opportunities": opportunities},
            reasoning=f"Found {len(opportunities)} saving opportunities",
            customer_id=customer_id,
        )
        return opportunities

    async def recommend_fd(self, amount: float, tenure_months: int) -> dict:
        """Calculate FD returns at 7.5% p.a."""
        rate = 7.5
        years = tenure_months / 12
        maturity = round(amount * ((1 + rate / 100) ** years), 2)
        interest = round(maturity - amount, 2)

        result = {
            "principal": amount,
            "tenure_months": tenure_months,
            "rate_pct": rate,
            "maturity_amount": maturity,
            "interest_earned": interest,
            "compounding": "annual",
        }

        self.emitter.emit(
            agent_id=AGENT_ID,
            agent_name=AGENT_NAME,
            action="recommend_fd",
            input_data={"amount": amount, "tenure_months": tenure_months},
            output_data=result,
            reasoning=f"₹{amount:,.2f} at {rate}% for {tenure_months}m yields ₹{interest:,.2f} interest",
        )
        return result

    async def generate_advice(self, customer_id: str) -> str:
        """Generate personalised savings advice using Azure OpenAI."""
        opportunities = await self.identify_opportunities(customer_id)
        start = time.time()

        try:
            client = _get_client()
            resp = await client.chat.completions.create(
                model=os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o"),
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a friendly savings advisor at BNB Bank India. "
                            "Based on the opportunities provided, give 3 actionable tips in 4-5 sentences. "
                            "Be encouraging. Use ₹ for amounts."
                        ),
                    },
                    {"role": "user", "content": str(opportunities)},
                ],
                temperature=0.5,
                max_tokens=300,
            )
            advice = resp.choices[0].message.content or ""
            tokens = resp.usage.total_tokens if resp.usage else 0
            latency = (time.time() - start) * 1000
        except Exception:
            advice = (
                "Great news – you have saving potential! "
                "Consider reducing food delivery spending by ₹1,500/month. "
                "Also, your idle balance can earn ₹7,500+ annually in a fixed deposit. "
                "Start small and stay consistent!"
            )
            tokens = 0
            latency = (time.time() - start) * 1000

        self.emitter.emit(
            agent_id=AGENT_ID,
            agent_name=AGENT_NAME,
            action="generate_advice",
            input_data={"customer_id": customer_id},
            output_data={"advice": advice},
            tokens_used=tokens,
            latency_ms=latency,
            customer_id=customer_id,
        )
        return advice

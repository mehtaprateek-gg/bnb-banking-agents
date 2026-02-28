"""Loan advisor agent – pre-qualification, EMI calculation and offer generation (UC2)."""

import math
import os
import time
from typing import Optional

from openai import AsyncAzureOpenAI

from backend.shared.events.emitter import EventEmitter
from backend.shared.mock_data.generator import generate_all_mock_data

AGENT_ID = "loan_advisor"
AGENT_NAME = "Loan Advisor Agent"

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


class LoanAdvisorAgent:
    """Loan pre-qualification and recommendation for UC2."""

    def __init__(self, emitter: EventEmitter):
        self.emitter = emitter

    async def pre_qualify(self, customer_id: str) -> dict:
        """Check loan eligibility based on income and credit score (mock)."""
        # Mock credit profile
        monthly_income = 85000.0
        credit_score = 760
        existing_emi = 5000.0
        max_emi = round(monthly_income * 0.5 - existing_emi, 2)
        max_loan = round(max_emi * 60, 2)  # ~5 year tenure

        eligible = credit_score >= 650 and max_emi > 10000

        result = {
            "customer_id": customer_id,
            "eligible": eligible,
            "credit_score": credit_score,
            "monthly_income": monthly_income,
            "existing_emi": existing_emi,
            "max_emi_capacity": max_emi,
            "max_loan_amount": max_loan,
            "products_available": ["Personal Loan", "Home Loan", "Car Loan"],
        }

        self.emitter.emit(
            agent_id=AGENT_ID,
            agent_name=AGENT_NAME,
            action="pre_qualify",
            input_data={"customer_id": customer_id},
            output_data=result,
            reasoning=f"Credit score {credit_score}, max EMI capacity ₹{max_emi:,.2f}",
            confidence=0.90,
            customer_id=customer_id,
        )
        return result

    async def calculate_emi(self, principal: float, rate: float, tenure_months: int) -> dict:
        """Calculate EMI using standard formula: EMI = P * r * (1+r)^n / ((1+r)^n - 1)."""
        monthly_rate = rate / (12 * 100)
        if monthly_rate == 0:
            emi = principal / tenure_months
        else:
            emi = principal * monthly_rate * math.pow(1 + monthly_rate, tenure_months) / (
                math.pow(1 + monthly_rate, tenure_months) - 1
            )

        total_payment = round(emi * tenure_months, 2)
        total_interest = round(total_payment - principal, 2)

        result = {
            "principal": principal,
            "annual_rate_pct": rate,
            "tenure_months": tenure_months,
            "emi": round(emi, 2),
            "total_payment": total_payment,
            "total_interest": total_interest,
        }

        self.emitter.emit(
            agent_id=AGENT_ID,
            agent_name=AGENT_NAME,
            action="calculate_emi",
            input_data={"principal": principal, "rate": rate, "tenure_months": tenure_months},
            output_data=result,
            reasoning=f"EMI ₹{emi:,.2f}/month for {tenure_months} months at {rate}% p.a.",
        )
        return result

    async def generate_offer(self, customer_id: str) -> dict:
        """Generate a personalised loan offer using pre-qualification data and Azure OpenAI."""
        qualification = await self.pre_qualify(customer_id)
        start = time.time()

        # Default offer
        offer_amount = min(qualification["max_loan_amount"], 1500000)
        rate = 10.5
        tenure = 60
        emi_details = await self.calculate_emi(offer_amount, rate, tenure)

        try:
            client = _get_client()
            resp = await client.chat.completions.create(
                model=os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o"),
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a loan advisor at BNB Bank India. "
                            "Given the customer's qualification and EMI details, write a short personalised "
                            "loan offer message (3-4 sentences). Be professional and mention the key numbers. "
                            "Use ₹ for amounts."
                        ),
                    },
                    {
                        "role": "user",
                        "content": f"Qualification: {qualification}\nEMI details: {emi_details}",
                    },
                ],
                temperature=0.4,
                max_tokens=250,
            )
            message = resp.choices[0].message.content or ""
            tokens = resp.usage.total_tokens if resp.usage else 0
            latency = (time.time() - start) * 1000
        except Exception:
            message = (
                f"Congratulations! You are pre-approved for a Personal Loan of up to "
                f"₹{offer_amount:,.2f} at {rate}% p.a. Your EMI would be ₹{emi_details['emi']:,.2f}/month "
                f"for {tenure} months. Apply now on the BNB app!"
            )
            tokens = 0
            latency = (time.time() - start) * 1000

        offer = {
            "customer_id": customer_id,
            "offer_amount": offer_amount,
            "rate_pct": rate,
            "tenure_months": tenure,
            "emi": emi_details["emi"],
            "message": message,
        }

        self.emitter.emit(
            agent_id=AGENT_ID,
            agent_name=AGENT_NAME,
            action="generate_offer",
            input_data={"customer_id": customer_id},
            output_data=offer,
            tokens_used=tokens,
            latency_ms=latency,
            reasoning=f"Generated personal loan offer for ₹{offer_amount:,.2f}",
            customer_id=customer_id,
        )
        return offer

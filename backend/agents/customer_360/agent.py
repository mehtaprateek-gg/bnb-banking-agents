"""Customer 360 agent – retrieves customer profiles and interaction history."""

from typing import Optional

from backend.shared.events.emitter import EventEmitter
from backend.shared.mock_data.generator import get_all_customers, get_all_accounts
from backend.shared.models.banking import Customer

AGENT_ID = "customer_360"
AGENT_NAME = "Customer 360 Agent"


class Customer360Agent:
    """Provides a unified customer view from mock data."""

    def __init__(self, emitter: EventEmitter):
        self.emitter = emitter

    async def get_profile(self, customer_id: str) -> dict:
        """Return full customer profile including account details."""
        customer = self._find_customer(customer_id)
        account = self._find_account(customer_id)

        profile = customer.model_dump(mode="json") if customer else {}
        if account:
            profile["account"] = account.model_dump(mode="json")

        self.emitter.emit(
            agent_id=AGENT_ID,
            agent_name=AGENT_NAME,
            action="get_profile",
            input_data={"customer_id": customer_id},
            output_data=profile,
            reasoning="Retrieved customer profile from CRM",
            confidence=1.0,
            customer_id=customer_id,
        )
        return profile

    async def get_interaction_history(self, customer_id: str) -> list[dict]:
        """Return recent interactions (mock)."""
        history = [
            {
                "date": "2025-01-10T10:30:00Z",
                "channel": "whatsapp",
                "summary": "Balance inquiry",
                "resolved": True,
            },
            {
                "date": "2025-01-08T14:15:00Z",
                "channel": "mobile",
                "summary": "Fund transfer to savings",
                "resolved": True,
            },
            {
                "date": "2025-01-05T09:00:00Z",
                "channel": "voice",
                "summary": "Credit card payment due date query",
                "resolved": True,
            },
        ]

        self.emitter.emit(
            agent_id=AGENT_ID,
            agent_name=AGENT_NAME,
            action="get_interaction_history",
            input_data={"customer_id": customer_id},
            output_data={"interactions": history},
            reasoning="Fetched last 3 interactions from mock CRM",
            customer_id=customer_id,
        )
        return history

    # ------------------------------------------------------------------
    def _find_customer(self, customer_id: str) -> Optional[Customer]:
        for c in get_all_customers():
            if c.customer_id == customer_id:
                return c
        return None

    def _find_account(self, customer_id: str):
        for a in get_all_accounts():
            if a.customer_id == customer_id:
                return a
        return None

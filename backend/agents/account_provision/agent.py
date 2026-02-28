"""Account provisioning agent – creates accounts and provisions identities (mock)."""

import random
import uuid
from datetime import datetime

from backend.shared.events.emitter import EventEmitter

AGENT_ID = "account_provision"
AGENT_NAME = "Account Provisioning Agent"


class AccountProvisionAgent:
    """Mock account creation and identity provisioning for onboarding (UC1)."""

    def __init__(self, emitter: EventEmitter):
        self.emitter = emitter

    async def create_account(self, customer_data: dict) -> dict:
        """Create a new savings account (mock)."""
        acct_num = f"{random.randint(1000, 9999)}{random.randint(10000000, 99999999)}"
        result = {
            "account_number": acct_num,
            "account_type": "savings",
            "ifsc_code": "BNBN0001234",
            "branch": "Koregaon Park, Pune",
            "status": "active",
            "customer_id": customer_data.get("customer_id", ""),
            "customer_name": customer_data.get("name", "New Customer"),
            "opening_balance": 0.0,
            "created_at": datetime.utcnow().isoformat(),
            "reference_id": f"ACC-{uuid.uuid4().hex[:8].upper()}",
        }

        self.emitter.emit(
            agent_id=AGENT_ID,
            agent_name=AGENT_NAME,
            action="create_account",
            input_data={"customer_id": customer_data.get("customer_id", "")},
            output_data=result,
            reasoning="Savings account created in CBS with zero opening balance",
            confidence=1.0,
            customer_id=customer_data.get("customer_id", ""),
        )
        return result

    async def provision_identity(self, customer_data: dict) -> dict:
        """Provision an Azure AD identity for digital banking (mock)."""
        result = {
            "identity_id": f"aad-{uuid.uuid4().hex[:12]}",
            "username": customer_data.get("name", "user").lower().replace(" ", "."),
            "mfa_enabled": True,
            "provisioned_at": datetime.utcnow().isoformat(),
            "status": "active",
        }

        self.emitter.emit(
            agent_id=AGENT_ID,
            agent_name=AGENT_NAME,
            action="provision_identity",
            input_data={"customer_id": customer_data.get("customer_id", "")},
            output_data=result,
            reasoning="Azure AD B2C identity created with MFA enabled",
            confidence=1.0,
            customer_id=customer_data.get("customer_id", ""),
        )
        return result

    async def send_welcome(self, customer_id: str, channel: str) -> dict:
        """Send a welcome message to the customer (mock)."""
        result = {
            "sent": True,
            "channel": channel,
            "message": "Welcome to BNB Bank! Your account is now active. Download the BNB app to get started.",
            "sent_at": datetime.utcnow().isoformat(),
            "reference_id": f"WEL-{uuid.uuid4().hex[:8].upper()}",
        }

        self.emitter.emit(
            agent_id=AGENT_ID,
            agent_name=AGENT_NAME,
            action="send_welcome",
            input_data={"customer_id": customer_id, "channel": channel},
            output_data=result,
            reasoning=f"Welcome message sent via {channel}",
            confidence=1.0,
            customer_id=customer_id,
        )
        return result

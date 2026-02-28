"""Card management agent – block, unblock and replace cards (mock)."""

import uuid
from datetime import datetime

from backend.shared.events.emitter import EventEmitter

AGENT_ID = "card_mgmt"
AGENT_NAME = "Card Management Agent"


class CardManagementAgent:
    """Handles card lifecycle operations with mock responses."""

    def __init__(self, emitter: EventEmitter):
        self.emitter = emitter

    async def block_card(self, customer_id: str, card_number: str) -> dict:
        """Block a card immediately (mock)."""
        result = {
            "status": "blocked",
            "card_number_masked": f"XXXX-XXXX-XXXX-{card_number[-4:]}",
            "reference_id": f"BLK-{uuid.uuid4().hex[:8].upper()}",
            "blocked_at": datetime.utcnow().isoformat(),
            "message": "Your card has been blocked successfully. No further transactions will be processed.",
        }

        self.emitter.emit(
            agent_id=AGENT_ID,
            agent_name=AGENT_NAME,
            action="block_card",
            input_data={"customer_id": customer_id, "card_number_masked": result["card_number_masked"]},
            output_data=result,
            reasoning="Card blocked per customer request; all POS/online transactions disabled",
            confidence=1.0,
            customer_id=customer_id,
        )
        return result

    async def unblock_card(self, customer_id: str, card_number: str) -> dict:
        """Unblock a previously blocked card (mock)."""
        result = {
            "status": "active",
            "card_number_masked": f"XXXX-XXXX-XXXX-{card_number[-4:]}",
            "reference_id": f"UBK-{uuid.uuid4().hex[:8].upper()}",
            "unblocked_at": datetime.utcnow().isoformat(),
            "message": "Your card has been unblocked. You can resume transactions.",
        }

        self.emitter.emit(
            agent_id=AGENT_ID,
            agent_name=AGENT_NAME,
            action="unblock_card",
            input_data={"customer_id": customer_id, "card_number_masked": result["card_number_masked"]},
            output_data=result,
            reasoning="Card unblocked after customer verification",
            confidence=1.0,
            customer_id=customer_id,
        )
        return result

    async def replace_card(self, customer_id: str) -> dict:
        """Initiate card replacement (mock)."""
        result = {
            "status": "replacement_initiated",
            "reference_id": f"RPL-{uuid.uuid4().hex[:8].upper()}",
            "estimated_delivery": "5-7 business days",
            "delivery_address": "Registered address on file",
            "message": "A replacement card has been initiated. You will receive your new card within 5-7 business days at your registered address.",
        }

        self.emitter.emit(
            agent_id=AGENT_ID,
            agent_name=AGENT_NAME,
            action="replace_card",
            input_data={"customer_id": customer_id},
            output_data=result,
            reasoning="Replacement card request raised; old card will be deactivated on new card activation",
            confidence=1.0,
            customer_id=customer_id,
        )
        return result

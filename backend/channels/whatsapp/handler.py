"""WhatsApp channel handler — send/receive via Azure Communication Services Advanced Messaging.

Inbound messages arrive via Event Grid → webhook → this handler → Orchestrator.
Outbound messages are sent via ACS NotificationMessagesClient.
"""

import json
import logging
import os
from typing import Optional

from azure.communication.messages import NotificationMessagesClient
from azure.communication.messages.models import TextNotificationContent

logger = logging.getLogger(__name__)

# BNB Bank's WhatsApp Business number
BNB_WHATSAPP_NUMBER = "+919987961115"

# Customer phone → customer_id mapping (PoC lookup)
_PHONE_TO_CUSTOMER = {
    "+919876543210": "CUST-001-ANANYA",   # Ananya Deshmukh
    "+919876543211": "CUST-002-PRIYA",    # Priya Sharma
    "+919876543212": "CUST-003-RAJESH",   # Rajesh Iyer
}

_client: Optional[NotificationMessagesClient] = None


def _get_client() -> NotificationMessagesClient:
    """Lazy-initialise the ACS messaging client."""
    global _client
    if _client is None:
        conn_str = os.getenv("ACS_CONNECTION_STRING", "")
        if not conn_str:
            raise RuntimeError("ACS_CONNECTION_STRING not set")
        _client = NotificationMessagesClient.from_connection_string(conn_str)
    return _client


def get_channel_registration_id() -> str:
    """Return the WhatsApp channel registration ID (from Azure Portal)."""
    return os.getenv("WHATSAPP_CHANNEL_ID", "")


def lookup_customer(phone: str) -> str:
    """Map a phone number to a customer ID."""
    # Normalise: strip spaces, ensure +91 prefix
    phone = phone.strip().replace(" ", "")
    if not phone.startswith("+"):
        phone = "+91" + phone.lstrip("0")
    return _PHONE_TO_CUSTOMER.get(phone, f"UNKNOWN-{phone}")


def register_phone(phone: str, customer_id: str) -> None:
    """Register a phone number → customer_id mapping (for demo customers)."""
    phone = phone.strip().replace(" ", "")
    if not phone.startswith("+"):
        phone = "+91" + phone.lstrip("0")
    _PHONE_TO_CUSTOMER[phone] = customer_id


async def send_whatsapp_message(to_phone: str, message: str) -> dict:
    """Send a text message to a WhatsApp user via ACS.

    Args:
        to_phone: Recipient phone in E.164 format (e.g. +919876543211)
        message: Text content to send

    Returns:
        dict with send result including message_id
    """
    channel_id = get_channel_registration_id()
    if not channel_id:
        logger.warning("WHATSAPP_CHANNEL_ID not configured — message not sent")
        return {"status": "skipped", "reason": "channel_not_configured", "message": message}

    try:
        client = _get_client()
        # Normalise phone number
        to_phone = to_phone.strip().replace(" ", "")
        if not to_phone.startswith("+"):
            to_phone = "+91" + to_phone.lstrip("0")

        content = TextNotificationContent(
            channel_registration_id=channel_id,
            to=[to_phone],
            content=message,
        )
        result = client.send(content)

        receipts = list(result.receipts)
        msg_id = receipts[0].message_id if receipts else "unknown"
        logger.info("WhatsApp sent to %s: message_id=%s", to_phone, msg_id)
        return {
            "status": "sent",
            "message_id": msg_id,
            "to": to_phone,
        }
    except Exception as exc:
        logger.error("WhatsApp send failed: %s", exc)
        return {"status": "error", "error": str(exc)}


def parse_event_grid_event(event: dict) -> Optional[dict]:
    """Parse an Event Grid event for an incoming WhatsApp message.

    Expected event types:
    - Microsoft.Communication.AdvancedMessageReceived
    - Microsoft.Communication.AdvancedMessageDeliveryStatusUpdated

    Returns:
        dict with keys: from_phone, message, message_id, timestamp
        or None if not a message event
    """
    event_type = event.get("eventType", "")

    if event_type == "Microsoft.Communication.AdvancedMessageReceived":
        data = event.get("data", {})
        return {
            "type": "message",
            "from_phone": data.get("from", ""),
            "message": data.get("content", ""),
            "message_id": data.get("messageId", ""),
            "timestamp": data.get("receivedTimestamp", ""),
            "channel_type": data.get("channelType", "whatsapp"),
        }
    elif event_type == "Microsoft.Communication.AdvancedMessageDeliveryStatusUpdated":
        data = event.get("data", {})
        return {
            "type": "status",
            "message_id": data.get("messageId", ""),
            "status": data.get("status", ""),
            "channel_type": data.get("channelType", "whatsapp"),
        }

    return None

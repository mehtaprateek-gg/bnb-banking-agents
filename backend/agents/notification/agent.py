"""Notification agent – drafts messages for WhatsApp, push and voice (UC3)."""

import os
import time
from typing import Optional

from openai import AsyncAzureOpenAI

from backend.shared.events.emitter import EventEmitter

AGENT_ID = "notification"
AGENT_NAME = "Notification Agent"

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


class NotificationAgent:
    """Drafts customer-facing messages across channels for UC3."""

    def __init__(self, emitter: EventEmitter):
        self.emitter = emitter

    async def draft_whatsapp_message(self, customer_id: str, insights: dict) -> dict:
        """Generate a WhatsApp-friendly spending insights message using Azure OpenAI."""
        start = time.time()
        try:
            client = _get_client()
            resp = await client.chat.completions.create(
                model=os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o"),
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are BNB Bank's WhatsApp assistant. Draft a short, friendly spending insights "
                            "message (max 160 words). Use emojis sparingly. Include a disclaimer: "
                            "'This is auto-generated. Not financial advice.' Use ₹ for amounts."
                        ),
                    },
                    {"role": "user", "content": str(insights)},
                ],
                temperature=0.5,
                max_tokens=250,
            )
            message = resp.choices[0].message.content or ""
            tokens = resp.usage.total_tokens if resp.usage else 0
            latency = (time.time() - start) * 1000
        except Exception:
            total = insights.get("total_spend", 0)
            message = (
                f"🏦 BNB Bank Weekly Summary\n\n"
                f"Hi! Here's your spending snapshot:\n"
                f"💰 Total spent: ₹{total:,.2f}\n"
                f"🍕 Food & Shopping are your top categories.\n\n"
                f"💡 Tip: Consider setting a weekly budget!\n\n"
                f"_This is auto-generated. Not financial advice._"
            )
            tokens = 0
            latency = (time.time() - start) * 1000

        result = {"channel": "whatsapp", "customer_id": customer_id, "message": message}

        self.emitter.emit(
            agent_id=AGENT_ID,
            agent_name=AGENT_NAME,
            action="draft_whatsapp_message",
            input_data={"customer_id": customer_id},
            output_data=result,
            tokens_used=tokens,
            latency_ms=latency,
            reasoning="Drafted WhatsApp spending insights message",
            customer_id=customer_id,
        )
        return result

    async def draft_push_notification(self, customer_id: str, insights: dict) -> dict:
        """Generate a concise push notification."""
        total = insights.get("total_spend", 0)
        categories = insights.get("categories", {})
        top_cat = max(categories, key=lambda c: categories[c].get("current", 0)) if categories else "General"

        message = f"📊 You spent ₹{total:,.2f} this week. {top_cat} was your biggest category. Tap to see tips!"

        result = {"channel": "push", "customer_id": customer_id, "message": message}

        self.emitter.emit(
            agent_id=AGENT_ID,
            agent_name=AGENT_NAME,
            action="draft_push_notification",
            input_data={"customer_id": customer_id},
            output_data=result,
            reasoning="Created push notification with spend summary",
            customer_id=customer_id,
        )
        return result

    async def draft_voice_script(self, customer_id: str, insights: dict) -> dict:
        """Generate a Hindi voice script for IVR/TTS."""
        start = time.time()
        try:
            client = _get_client()
            resp = await client.chat.completions.create(
                model=os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o"),
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are BNB Bank's voice assistant. Write a short Hindi script (4-5 sentences) "
                            "summarising the customer's weekly spending. Use simple Hindi with Devanagari. "
                            "End with 'Dhanyavaad, BNB Bank'. Use ₹ for amounts."
                        ),
                    },
                    {"role": "user", "content": str(insights)},
                ],
                temperature=0.4,
                max_tokens=300,
            )
            script = resp.choices[0].message.content or ""
            tokens = resp.usage.total_tokens if resp.usage else 0
            latency = (time.time() - start) * 1000
        except Exception:
            total = insights.get("total_spend", 0)
            script = (
                f"नमस्ते! BNB Bank की ओर से आपका साप्ताहिक खर्च सारांश। "
                f"इस हफ्ते आपने कुल ₹{total:,.2f} खर्च किए। "
                f"खाने और शॉपिंग पर सबसे ज़्यादा खर्च हुआ। "
                f"बचत के लिए साप्ताहिक बजट बनाएं। "
                f"धन्यवाद, BNB Bank।"
            )
            tokens = 0
            latency = (time.time() - start) * 1000

        result = {"channel": "voice", "customer_id": customer_id, "script": script, "language": "hi"}

        self.emitter.emit(
            agent_id=AGENT_ID,
            agent_name=AGENT_NAME,
            action="draft_voice_script",
            input_data={"customer_id": customer_id},
            output_data=result,
            tokens_used=tokens,
            latency_ms=latency,
            reasoning="Generated Hindi voice script for TTS",
            customer_id=customer_id,
        )
        return result

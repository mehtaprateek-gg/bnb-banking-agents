"""Voice summary agent – generates Hindi voice scripts for TTS (UC3)."""

import os
import time
from typing import Optional

from openai import AsyncAzureOpenAI

from backend.shared.events.emitter import EventEmitter

AGENT_ID = "voice_summary"
AGENT_NAME = "Voice Summary Agent"

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


class VoiceSummaryAgent:
    """Creates Hindi voice scripts for weekly financial summaries (UC3)."""

    def __init__(self, emitter: EventEmitter):
        self.emitter = emitter

    async def generate_summary_script(self, customer_id: str, insights: dict) -> dict:
        """Create a Hindi voice script from spending insights."""
        start = time.time()
        try:
            client = _get_client()
            resp = await client.chat.completions.create(
                model=os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o"),
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are BNB Bank's voice assistant. Write a warm, clear Hindi script "
                            "(5-6 sentences in Devanagari) summarising the customer's weekly finances. "
                            "Mention total spend, top category, and one saving tip. "
                            "Start with 'Namaste' and end with 'Dhanyavaad, BNB Bank'. "
                            "Keep it under 100 words. Use ₹ for amounts."
                        ),
                    },
                    {"role": "user", "content": str(insights)},
                ],
                temperature=0.4,
                max_tokens=350,
            )
            script = resp.choices[0].message.content or ""
            tokens = resp.usage.total_tokens if resp.usage else 0
            latency = (time.time() - start) * 1000
        except Exception:
            total = insights.get("total_spend", 0)
            script = (
                f"नमस्ते! BNB Bank की ओर से आपका साप्ताहिक वित्तीय सारांश। "
                f"इस हफ्ते आपने कुल ₹{total:,.2f} खर्च किए। "
                f"आपका सबसे बड़ा खर्च खाने और शॉपिंग में रहा। "
                f"हमारा सुझाव है कि आप साप्ताहिक बजट तय करें और बचत को FD में लगाएं। "
                f"अधिक जानकारी के लिए BNB ऐप खोलें। "
                f"धन्यवाद, BNB Bank।"
            )
            tokens = 0
            latency = (time.time() - start) * 1000

        result = {
            "customer_id": customer_id,
            "script": script,
            "language": "hi",
            "word_count": len(script.split()),
        }

        self.emitter.emit(
            agent_id=AGENT_ID,
            agent_name=AGENT_NAME,
            action="generate_summary_script",
            input_data={"customer_id": customer_id},
            output_data=result,
            tokens_used=tokens,
            latency_ms=latency,
            reasoning="Generated Hindi voice summary script for TTS",
            customer_id=customer_id,
        )
        return result

    async def format_for_tts(self, script: str) -> dict:
        """Format a script for Azure Speech Services TTS."""
        ssml = (
            '<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="hi-IN">'
            '<voice name="hi-IN-SwaraNeural">'
            f'<prosody rate="medium" pitch="medium">{script}</prosody>'
            "</voice>"
            "</speak>"
        )

        result = {
            "ssml": ssml,
            "voice": "hi-IN-SwaraNeural",
            "language": "hi-IN",
            "format": "audio-16khz-128kbitrate-mono-mp3",
        }

        self.emitter.emit(
            agent_id=AGENT_ID,
            agent_name=AGENT_NAME,
            action="format_for_tts",
            input_data={"script_length": len(script)},
            output_data={"ssml_length": len(ssml), "voice": result["voice"]},
            reasoning="Formatted Hindi script as SSML for Azure TTS",
        )
        return result

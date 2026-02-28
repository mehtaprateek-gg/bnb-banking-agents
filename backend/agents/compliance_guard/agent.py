"""Compliance guard agent – checks messages against RBI rules (UC3)."""

import os
import time
from typing import Optional

from openai import AsyncAzureOpenAI

from backend.shared.events.emitter import EventEmitter

AGENT_ID = "compliance_guard"
AGENT_NAME = "Compliance Guard Agent"

RBI_RULES = [
    "Must include disclaimer that message is auto-generated",
    "Must not guarantee returns on investments",
    "Must not use misleading terms like 'risk-free'",
    "Must include bank name (BNB Bank)",
    "Must not share full account numbers or Aadhaar",
    "Must comply with RBI circular on digital lending guidelines",
]

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


class ComplianceGuardAgent:
    """Reviews outgoing messages for RBI regulatory compliance (UC3)."""

    def __init__(self, emitter: EventEmitter):
        self.emitter = emitter

    async def review_message(self, message_text: str) -> dict:
        """Check message against RBI compliance rules using Azure OpenAI."""
        start = time.time()
        try:
            client = _get_client()
            resp = await client.chat.completions.create(
                model=os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o"),
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are an RBI compliance officer. Review the message against these rules:\n"
                            + "\n".join(f"- {r}" for r in RBI_RULES)
                            + "\n\nReturn JSON with: "
                            '{"compliant": true/false, "issues": ["issue1",...], "suggestions": ["fix1",...]}'
                            "\nOnly output JSON."
                        ),
                    },
                    {"role": "user", "content": message_text},
                ],
                temperature=0.1,
                max_tokens=300,
            )
            import json

            raw = resp.choices[0].message.content or "{}"
            tokens = resp.usage.total_tokens if resp.usage else 0
            latency = (time.time() - start) * 1000
            result = json.loads(raw)
        except Exception:
            # Fallback rule-based check
            issues = []
            if "auto-generated" not in message_text.lower() and "auto generated" not in message_text.lower():
                issues.append("Missing auto-generated disclaimer")
            if "risk-free" in message_text.lower():
                issues.append("Contains misleading term 'risk-free'")
            if "guaranteed" in message_text.lower() and "return" in message_text.lower():
                issues.append("Implies guaranteed returns")

            result = {
                "compliant": len(issues) == 0,
                "issues": issues,
                "suggestions": [f"Fix: {i}" for i in issues],
            }
            tokens = 0
            latency = (time.time() - start) * 1000

        self.emitter.emit(
            agent_id=AGENT_ID,
            agent_name=AGENT_NAME,
            action="review_message",
            input_data={"message_length": len(message_text)},
            output_data=result,
            tokens_used=tokens,
            latency_ms=latency,
            reasoning=f"Compliance check: {'PASS' if result.get('compliant') else 'FAIL – ' + str(len(result.get('issues', []))) + ' issue(s)'}",
        )
        return result

    async def check_disclaimers(self, message_text: str) -> dict:
        """Verify required disclaimers are present in the message."""
        required = [
            ("auto-generated", "Auto-generated disclaimer"),
            ("not financial advice", "Financial advice disclaimer"),
        ]
        present = []
        missing = []

        lower = message_text.lower()
        for keyword, label in required:
            if keyword in lower:
                present.append(label)
            else:
                missing.append(label)

        result = {
            "all_present": len(missing) == 0,
            "present": present,
            "missing": missing,
        }

        self.emitter.emit(
            agent_id=AGENT_ID,
            agent_name=AGENT_NAME,
            action="check_disclaimers",
            input_data={"message_length": len(message_text)},
            output_data=result,
            reasoning=f"Disclaimers: {len(present)} present, {len(missing)} missing",
        )
        return result

    async def approve_or_flag(self, message_text: str) -> dict:
        """Return approved/flagged status with reason."""
        review = await self.review_message(message_text)
        disclaimers = await self.check_disclaimers(message_text)

        compliant = review.get("compliant", False)
        all_disclaimers = disclaimers.get("all_present", False)
        approved = compliant and all_disclaimers

        reasons = review.get("issues", []) + [
            f"Missing disclaimer: {d}" for d in disclaimers.get("missing", [])
        ]

        result = {
            "status": "approved" if approved else "flagged",
            "reasons": reasons if not approved else [],
            "review_details": review,
            "disclaimer_check": disclaimers,
        }

        self.emitter.emit(
            agent_id=AGENT_ID,
            agent_name=AGENT_NAME,
            action="approve_or_flag",
            input_data={"message_length": len(message_text)},
            output_data=result,
            reasoning=f"Message {'APPROVED' if approved else 'FLAGGED'} – {len(reasons)} issue(s)",
            confidence=1.0 if approved else 0.5,
        )
        return result

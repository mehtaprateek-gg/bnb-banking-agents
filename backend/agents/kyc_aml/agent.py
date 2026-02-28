"""KYC/AML agent – anti-money-laundering checks and risk scoring (mock)."""

import uuid
from datetime import datetime

from backend.shared.events.emitter import EventEmitter

AGENT_ID = "kyc_aml"
AGENT_NAME = "KYC/AML Agent"


class KycAmlAgent:
    """Mock KYC and AML screening for onboarding (UC1)."""

    def __init__(self, emitter: EventEmitter):
        self.emitter = emitter

    async def run_aml_check(self, customer_data: dict) -> dict:
        """Run AML check and return risk level (low/medium/high)."""
        risk = "low"
        result = {
            "risk_level": risk,
            "customer_name": customer_data.get("name", "Unknown"),
            "sanctions_hit": False,
            "pep_hit": False,
            "adverse_media": False,
            "reference_id": f"AML-{uuid.uuid4().hex[:8].upper()}",
            "checked_at": datetime.utcnow().isoformat(),
        }

        self.emitter.emit(
            agent_id=AGENT_ID,
            agent_name=AGENT_NAME,
            action="run_aml_check",
            input_data={"customer_name": customer_data.get("name", "")},
            output_data=result,
            reasoning="No sanctions, PEP or adverse media matches found",
            confidence=0.99,
        )
        return result

    async def sanctions_screening(self, name: str) -> dict:
        """Screen name against sanctions lists (mock)."""
        result = {
            "screened_name": name,
            "match_found": False,
            "lists_checked": ["OFAC SDN", "UN Consolidated", "EU Sanctions", "RBI Caution List"],
            "reference_id": f"SCR-{uuid.uuid4().hex[:8].upper()}",
            "screened_at": datetime.utcnow().isoformat(),
        }

        self.emitter.emit(
            agent_id=AGENT_ID,
            agent_name=AGENT_NAME,
            action="sanctions_screening",
            input_data={"name": name},
            output_data=result,
            reasoning="Screened against 4 international and domestic sanction lists – no match",
            confidence=1.0,
        )
        return result

    async def calculate_risk_score(self, customer_data: dict) -> dict:
        """Return a 0-100 risk score based on customer data."""
        score = 15  # low-risk default for PoC
        result = {
            "risk_score": score,
            "risk_band": "low" if score < 30 else ("medium" if score < 60 else "high"),
            "factors": [
                {"factor": "Domestic resident", "impact": -10},
                {"factor": "Salaried individual", "impact": -5},
                {"factor": "No prior alerts", "impact": -5},
                {"factor": "First-time account", "impact": +15},
            ],
            "reference_id": f"RSK-{uuid.uuid4().hex[:8].upper()}",
            "scored_at": datetime.utcnow().isoformat(),
        }

        self.emitter.emit(
            agent_id=AGENT_ID,
            agent_name=AGENT_NAME,
            action="calculate_risk_score",
            input_data={"customer_id": customer_data.get("customer_id", "")},
            output_data=result,
            reasoning=f"Risk score {score}/100 – domestic salaried individual, no red flags",
            confidence=0.95,
        )
        return result

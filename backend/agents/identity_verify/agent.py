"""Identity verification agent – Aadhaar, PAN and selfie verification (mock)."""

import uuid
from datetime import datetime

from backend.shared.events.emitter import EventEmitter

AGENT_ID = "identity_verify"
AGENT_NAME = "Identity Verification Agent"


class IdentityVerifyAgent:
    """Mock identity verification for onboarding (UC1)."""

    def __init__(self, emitter: EventEmitter):
        self.emitter = emitter

    async def verify_aadhaar(self, aadhaar_number: str) -> dict:
        """Verify Aadhaar number (mock – always succeeds with 95% confidence)."""
        result = {
            "verified": True,
            "confidence": 0.95,
            "aadhaar_masked": f"XXXX XXXX {aadhaar_number[-4:]}",
            "name_on_record": "Ananya Deshmukh",
            "reference_id": f"AADH-{uuid.uuid4().hex[:8].upper()}",
            "verified_at": datetime.utcnow().isoformat(),
        }

        self.emitter.emit(
            agent_id=AGENT_ID,
            agent_name=AGENT_NAME,
            action="verify_aadhaar",
            input_data={"aadhaar_masked": result["aadhaar_masked"]},
            output_data=result,
            reasoning="Aadhaar OTP verified successfully via UIDAI sandbox",
            confidence=0.95,
        )
        return result

    async def verify_pan(self, pan_number: str) -> dict:
        """Verify PAN card (mock)."""
        result = {
            "verified": True,
            "confidence": 0.98,
            "pan_masked": f"{pan_number[:5]}****{pan_number[-1]}",
            "name_on_record": "Ananya Deshmukh",
            "reference_id": f"PAN-{uuid.uuid4().hex[:8].upper()}",
            "verified_at": datetime.utcnow().isoformat(),
        }

        self.emitter.emit(
            agent_id=AGENT_ID,
            agent_name=AGENT_NAME,
            action="verify_pan",
            input_data={"pan_masked": result["pan_masked"]},
            output_data=result,
            reasoning="PAN validated against NSDL/UTIITSL database",
            confidence=0.98,
        )
        return result

    async def verify_selfie(self, image_data: bytes) -> dict:
        """Perform liveness check on selfie (mock)."""
        result = {
            "liveness": True,
            "confidence": 0.97,
            "face_match": True,
            "face_match_score": 0.94,
            "reference_id": f"SEL-{uuid.uuid4().hex[:8].upper()}",
            "verified_at": datetime.utcnow().isoformat(),
        }

        self.emitter.emit(
            agent_id=AGENT_ID,
            agent_name=AGENT_NAME,
            action="verify_selfie",
            input_data={"image_size_bytes": len(image_data)},
            output_data=result,
            reasoning="Liveness detected; face matched with Aadhaar photo on file",
            confidence=0.97,
        )
        return result

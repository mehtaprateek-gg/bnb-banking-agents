"""Document agent – document classification and data extraction (mock)."""

import uuid
from datetime import datetime

from backend.shared.events.emitter import EventEmitter

AGENT_ID = "document_agent"
AGENT_NAME = "Document Agent"


class DocumentAgent:
    """Mock document processing for onboarding (UC1)."""

    def __init__(self, emitter: EventEmitter):
        self.emitter = emitter

    async def extract_aadhaar_data(self, document_bytes: bytes) -> dict:
        """Extract structured data from an Aadhaar card image (mock)."""
        result = {
            "document_type": "aadhaar",
            "name": "Ananya Deshmukh",
            "address": "Flat 402, Koregaon Park, Pune, Maharashtra 411001",
            "aadhaar_number_masked": "XXXX XXXX 3210",
            "date_of_birth": "1995-03-15",
            "gender": "Female",
            "extraction_confidence": 0.96,
            "reference_id": f"DOC-{uuid.uuid4().hex[:8].upper()}",
            "extracted_at": datetime.utcnow().isoformat(),
        }

        self.emitter.emit(
            agent_id=AGENT_ID,
            agent_name=AGENT_NAME,
            action="extract_aadhaar_data",
            input_data={"document_size_bytes": len(document_bytes)},
            output_data=result,
            reasoning="OCR extracted name, address, and masked Aadhaar from uploaded image",
            confidence=0.96,
        )
        return result

    async def extract_pan_data(self, document_bytes: bytes) -> dict:
        """Extract structured data from a PAN card image (mock)."""
        result = {
            "document_type": "pan",
            "name": "Ananya Deshmukh",
            "pan_number": "ABCDE1234F",
            "date_of_birth": "1995-03-15",
            "extraction_confidence": 0.97,
            "reference_id": f"DOC-{uuid.uuid4().hex[:8].upper()}",
            "extracted_at": datetime.utcnow().isoformat(),
        }

        self.emitter.emit(
            agent_id=AGENT_ID,
            agent_name=AGENT_NAME,
            action="extract_pan_data",
            input_data={"document_size_bytes": len(document_bytes)},
            output_data=result,
            reasoning="OCR extracted name and PAN from uploaded image",
            confidence=0.97,
        )
        return result

    async def classify_document(self, document_bytes: bytes) -> dict:
        """Classify the type of uploaded document (mock)."""
        result = {
            "document_type": "aadhaar",
            "confidence": 0.99,
            "alternatives": [
                {"type": "pan", "confidence": 0.01},
            ],
            "reference_id": f"CLS-{uuid.uuid4().hex[:8].upper()}",
            "classified_at": datetime.utcnow().isoformat(),
        }

        self.emitter.emit(
            agent_id=AGENT_ID,
            agent_name=AGENT_NAME,
            action="classify_document",
            input_data={"document_size_bytes": len(document_bytes)},
            output_data=result,
            reasoning="Document classified as Aadhaar card with 99% confidence",
            confidence=0.99,
        )
        return result

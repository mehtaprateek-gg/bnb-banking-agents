"""BNB Banking Agents — FastAPI demo server.

Exposes the orchestrator as an HTTP API and streams agent events to the
React dashboard via Server-Sent Events (SSE).

Usage:
    cd C:\\temp\\bnb-banking-agents
    set PYTHONPATH=C:\\temp\\bnb-banking-agents
    uvicorn backend.main:app --reload --port 8000
"""

import asyncio
import json
import os
import uuid
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel

from backend.shared.events.emitter import EventEmitter
from backend.shared.models.banking import Channel, Language
from backend.shared.registry.copilot_studio_client import get_registry
from backend.agents.orchestrator.agent import OrchestratorAgent

# ---------------------------------------------------------------------------
# Global event bus — agents push events here, SSE clients consume them
# ---------------------------------------------------------------------------
_event_subscribers: list[asyncio.Queue] = []


class SSEEventEmitter(EventEmitter):
    """EventEmitter that also pushes events to all SSE subscribers."""

    def emit(self, **kwargs):
        event = super().emit(**kwargs)
        payload = json.dumps(event.model_dump(mode="json"), default=str)
        for q in _event_subscribers:
            q.put_nowait(payload)
        return event


# ---------------------------------------------------------------------------
# Lifespan — load Copilot Studio agent registry at startup
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    registry = get_registry()
    try:
        await registry.refresh_cache()
        agents = registry.list_agents()
        print(f"[BNB] Copilot Studio registry loaded: {len(agents)} agents")
    except Exception as exc:
        print(f"[BNB] Copilot Studio unavailable ({exc}), using empty registry")
    yield


app = FastAPI(
    title="BNB Banking Agents",
    description="Multi-agent AI banking system for Bharat National Bank",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Request / Response models
# ---------------------------------------------------------------------------
class AddCustomerRequest(BaseModel):
    name: str
    phone: str


class ChatRequest(BaseModel):
    message: str
    customer_id: str = "CUST-002-PRIYA"
    channel: str = "whatsapp"
    session_id: str | None = None


class ChatResponse(BaseModel):
    session_id: str
    language: str
    intent: str
    sentiment: str
    summary: str
    agents: list[str]
    events: list[dict]


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------
@app.get("/api/health")
async def health():
    registry = get_registry()
    agents = registry.list_agents()
    return {
        "status": "healthy",
        "agents_registered": len(agents),
        "registry_source": registry._source,
        "dataverse_url": os.getenv("DATAVERSE_URL", "not configured"),
    }


@app.get("/api/agents")
async def list_agents(agent_type: str | None = None, use_case: str | None = None):
    """List all agents from Copilot Studio registry."""
    from backend.shared.models.banking import AgentType
    registry = get_registry()
    at = AgentType(agent_type) if agent_type else None
    agents = registry.list_agents(agent_type=at, use_case=use_case)
    return [a.model_dump() for a in agents]


@app.get("/api/agents/{agent_id}")
async def get_agent(agent_id: str):
    """Get a single agent from Copilot Studio registry."""
    registry = get_registry()
    agent = registry.get_agent(agent_id)
    if not agent:
        return {"error": "Agent not found"}, 404
    return agent.model_dump()


@app.post("/api/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    """Send a message to the orchestrator and get routed to specialist agents."""
    session_id = req.session_id or f"sess-{uuid.uuid4().hex[:8]}"
    channel = Channel(req.channel) if req.channel in [c.value for c in Channel] else Channel.MOBILE

    emitter = SSEEventEmitter(session_id=session_id, use_case="demo", channel=channel)
    orchestrator = OrchestratorAgent(emitter)

    result = await orchestrator.handle_message(
        message=req.message,
        customer_id=req.customer_id,
        channel=channel,
        session_id=session_id,
    )

    events = [e.model_dump(mode="json") for e in emitter.get_events()]

    return ChatResponse(
        session_id=session_id,
        language=result.get("language", "en"),
        intent=result.get("intent", "unknown"),
        sentiment=result.get("sentiment", "neutral"),
        summary=result.get("summary", ""),
        agents=result.get("agents", []),
        events=events,
    )


@app.get("/api/events/stream")
async def event_stream(request: Request):
    """SSE endpoint — streams agent events to the React dashboard in real-time."""

    async def generate() -> AsyncGenerator[str, None]:
        q: asyncio.Queue = asyncio.Queue()
        _event_subscribers.append(q)
        try:
            while True:
                if await request.is_disconnected():
                    break
                try:
                    data = await asyncio.wait_for(q.get(), timeout=30)
                    yield f"data: {data}\n\n"
                except asyncio.TimeoutError:
                    yield ": keepalive\n\n"
        finally:
            _event_subscribers.remove(q)

    return StreamingResponse(generate(), media_type="text/event-stream")


@app.get("/api/cosmos/customers")
async def list_customers():
    """Retrieve customers (fixed personas + dynamically added demo customers)."""
    from backend.shared.mock_data.generator import get_all_customers
    customers = get_all_customers()
    return [c.model_dump(mode="json") for c in customers]


@app.post("/api/customers")
async def add_customer(req: AddCustomerRequest):
    """Register a demo customer with a real phone number. All other data is auto-generated."""
    from backend.shared.mock_data.generator import create_demo_customer
    from backend.channels.whatsapp.handler import register_phone

    try:
        customer, account = create_demo_customer(name=req.name, phone=req.phone)
    except ValueError as e:
        return JSONResponse(status_code=409, content={"error": str(e)})

    # Update the WhatsApp phone → customer_id lookup map
    register_phone(customer.phone, customer.customer_id)

    return {
        "status": "created",
        "customer": customer.model_dump(mode="json"),
        "account": account.model_dump(mode="json"),
    }


@app.delete("/api/cosmos/customers/{customer_id}")
async def delete_customer(customer_id: str):
    """Delete a dynamically added customer. Fixed personas cannot be deleted."""
    from backend.shared.mock_data.generator import delete_dynamic_customer
    from backend.channels.whatsapp.handler import unregister_phone

    FIXED_IDS = {"CUST-001-ANANYA", "CUST-002-PRIYA", "CUST-003-RAJESH"}
    if customer_id in FIXED_IDS:
        return JSONResponse(status_code=400, content={"error": "Cannot delete fixed demo personas"})

    deleted = delete_dynamic_customer(customer_id)
    if not deleted:
        return JSONResponse(status_code=404, content={"error": f"Customer {customer_id} not found"})

    unregister_phone(customer_id)
    return {"status": "deleted", "customer_id": customer_id}


@app.get("/api/cosmos/transactions/{customer_id}")
async def list_transactions(customer_id: str, limit: int = 10):
    """Retrieve transactions for a customer (from mock data generator)."""
    from backend.shared.mock_data.generator import generate_transactions
    txns = generate_transactions(customer_id, days=30, count=25)
    return [t.model_dump(mode="json") for t in txns[:limit]]


# ---------------------------------------------------------------------------
# WhatsApp Channel (Azure Communication Services Advanced Messaging)
# ---------------------------------------------------------------------------
@app.post("/api/whatsapp/webhook")
async def whatsapp_webhook(request: Request):
    """Event Grid webhook — receives inbound WhatsApp messages and delivery status.

    Handles:
    - Event Grid validation handshake (SubscriptionValidation)
    - Multi-turn onboarding flow (SBI YONO style)
    - Single-turn intent routing for other messages
    - Delivery status updates
    """
    from backend.channels.whatsapp.handler import (
        parse_event_grid_event, lookup_customer, send_whatsapp_message,
        register_phone,
    )
    from backend.channels.whatsapp.conversation import (
        is_onboarding_trigger, has_active_session, start_session,
        get_session, end_session, handle_step,
    )

    body = await request.json()
    events = body if isinstance(body, list) else [body]

    for event in events:
        # Event Grid validation handshake
        if event.get("eventType") == "Microsoft.EventGrid.SubscriptionValidationEvent":
            code = event.get("data", {}).get("validationCode", "")
            return {"validationResponse": code}

        parsed = parse_event_grid_event(event)
        if not parsed:
            continue

        if parsed["type"] == "status":
            continue

        from_phone = parsed["from_phone"]
        message = parsed["message"]
        print(f"[WA-WEBHOOK] Inbound from {from_phone}: {message[:50]}")

        # --- Emit inbound chat event for dashboard ---
        _emit_chat_event(from_phone, message, direction="inbound")

        # --- Multi-turn onboarding flow ---
        if is_onboarding_trigger(message) and not has_active_session(from_phone):
            print(f"[WA-WEBHOOK] Onboarding trigger detected for {from_phone}")
            session = start_session(from_phone)
            session_id = f"wa-onboard-{uuid.uuid4().hex[:8]}"
            emitter = SSEEventEmitter(session_id=session_id, use_case="UC1", channel=Channel.WHATSAPP)
            customer_id = f"NEW-{from_phone}"

            # ── Rich cascade: Channel → Language → Orchestrator ──
            emitter.emit(
                agent_id="whatsapp-agent", agent_name="WhatsApp Channel",
                action="message_received",
                input_data={"from": from_phone, "content": message[:50]},
                output_data={"intent_signal": "account_opening", "channel": "whatsapp"},
                reasoning="Inbound WhatsApp message — detected account opening keywords",
                confidence=0.99, latency_ms=45,
                next_agents=["language-agent"], customer_id=customer_id,
            )
            await asyncio.sleep(0.4)
            emitter.emit(
                agent_id="language-agent", agent_name="Language NLP",
                action="language_detected",
                output_data={"language": "English", "intent": "new_account", "sentiment": "positive"},
                reasoning="NLP: language=English, intent=account_opening (0.97), sentiment=positive",
                confidence=0.97, latency_ms=85,
                event_type="decision",
                next_agents=["orchestrator"], customer_id=customer_id,
            )
            await asyncio.sleep(0.4)
            emitter.emit(
                agent_id="orchestrator", agent_name="Orchestrator",
                action="onboarding_flow_started",
                input_data={"message": message, "phone": from_phone},
                output_data={"flow": "SBI_YONO_Digital_KYC", "total_steps": 8, "step": 1},
                reasoning="Account opening request → routing to SBI YONO-style digital KYC onboarding",
                confidence=0.98, latency_ms=110,
                event_type="decision",
                next_agents=["customer360-agent"], customer_id=customer_id,
            )

            reply = (
                "🏦 *Welcome to Bharat National Bank!*\n\n"
                "Let's open your Digital Savings Account — "
                "fully paperless, just like SBI YONO.\n\n"
                "Please share your *full name* as per Aadhaar."
            )
            _emit_chat_event(from_phone, reply, direction="outbound")
            result = await send_whatsapp_message(from_phone, reply)
            print(f"[WA-WEBHOOK] Send result: {result}")
            continue

        if has_active_session(from_phone):
            session = get_session(from_phone)
            if not session:
                continue

            old_step = session.step
            print(f"[WA-WEBHOOK] Active session for {from_phone}, step={old_step}")
            session_id = f"wa-onboard-{from_phone[-6:]}"
            emitter = SSEEventEmitter(session_id=session_id, use_case="UC1", channel=Channel.WHATSAPP)

            reply, is_complete = handle_step(session, message)
            step_advanced = session.step != old_step
            print(f"[WA-WEBHOOK] Step reply (complete={is_complete}, step={session.step}, advanced={step_advanced}): {reply[:120]}...")

            # ── Emit rich agent cascade only when step succeeds ──
            if step_advanced:
                await _emit_step_events(old_step, session, emitter, from_phone)

            _emit_chat_event(from_phone, reply, direction="outbound")
            result = await send_whatsapp_message(from_phone, reply)
            print(f"[WA-WEBHOOK] Send result: {result}")

            if is_complete and session.step == "complete":
                # Auto-register customer
                print(f"[WA-WEBHOOK] Onboarding complete! Finalizing for {from_phone}")
                await _finalize_onboarding(session, emitter, from_phone)
                end_session(from_phone)
                print(f"[WA-WEBHOOK] Session ended for {from_phone}")
            continue

        # --- Default: single-turn orchestrator flow ---
        customer_id = lookup_customer(from_phone)
        session_id = f"wa-{uuid.uuid4().hex[:8]}"
        emitter = SSEEventEmitter(session_id=session_id, use_case="UC2", channel=Channel.WHATSAPP)
        orchestrator = OrchestratorAgent(emitter)

        result = await orchestrator.handle_message(
            message=message,
            customer_id=customer_id,
            channel=Channel.WHATSAPP,
            session_id=session_id,
        )

        intent = result.get("intent", "unknown")
        summary = result.get("summary", message)
        reply = (
            f"🏦 BNB Bank\n\n"
            f"Namaste! We received your message.\n"
            f"Request type: {intent.replace('_', ' ').title()}\n\n"
            f"{summary}\n\n"
            f"Our team is processing your request. "
            f"You'll receive an update shortly.\n\n"
            f"Ref: {session_id}"
        )
        _emit_chat_event(from_phone, reply, direction="outbound")
        await send_whatsapp_message(from_phone, reply)

    return {"status": "ok"}


def _emit_chat_event(phone: str, message: str, direction: str = "inbound"):
    """Push a chat message event to the SSE bus for dashboard WhatsApp panel."""
    import time as _time
    chat_event = {
        "type": "chat",
        "phone": phone,
        "message": message,
        "direction": direction,
        "timestamp": _time.time(),
    }
    payload = json.dumps(chat_event, default=str)
    for q in _event_subscribers:
        try:
            q.put_nowait(payload)
        except asyncio.QueueFull:
            pass


async def _emit_step_events(completed_step: str, session, emitter, phone: str):
    """Emit rich cascading agent events for each completed onboarding step."""
    customer_id = f"NEW-{phone}"
    DELAY = 0.4

    if completed_step == "name":
        emitter.emit(
            agent_id="orchestrator", agent_name="Orchestrator",
            action="input_processed",
            output_data={"field": "full_name", "value": session.name, "step": "2/8"},
            reasoning=f"Customer name '{session.name}' captured — requesting Aadhaar for eKYC",
            confidence=0.99, latency_ms=65, event_type="decision",
            next_agents=["customer360-agent"], customer_id=customer_id,
        )
        await asyncio.sleep(DELAY)
        emitter.emit(
            agent_id="customer360-agent", agent_name="Customer 360",
            action="profile_initialized",
            output_data={"name": session.name, "phone": phone, "status": "pending_kyc"},
            reasoning="New customer profile created in CRM — awaiting KYC verification",
            confidence=0.95, latency_ms=180,
            next_agents=["document-agent"], customer_id=customer_id,
        )

    elif completed_step == "aadhaar":
        last4 = session.aadhaar[-4:] if session.aadhaar else "XXXX"
        emitter.emit(
            agent_id="document-agent", agent_name="Document AI",
            action="aadhaar_parsed",
            output_data={"aadhaar_masked": f"XXXX-XXXX-{last4}", "checksum": "valid", "format": "12-digit"},
            reasoning="Aadhaar number parsed — Verhoeff checksum validated successfully",
            confidence=0.99, latency_ms=95,
            next_agents=["kyc-agent"], customer_id=customer_id,
        )
        await asyncio.sleep(DELAY)
        emitter.emit(
            agent_id="kyc-agent", agent_name="KYC / AML",
            action="uidai_verification",
            output_data={"status": "verified", "aadhaar_last4": last4, "api": "UIDAI_eKYC"},
            reasoning="UIDAI eKYC API: Aadhaar found in database, OTP dispatched to registered mobile",
            confidence=0.97, latency_ms=320,
            next_agents=["fraud-analysis-agent"], customer_id=customer_id,
        )
        await asyncio.sleep(DELAY)
        emitter.emit(
            agent_id="fraud-analysis-agent", agent_name="Fraud Analysis",
            action="duplicate_check",
            output_data={"duplicates_found": 0, "status": "clear", "db_searched": "pan_india"},
            reasoning="Screened against 50M+ existing accounts — no duplicate registrations found",
            confidence=0.98, latency_ms=250,
            next_agents=["notification-agent"], customer_id=customer_id,
        )
        await asyncio.sleep(DELAY)
        emitter.emit(
            agent_id="notification-agent", agent_name="Notification",
            action="otp_dispatched",
            output_data={"channel": "whatsapp", "otp_type": "uidai_simulated", "validity": "15min"},
            reasoning="6-digit OTP sent to customer's WhatsApp (simulated UIDAI gateway)",
            confidence=0.99, latency_ms=75,
            customer_id=customer_id,
        )

    elif completed_step == "otp":
        emitter.emit(
            agent_id="kyc-agent", agent_name="KYC / AML",
            action="otp_verified",
            output_data={"status": "match", "attempts_used": 1, "method": "uidai_otp"},
            reasoning="OTP verification successful — UIDAI eKYC authentication complete",
            confidence=0.99, latency_ms=65,
            next_agents=["document-agent"], customer_id=customer_id,
        )
        await asyncio.sleep(DELAY)
        emitter.emit(
            agent_id="document-agent", agent_name="Document AI",
            action="ekyc_extracted",
            output_data={"fields": ["name", "dob", "address", "photo"], "source": "UIDAI", "status": "retrieved"},
            reasoning="eKYC data extracted from UIDAI — name, DOB, address, photo retrieved",
            confidence=0.96, latency_ms=280,
            next_agents=["customer360-agent"], customer_id=customer_id,
        )
        await asyncio.sleep(DELAY)
        emitter.emit(
            agent_id="customer360-agent", agent_name="Customer 360",
            action="profile_enriched",
            output_data={"fields_updated": ["dob", "address", "photo", "aadhaar_verified"], "ekyc_status": "verified"},
            reasoning="Customer profile enriched with UIDAI eKYC data — pending customer confirmation",
            confidence=0.95, latency_ms=150,
            customer_id=customer_id,
        )

    elif completed_step == "confirm_ekyc":
        emitter.emit(
            agent_id="kyc-agent", agent_name="KYC / AML",
            action="ekyc_confirmed",
            output_data={"customer_consent": True, "consent_timestamp": "recorded"},
            reasoning="Customer explicitly confirmed eKYC data accuracy — consent recorded",
            confidence=0.99, latency_ms=45,
            next_agents=["orchestrator"], customer_id=customer_id,
        )
        await asyncio.sleep(DELAY)
        emitter.emit(
            agent_id="orchestrator", agent_name="Orchestrator",
            action="compliance_cleared",
            output_data={"regulation": "RBI_KYC_Master_Direction_2016", "ekyc_status": "confirmed"},
            reasoning="RBI eKYC regulatory requirement satisfied — proceeding to PAN verification",
            confidence=0.97, latency_ms=180, event_type="decision",
            next_agents=["document-agent"], customer_id=customer_id,
        )

    elif completed_step == "pan":
        pan_masked = f"{session.pan[:2]}XXX{session.pan[-2:]}" if session.pan else "XXXXX"
        emitter.emit(
            agent_id="document-agent", agent_name="Document AI",
            action="pan_validated",
            output_data={"pan_masked": pan_masked, "format": "valid", "type": "individual"},
            reasoning="PAN format verified — Income Tax Department database cross-check initiated",
            confidence=0.99, latency_ms=110,
            next_agents=["kyc-agent"], customer_id=customer_id,
        )
        await asyncio.sleep(DELAY)
        emitter.emit(
            agent_id="kyc-agent", agent_name="KYC / AML",
            action="pan_aadhaar_linked",
            output_data={"linkage_status": "confirmed", "source": "income_tax_db"},
            reasoning="PAN-Aadhaar linkage confirmed via Income Tax Department API",
            confidence=0.96, latency_ms=280,
            next_agents=["fraud-analysis-agent"], customer_id=customer_id,
        )
        await asyncio.sleep(DELAY)
        emitter.emit(
            agent_id="fraud-analysis-agent", agent_name="Fraud Analysis",
            action="aml_screening",
            output_data={"pep_check": "clear", "sanctions": "clear", "adverse_media": "clear", "risk_db": "WorldCheck"},
            reasoning="AML screening: PEP check clear, OFAC/UN sanctions clear, adverse media clear",
            confidence=0.98, latency_ms=350,
            next_agents=["customer360-agent"], customer_id=customer_id,
        )
        await asyncio.sleep(DELAY)
        emitter.emit(
            agent_id="customer360-agent", agent_name="Customer 360",
            action="risk_assessed",
            output_data={"risk_score": 0.12, "risk_level": "LOW", "category": "retail_standard"},
            reasoning="Customer risk score: 0.12 (LOW) — eligible for standard digital savings account",
            confidence=0.94, latency_ms=200, event_type="decision",
            next_agents=["orchestrator"], customer_id=customer_id,
        )

    elif completed_step == "video_kyc":
        emitter.emit(
            agent_id="kyc-agent", agent_name="KYC / AML",
            action="video_kyc_initiated",
            output_data={"mode": "ai_assisted", "resolution": "720p", "rbi_mandate": True},
            reasoning="Video KYC session initiated — RBI mandate for digital account opening",
            confidence=0.98, latency_ms=150,
            next_agents=["fraud-analysis-agent"], customer_id=customer_id,
        )
        await asyncio.sleep(DELAY)
        emitter.emit(
            agent_id="fraud-analysis-agent", agent_name="Fraud Analysis",
            action="liveness_verified",
            output_data={"liveness_score": 0.994, "spoofing_detected": False, "method": "3d_depth_map"},
            reasoning="Liveness detection passed: score 0.994, no spoofing indicators detected",
            confidence=0.97, latency_ms=280,
            next_agents=["kyc-agent"], customer_id=customer_id,
        )
        await asyncio.sleep(DELAY)
        emitter.emit(
            agent_id="kyc-agent", agent_name="KYC / AML",
            action="biometric_matched",
            output_data={"match_score": 0.987, "method": "aadhaar_photo_vs_live", "threshold": 0.85},
            reasoning="Biometric face match: 98.7% confidence — Aadhaar photo vs live capture",
            confidence=0.987, latency_ms=320,
            next_agents=["account-agent"], customer_id=customer_id,
        )


async def _finalize_onboarding(session, emitter, phone: str):
    """Create the customer record and emit rich account creation cascade."""
    from backend.shared.mock_data.generator import create_demo_customer
    from backend.channels.whatsapp.handler import register_phone

    print(f"[WA-WEBHOOK] Finalizing onboarding for {phone}, name={session.name}")
    customer_id = f"NEW-{phone}"
    DELAY = 0.4

    # ── Rich finalization cascade: Account → Card → Product Rec → Notification → Orchestrator ──
    try:
        emitter.emit(
            agent_id="account-agent", agent_name="Account Service",
            action="account_created",
            output_data={"account_type": "Digital Savings", "currency": "INR", "ifsc": "BNB0001234", "neft": True, "upi": True},
            reasoning="Digital savings account provisioned — zero balance, NEFT/IMPS/UPI enabled",
            confidence=0.99, latency_ms=250,
            next_agents=["card-management-agent"], customer_id=customer_id,
        )
        await asyncio.sleep(DELAY)
        emitter.emit(
            agent_id="card-management-agent", agent_name="Card Management",
            action="virtual_card_issued",
            output_data={"card_type": "RuPay Platinum", "status": "activated", "limit": "₹2,00,000", "virtual": True},
            reasoning="Virtual RuPay Platinum debit card generated and linked to new account",
            confidence=0.98, latency_ms=180,
            next_agents=["product-recommendation-agent"], customer_id=customer_id,
        )
        await asyncio.sleep(DELAY)
        emitter.emit(
            agent_id="product-recommendation-agent", agent_name="Product Recommendation",
            action="products_suggested",
            output_data={"suggestions": ["Recurring Deposit @ 7.1%", "Health Insurance", "BNB Credit Card"], "model": "collaborative_filtering"},
            reasoning="AI recommendation: customer profile suggests RD, health insurance, credit card eligibility",
            confidence=0.92, latency_ms=350, event_type="decision",
            next_agents=["notification-agent"], customer_id=customer_id,
        )
        await asyncio.sleep(DELAY)
    except Exception as e:
        print(f"[WA-WEBHOOK] Event emission error (non-fatal): {e}")

    # Register as a demo customer
    customer = None
    try:
        customer, account = create_demo_customer(
            name=session.name, phone=phone,
            aadhaar=session.aadhaar or "", pan=session.pan or "",
        )
        register_phone(customer.phone, customer.customer_id)
        print(f"[WA-WEBHOOK] Customer registered: {customer.customer_id} phone={customer.phone}")
    except ValueError as e:
        print(f"[WA-WEBHOOK] Customer already exists: {e}")
    except Exception as e:
        print(f"[WA-WEBHOOK] Customer registration error: {e}")

    # Final cascade events
    try:
        final_cid = customer.customer_id if customer else customer_id
        emitter.emit(
            agent_id="notification-agent", agent_name="Notification",
            action="welcome_dispatched",
            output_data={"channel": "whatsapp", "content": "account_details + welcome_kit + card_info"},
            reasoning="Welcome package with account details, debit card info dispatched via WhatsApp",
            confidence=0.99, latency_ms=65,
            next_agents=["orchestrator"], customer_id=final_cid,
        )
        await asyncio.sleep(DELAY)
        emitter.emit(
            agent_id="orchestrator", agent_name="Orchestrator",
            action="onboarding_complete",
            output_data={"customer_id": final_cid, "steps_completed": 8, "status": "✅ success",
                         "accounts": ["savings"], "cards": ["RuPay Platinum"]},
            reasoning="✅ Full digital KYC onboarding completed — all RBI regulatory checks passed",
            confidence=1.0, latency_ms=45, event_type="decision",
            customer_id=final_cid,
        )
    except Exception as e:
        print(f"[WA-WEBHOOK] Final event emission error: {e}")


@app.post("/api/whatsapp/send")
async def whatsapp_send(request: Request):
    """Send a WhatsApp message to a customer (for testing / agent-initiated messages)."""
    from backend.channels.whatsapp.handler import send_whatsapp_message

    body = await request.json()
    to_phone = body.get("to", "")
    message = body.get("message", "")
    if not to_phone or not message:
        return {"error": "Missing 'to' and 'message' fields"}, 400

    result = await send_whatsapp_message(to_phone, message)
    return result

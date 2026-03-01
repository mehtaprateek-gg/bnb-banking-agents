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

            emitter.emit(
                agent_id="orchestrator", agent_name="Orchestrator Agent",
                action="onboarding_initiated",
                input_data={"message": message, "phone": from_phone},
                output_data={"intent": "onboarding", "flow": "sbi_yono_style"},
                reasoning="Detected account opening request — starting multi-turn onboarding",
                customer_id=f"NEW-{from_phone}",
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
            print(f"[WA-WEBHOOK] Active session for {from_phone}, step={get_session(from_phone).step if get_session(from_phone) else 'None'}")
            session = get_session(from_phone)
            if not session:
                continue

            session_id = f"wa-onboard-{uuid.uuid4().hex[:8]}"
            emitter = SSEEventEmitter(session_id=session_id, use_case="UC1", channel=Channel.WHATSAPP)

            # Run agents at specific steps
            await _run_onboarding_agents(session, emitter, from_phone)

            reply, is_complete = handle_step(session, message)
            print(f"[WA-WEBHOOK] Step reply (complete={is_complete}, step={session.step}): {reply[:120]}...")
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


async def _run_onboarding_agents(session, emitter, phone: str):
    """Call the appropriate agents based on the conversation step for event emission."""
    step = session.step
    customer_id = f"NEW-{phone}"

    if step == "aadhaar":
        from backend.agents.identity_verify.agent import IdentityVerifyAgent
        agent = IdentityVerifyAgent(emitter)
        await agent.verify_aadhaar(session.aadhaar if session.aadhaar else "999999999999")

    elif step == "otp":
        from backend.agents.document_agent.agent import DocumentAgent
        agent = DocumentAgent(emitter)
        await agent.extract_aadhaar_data(b"mock-aadhaar-photo")

    elif step == "pan":
        from backend.agents.identity_verify.agent import IdentityVerifyAgent
        from backend.agents.kyc_aml.agent import KycAmlAgent
        id_agent = IdentityVerifyAgent(emitter)
        kyc = KycAmlAgent(emitter)
        await id_agent.verify_pan(session.pan if session.pan else "ABCDE1234F")
        await kyc.run_aml_check({"name": session.name, "customer_id": customer_id})

    elif step == "video_kyc":
        from backend.agents.identity_verify.agent import IdentityVerifyAgent
        agent = IdentityVerifyAgent(emitter)
        await agent.verify_selfie(b"mock-selfie")


async def _finalize_onboarding(session, emitter, phone: str):
    """Create the customer record and emit account creation events."""
    from backend.agents.account_provision.agent import AccountProvisionAgent
    from backend.shared.mock_data.generator import create_demo_customer
    from backend.channels.whatsapp.handler import register_phone

    print(f"[WA-WEBHOOK] Finalizing onboarding for {phone}, name={session.name}")

    try:
        acct_agent = AccountProvisionAgent(emitter)
        await acct_agent.create_account({"customer_id": f"NEW-{phone}", "name": session.name})
        await acct_agent.send_welcome(f"NEW-{phone}", "whatsapp")
    except Exception as e:
        print(f"[WA-WEBHOOK] Agent error (non-fatal): {e}")

    # Register as a demo customer
    try:
        customer, account = create_demo_customer(
            name=session.name, phone=phone,
            aadhaar=session.aadhaar or "", pan=session.pan or "",
        )
        register_phone(customer.phone, customer.customer_id)
        print(f"[WA-WEBHOOK] Customer registered: {customer.customer_id} phone={customer.phone}")
        emitter.emit(
            agent_id="account-provision", agent_name="Account Provision Agent",
            action="customer_registered",
            output_data={"customer_id": customer.customer_id, "name": session.name},
            customer_id=customer.customer_id,
        )
    except ValueError as e:
        print(f"[WA-WEBHOOK] Customer already exists: {e}")
    except Exception as e:
        print(f"[WA-WEBHOOK] Customer registration error: {e}")


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

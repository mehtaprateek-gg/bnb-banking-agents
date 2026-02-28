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
from fastapi.responses import StreamingResponse
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
        "registry_source": "copilot_studio",
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
    """Retrieve customers (from mock data generator — Cosmos DB is seeded identically)."""
    from backend.shared.mock_data.generator import generate_customers
    customers = generate_customers()
    return [c.model_dump(mode="json") for c in customers]


@app.get("/api/cosmos/transactions/{customer_id}")
async def list_transactions(customer_id: str, limit: int = 10):
    """Retrieve transactions for a customer (from mock data generator)."""
    from backend.shared.mock_data.generator import generate_transactions
    txns = generate_transactions(customer_id, days=30, count=25)
    return [t.model_dump(mode="json") for t in txns[:limit]]

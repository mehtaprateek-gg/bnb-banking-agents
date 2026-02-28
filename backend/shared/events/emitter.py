"""Event emitter for streaming agent actions to the visualization dashboard."""

import json
import uuid
from datetime import datetime
from typing import Optional

from backend.shared.models.banking import AgentEvent, Channel, Language, Sentiment


class EventEmitter:
    """Emits structured events from agents for real-time dashboard visualization."""

    def __init__(self, session_id: str, use_case: str, channel: Channel = Channel.MOBILE):
        self.session_id = session_id
        self.use_case = use_case
        self.channel = channel
        self._events: list[AgentEvent] = []

    def emit(
        self,
        agent_id: str,
        agent_name: str,
        action: str,
        input_data: Optional[dict] = None,
        output_data: Optional[dict] = None,
        reasoning: str = "",
        tokens_used: int = 0,
        latency_ms: float = 0.0,
        confidence: float = 0.0,
        next_agents: Optional[list[str]] = None,
        customer_id: str = "",
        language: Language = Language.HINDI,
        sentiment: Sentiment = Sentiment.NEUTRAL,
        event_type: str = "action",
    ) -> AgentEvent:
        """Emit a single agent event."""
        event = AgentEvent(
            event_id=f"evt-{uuid.uuid4().hex[:12]}",
            timestamp=datetime.utcnow(),
            session_id=self.session_id,
            use_case=self.use_case,
            agent_id=agent_id,
            agent_name=agent_name,
            event_type=event_type,
            action=action,
            input_data=input_data or {},
            output_data=output_data or {},
            reasoning=reasoning,
            tokens_used=tokens_used,
            latency_ms=latency_ms,
            confidence=confidence,
            next_agents=next_agents or [],
            channel=self.channel,
            customer_id=customer_id,
            language=language,
            sentiment=sentiment,
        )
        self._events.append(event)
        return event

    def get_events(self) -> list[AgentEvent]:
        """Return all emitted events."""
        return self._events

    def to_json(self) -> str:
        """Serialize all events to JSON."""
        return json.dumps(
            [event.model_dump(mode="json") for event in self._events],
            indent=2,
            default=str,
        )

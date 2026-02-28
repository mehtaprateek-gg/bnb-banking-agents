"""Pydantic data models for BNB Banking multi-agent system."""

from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class Channel(str, Enum):
    WHATSAPP = "whatsapp"
    VOICE = "voice"
    MOBILE = "mobile"


class Language(str, Enum):
    HINDI = "hi"
    ENGLISH = "en"
    HINGLISH = "hi-en"


class Sentiment(str, Enum):
    POSITIVE = "positive"
    NEUTRAL = "neutral"
    NEGATIVE = "negative"
    FRUSTRATED = "frustrated"


class AgentType(str, Enum):
    ROUTER = "router"
    CHANNEL = "channel"
    SPECIALIST = "specialist"


class CaseStatus(str, Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    ESCALATED = "escalated"


class Customer(BaseModel):
    customer_id: str
    name: str
    phone: str
    email: Optional[str] = None
    aadhaar_masked: Optional[str] = None
    pan_masked: Optional[str] = None
    account_number: Optional[str] = None
    account_type: Optional[str] = None
    segment: str = "retail"
    rm_name: Optional[str] = None
    language_preference: Language = Language.HINDI
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Transaction(BaseModel):
    transaction_id: str
    customer_id: str
    date: datetime
    description: str
    amount: float
    currency: str = "INR"
    category: str
    merchant: Optional[str] = None
    is_credit: bool = False
    is_disputed: bool = False


class Account(BaseModel):
    account_id: str
    customer_id: str
    account_number: str
    account_type: str
    balance: float
    currency: str = "INR"
    ifsc_code: str
    branch: str
    status: str = "active"


class Case(BaseModel):
    case_id: str
    customer_id: str
    case_type: str
    status: CaseStatus = CaseStatus.OPEN
    priority: str = "medium"
    channel: Channel
    summary: str
    assigned_rm: Optional[str] = None
    resolution: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class AgentRegistryEntry(BaseModel):
    agent_id: str
    display_name: str
    description: str
    version: str = "1.0.0"
    agent_type: AgentType
    use_cases: list[str]
    endpoint: str
    capabilities: list[str]
    llm_model: str = "gpt-4o"
    max_tokens: int = 4096
    temperature: float = 0.3
    status: str = "active"
    avg_latency_ms: float = 0.0
    calls_last_24h: int = 0
    error_rate: float = 0.0


class AgentEvent(BaseModel):
    event_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    session_id: str
    use_case: str
    agent_id: str
    agent_name: str
    event_type: str = "action"
    action: str
    input_data: dict = Field(default_factory=dict)
    output_data: dict = Field(default_factory=dict)
    reasoning: str = ""
    tokens_used: int = 0
    latency_ms: float = 0.0
    confidence: float = 0.0
    next_agents: list[str] = Field(default_factory=list)
    channel: Channel = Channel.MOBILE
    customer_id: str = ""
    language: Language = Language.HINDI
    sentiment: Sentiment = Sentiment.NEUTRAL

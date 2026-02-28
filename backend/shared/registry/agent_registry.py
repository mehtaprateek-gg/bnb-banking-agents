"""Agent registry for discovering and managing AI agents."""

from typing import Optional
from backend.shared.models.banking import AgentRegistryEntry, AgentType


# In-memory registry for PoC (will be backed by Cosmos DB in production)
_REGISTRY: dict[str, AgentRegistryEntry] = {}


def register_agent(entry: AgentRegistryEntry) -> None:
    """Register an agent in the registry."""
    _REGISTRY[entry.agent_id] = entry


def get_agent(agent_id: str) -> Optional[AgentRegistryEntry]:
    """Get agent by ID."""
    return _REGISTRY.get(agent_id)


def list_agents(agent_type: Optional[AgentType] = None, use_case: Optional[str] = None) -> list[AgentRegistryEntry]:
    """List agents, optionally filtered by type or use case."""
    agents = list(_REGISTRY.values())
    if agent_type:
        agents = [a for a in agents if a.agent_type == agent_type]
    if use_case:
        agents = [a for a in agents if use_case in a.use_cases]
    return agents


def initialize_registry() -> None:
    """Initialize the registry with all BNB agents."""
    agents = [
        AgentRegistryEntry(
            agent_id="orchestrator", display_name="Orchestrator Agent",
            description="Central orchestrator - intent classification, agent selection, workflow management",
            agent_type=AgentType.ROUTER, use_cases=["UC1", "UC2", "UC3"],
            endpoint="/api/orchestrator", capabilities=["intent_classification", "agent_routing", "context_management"],
        ),
        AgentRegistryEntry(
            agent_id="whatsapp-agent", display_name="WhatsApp Agent",
            description="WhatsApp Business API channel handler for natural chat",
            agent_type=AgentType.CHANNEL, use_cases=["UC1", "UC2", "UC3"],
            endpoint="/api/whatsapp", capabilities=["chat", "rich_media", "quick_replies", "document_upload"],
        ),
        AgentRegistryEntry(
            agent_id="voice-agent", display_name="Voice Agent",
            description="Voice call handler with real-time STT/TTS in Hindi and English",
            agent_type=AgentType.CHANNEL, use_cases=["UC2", "UC3"],
            endpoint="/api/voice", capabilities=["stt", "tts", "sentiment_analysis", "call_recording", "rm_handoff"],
        ),
        AgentRegistryEntry(
            agent_id="identity-verify", display_name="Identity Verification Agent",
            description="Validates Aadhaar, PAN, selfie match for customer onboarding",
            agent_type=AgentType.SPECIALIST, use_cases=["UC1"],
            endpoint="/api/identity-verify", capabilities=["aadhaar_verify", "pan_verify", "selfie_match", "liveness_check"],
        ),
        AgentRegistryEntry(
            agent_id="kyc-aml", display_name="KYC/AML Compliance Agent",
            description="Anti-money laundering checks, sanctions screening, risk scoring",
            agent_type=AgentType.SPECIALIST, use_cases=["UC1"],
            endpoint="/api/kyc-aml", capabilities=["aml_screening", "sanctions_check", "risk_scoring"],
        ),
        AgentRegistryEntry(
            agent_id="document-agent", display_name="Document Agent",
            description="Extracts data from Aadhaar, PAN, address proof documents",
            agent_type=AgentType.SPECIALIST, use_cases=["UC1"],
            endpoint="/api/document-agent", capabilities=["ocr", "data_extraction", "document_classification"],
        ),
        AgentRegistryEntry(
            agent_id="account-provision", display_name="Account Provisioning Agent",
            description="Creates bank accounts, provisions Azure AD identity",
            agent_type=AgentType.SPECIALIST, use_cases=["UC1"],
            endpoint="/api/account-provision", capabilities=["create_account", "provision_identity", "send_welcome"],
        ),
        AgentRegistryEntry(
            agent_id="customer-360", display_name="Customer 360 Agent",
            description="Retrieves full customer profile from SharePoint CRM",
            agent_type=AgentType.SPECIALIST, use_cases=["UC2"],
            endpoint="/api/customer-360", capabilities=["get_profile", "get_history", "get_preferences"],
        ),
        AgentRegistryEntry(
            agent_id="transaction-agent", display_name="Transaction Agent",
            description="Queries transaction history, detects fraud patterns, initiates disputes",
            agent_type=AgentType.SPECIALIST, use_cases=["UC2", "UC3"],
            endpoint="/api/transaction", capabilities=["query_transactions", "fraud_analysis", "initiate_dispute", "categorize_spending"],
            temperature=0.2,
        ),
        AgentRegistryEntry(
            agent_id="card-mgmt", display_name="Card Management Agent",
            description="Handles card block/unblock, replacement, PIN reset",
            agent_type=AgentType.SPECIALIST, use_cases=["UC2"],
            endpoint="/api/card-mgmt", capabilities=["block_card", "unblock_card", "replace_card", "reset_pin"],
        ),
        AgentRegistryEntry(
            agent_id="loan-advisor", display_name="Loan Advisor Agent",
            description="Pre-qualifies customers, explains loan products, generates offers",
            agent_type=AgentType.SPECIALIST, use_cases=["UC2"],
            endpoint="/api/loan-advisor", capabilities=["pre_qualify", "product_recommend", "generate_offer", "emi_calculator"],
        ),
        AgentRegistryEntry(
            agent_id="spending-analytics", display_name="Spending Analytics Agent",
            description="Analyzes spending patterns, detects anomalies, categorizes expenses",
            agent_type=AgentType.SPECIALIST, use_cases=["UC3"],
            endpoint="/api/spending-analytics", capabilities=["spending_analysis", "anomaly_detection", "categorization", "trend_analysis"],
        ),
        AgentRegistryEntry(
            agent_id="savings-advisor", display_name="Savings Advisor Agent",
            description="Identifies saving opportunities, recommends FD/RD, suggests auto-sweep",
            agent_type=AgentType.SPECIALIST, use_cases=["UC3"],
            endpoint="/api/savings-advisor", capabilities=["savings_analysis", "fd_recommend", "goal_setting", "auto_sweep"],
        ),
        AgentRegistryEntry(
            agent_id="notification-agent", display_name="Notification Agent",
            description="Generates personalized notifications for WhatsApp, push, and voice",
            agent_type=AgentType.SPECIALIST, use_cases=["UC3"],
            endpoint="/api/notification", capabilities=["whatsapp_notify", "push_notify", "voice_notify", "template_generate"],
        ),
        AgentRegistryEntry(
            agent_id="compliance-guard", display_name="Compliance Guard Agent",
            description="Reviews outbound messages for RBI regulatory compliance",
            agent_type=AgentType.SPECIALIST, use_cases=["UC3"],
            endpoint="/api/compliance-guard", capabilities=["rbi_compliance_check", "disclaimer_verify", "prohibited_claims_check"],
        ),
        AgentRegistryEntry(
            agent_id="voice-summary", display_name="Voice Summary Agent",
            description="Delivers automated weekly financial summary via voice call",
            agent_type=AgentType.SPECIALIST, use_cases=["UC3"],
            endpoint="/api/voice-summary", capabilities=["generate_summary", "tts_delivery", "interactive_qa"],
        ),
    ]
    for agent in agents:
        register_agent(agent)

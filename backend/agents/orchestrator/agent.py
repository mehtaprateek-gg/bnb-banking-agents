"""Orchestrator agent – classifies intent, detects language, and routes to specialists.

Agent discovery is powered by Copilot Studio (Dataverse bots table).
"""

import json
import os
import time
import uuid
from typing import Optional

from openai import AsyncAzureOpenAI
from azure.identity import DefaultAzureCredential, get_bearer_token_provider

from backend.shared.events.emitter import EventEmitter
from backend.shared.models.banking import Channel, Language, Sentiment
from backend.shared.registry.copilot_studio_client import get_registry

AGENT_ID = "orchestrator"
AGENT_NAME = "Orchestrator Agent"

SYSTEM_PROMPT = """You are the BNB Bank orchestrator. Given a customer message, respond with a JSON object containing exactly these keys:
{
  "language": "hi" | "en" | "hi-en",
  "intent": "onboarding" | "dispute" | "balance_check" | "card_block" | "loan_inquiry" | "financial_health",
  "sentiment": "positive" | "neutral" | "negative" | "frustrated",
  "summary": "<one-line summary of what the customer wants>"
}
Only output the JSON, nothing else."""

_client: Optional[AsyncAzureOpenAI] = None
_token_provider = get_bearer_token_provider(
    DefaultAzureCredential(), "https://cognitiveservices.azure.com/.default"
)


def _get_client() -> AsyncAzureOpenAI:
    global _client
    if _client is None:
        _client = AsyncAzureOpenAI(
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT", "https://bnb-openai.openai.azure.com/"),
            api_version="2024-02-01",
            azure_ad_token_provider=_token_provider,
        )
    return _client


class OrchestratorAgent:
    """Central orchestrator that classifies intent and routes to specialist agents."""

    def __init__(self, emitter: EventEmitter):
        self.emitter = emitter
        self.conversation_context: dict[str, list[dict]] = {}

    async def handle_message(
        self,
        message: str,
        customer_id: str,
        channel: Channel = Channel.MOBILE,
        session_id: Optional[str] = None,
    ) -> dict:
        """Accept a customer message, classify intent, and route to specialists.

        Returns a dict with keys: language, intent, sentiment, summary, agents, results.
        """
        session_id = session_id or f"sess-{uuid.uuid4().hex[:8]}"

        # 1. Emit receipt event
        self.emitter.emit(
            agent_id=AGENT_ID,
            agent_name=AGENT_NAME,
            action="message_received",
            input_data={"message": message, "channel": channel.value},
            customer_id=customer_id,
        )

        # 2. Maintain conversation context
        self.conversation_context.setdefault(session_id, []).append(
            {"role": "user", "content": message}
        )

        # 3. Call Azure OpenAI for intent classification
        classification = await self._classify(message, customer_id)

        # 4. Discover specialist agents from Copilot Studio registry
        intent = classification.get("intent", "balance_check")
        registry = get_registry()
        cs_agents = registry.get_agents_for_intent(intent)
        agents_to_call = [a.agent_id for a in cs_agents]

        self.emitter.emit(
            agent_id=AGENT_ID,
            agent_name=AGENT_NAME,
            action="intent_classified",
            input_data={"message": message},
            output_data=classification,
            reasoning=f"Detected intent={intent}, routing to {agents_to_call}",
            confidence=0.92,
            next_agents=agents_to_call,
            customer_id=customer_id,
            language=Language(classification.get("language", "en")),
            sentiment=Sentiment(classification.get("sentiment", "neutral")),
        )

        # 5. Invoke specialists (imported lazily to avoid circular deps)
        results = await self._route(intent, customer_id, classification, message)

        # 6. Emit completion
        self.emitter.emit(
            agent_id=AGENT_ID,
            agent_name=AGENT_NAME,
            action="routing_complete",
            output_data={"intent": intent, "agent_count": len(results)},
            customer_id=customer_id,
        )

        return {
            **classification,
            "agents": agents_to_call,
            "results": results,
        }

    # ------------------------------------------------------------------
    async def _classify(self, message: str, customer_id: str) -> dict:
        """Use Azure OpenAI to classify language, intent and sentiment."""
        start = time.time()
        try:
            client = _get_client()
            resp = await client.chat.completions.create(
                model=os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o"),
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": message},
                ],
                temperature=0.1,
                max_tokens=256,
            )
            raw = (resp.choices[0].message.content or "{}").strip()
            # Strip markdown code fences if present
            if raw.startswith("```"):
                raw = raw.split("\n", 1)[1] if "\n" in raw else raw[3:]
                raw = raw.rsplit("```", 1)[0].strip()
            tokens = resp.usage.total_tokens if resp.usage else 0
            latency = (time.time() - start) * 1000

            self.emitter.emit(
                agent_id=AGENT_ID,
                agent_name=AGENT_NAME,
                action="llm_classification",
                input_data={"message": message},
                output_data={"raw_response": raw},
                tokens_used=tokens,
                latency_ms=latency,
                customer_id=customer_id,
            )
            return json.loads(raw)
        except Exception:
            # Fallback when Azure OpenAI is unavailable
            return {
                "language": "en",
                "intent": "balance_check",
                "sentiment": "neutral",
                "summary": message,
            }

    async def _route(
        self, intent: str, customer_id: str, classification: dict, message: str
    ) -> dict:
        """Route to the appropriate specialist agents and collect results."""
        results: dict = {}

        if intent == "onboarding":
            results = await self._handle_onboarding(customer_id)
        elif intent == "dispute":
            results = await self._handle_dispute(customer_id)
        elif intent == "balance_check":
            results = await self._handle_balance(customer_id)
        elif intent == "card_block":
            results = await self._handle_card_block(customer_id)
        elif intent == "loan_inquiry":
            results = await self._handle_loan_inquiry(customer_id)
        elif intent == "financial_health":
            results = await self._handle_financial_health(customer_id)

        return results

    # ---------- intent handlers ----------
    async def _handle_onboarding(self, customer_id: str) -> dict:
        from backend.agents.identity_verify.agent import IdentityVerifyAgent
        from backend.agents.kyc_aml.agent import KycAmlAgent
        from backend.agents.document_agent.agent import DocumentAgent
        from backend.agents.account_provision.agent import AccountProvisionAgent

        id_agent = IdentityVerifyAgent(self.emitter)
        kyc = KycAmlAgent(self.emitter)
        doc = DocumentAgent(self.emitter)
        acct = AccountProvisionAgent(self.emitter)

        aadhaar = await id_agent.verify_aadhaar("999999999999")
        pan = await id_agent.verify_pan("ABCDE1234F")
        selfie = await id_agent.verify_selfie(b"mock-selfie")
        doc_class = await doc.classify_document(b"mock-doc")
        aml = await kyc.run_aml_check({"name": "New Customer", "customer_id": customer_id})
        account = await acct.create_account({"customer_id": customer_id, "name": "New Customer"})
        welcome = await acct.send_welcome(customer_id, "mobile")

        return {
            "aadhaar_verification": aadhaar,
            "pan_verification": pan,
            "selfie_verification": selfie,
            "document_classification": doc_class,
            "aml_check": aml,
            "account_created": account,
            "welcome_sent": welcome,
        }

    async def _handle_dispute(self, customer_id: str) -> dict:
        from backend.agents.customer_360.agent import Customer360Agent
        from backend.agents.transaction.agent import TransactionAgent

        c360 = Customer360Agent(self.emitter)
        txn = TransactionAgent(self.emitter)

        profile = await c360.get_profile(customer_id)
        disputed = await txn.find_disputed(customer_id)
        return {"profile": profile, "disputed_transactions": disputed}

    async def _handle_balance(self, customer_id: str) -> dict:
        from backend.agents.customer_360.agent import Customer360Agent
        from backend.agents.transaction.agent import TransactionAgent

        c360 = Customer360Agent(self.emitter)
        txn = TransactionAgent(self.emitter)

        profile = await c360.get_profile(customer_id)
        recent = await txn.query_transactions(customer_id, days=7)
        return {"profile": profile, "recent_transactions": recent}

    async def _handle_card_block(self, customer_id: str) -> dict:
        from backend.agents.customer_360.agent import Customer360Agent
        from backend.agents.card_mgmt.agent import CardManagementAgent

        c360 = Customer360Agent(self.emitter)
        card = CardManagementAgent(self.emitter)

        profile = await c360.get_profile(customer_id)
        block_result = await card.block_card(customer_id, "XXXX-XXXX-XXXX-4321")
        return {"profile": profile, "card_blocked": block_result}

    async def _handle_loan_inquiry(self, customer_id: str) -> dict:
        from backend.agents.customer_360.agent import Customer360Agent
        from backend.agents.loan_advisor.agent import LoanAdvisorAgent

        c360 = Customer360Agent(self.emitter)
        loan = LoanAdvisorAgent(self.emitter)

        profile = await c360.get_profile(customer_id)
        eligibility = await loan.pre_qualify(customer_id)
        offer = await loan.generate_offer(customer_id)
        return {"profile": profile, "eligibility": eligibility, "offer": offer}

    async def _handle_financial_health(self, customer_id: str) -> dict:
        from backend.agents.customer_360.agent import Customer360Agent
        from backend.agents.transaction.agent import TransactionAgent
        from backend.agents.spending_analytics.agent import SpendingAnalyticsAgent
        from backend.agents.savings_advisor.agent import SavingsAdvisorAgent
        from backend.agents.notification.agent import NotificationAgent
        from backend.agents.compliance_guard.agent import ComplianceGuardAgent
        from backend.agents.voice_summary.agent import VoiceSummaryAgent

        c360 = Customer360Agent(self.emitter)
        txn = TransactionAgent(self.emitter)
        spending = SpendingAnalyticsAgent(self.emitter)
        savings = SavingsAdvisorAgent(self.emitter)
        notif = NotificationAgent(self.emitter)
        compliance = ComplianceGuardAgent(self.emitter)
        voice = VoiceSummaryAgent(self.emitter)

        profile = await c360.get_profile(customer_id)
        analysis = await spending.analyze_spending(customer_id, days=7)
        anomalies = await spending.detect_anomalies(customer_id)
        advice = await savings.generate_advice(customer_id)
        summary_script = await voice.generate_summary_script(customer_id, analysis)

        draft = await notif.draft_whatsapp_message(customer_id, analysis)
        review = await compliance.approve_or_flag(draft.get("message", ""))

        return {
            "profile": profile,
            "spending_analysis": analysis,
            "anomalies": anomalies,
            "savings_advice": advice,
            "voice_script": summary_script,
            "notification_draft": draft,
            "compliance_review": review,
        }

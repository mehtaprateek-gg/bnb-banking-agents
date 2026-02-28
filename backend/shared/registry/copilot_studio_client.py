"""Copilot Studio registry client — reads agent catalog from Dataverse bots table."""

import json
import logging
import os
from typing import Optional

import httpx
from azure.identity import DefaultAzureCredential, ClientSecretCredential

from backend.shared.models.banking import AgentRegistryEntry, AgentType

logger = logging.getLogger(__name__)

# Schema-name → agent_id mapping (matches existing Python agent module names)
_SCHEMA_TO_AGENT_ID = {
    "BNB_Orchestrator": "orchestrator",
    "BNB_WhatsApp": "whatsapp-agent",
    "BNB_Voice": "voice-agent",
    "BNB_IdentityVerify": "identity-verify",
    "BNB_KYCAML": "kyc-aml",
    "BNB_Document": "document-agent",
    "BNB_AccountProvision": "account-provision",
    "BNB_Customer360": "customer-360",
    "BNB_Transaction": "transaction-agent",
    "BNB_CardMgmt": "card-mgmt",
    "BNB_LoanAdvisor": "loan-advisor",
    "BNB_SpendingAnalytics": "spending-analytics",
    "BNB_SavingsAdvisor": "savings-advisor",
    "BNB_Notification": "notification-agent",
    "BNB_ComplianceGuard": "compliance-guard",
    "BNB_VoiceSummary": "voice-summary",
}


class CopilotStudioClient:
    """Client that discovers BNB agents from Copilot Studio (Dataverse bots table).

    Uses Azure DefaultAzureCredential for token acquisition when running
    in Azure (Managed Identity) and falls back to environment credentials
    for local development.
    """

    def __init__(self, dataverse_url: Optional[str] = None):
        self.dataverse_url = (
            dataverse_url
            or os.getenv("DATAVERSE_URL", "https://org8973c330.crm.dynamics.com")
        ).rstrip("/")
        self._credential = DefaultAzureCredential()
        self._cache: dict[str, AgentRegistryEntry] = {}

    def _get_token(self) -> str:
        """Acquire an access token scoped to the Dataverse environment."""
        scope = f"{self.dataverse_url}/.default"
        token = self._credential.get_token(scope)
        return token.token

    def _headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self._get_token()}",
            "OData-MaxVersion": "4.0",
            "OData-Version": "4.0",
            "Accept": "application/json",
        }

    # ------------------------------------------------------------------
    # Public API (mirrors the old in-memory registry interface)
    # ------------------------------------------------------------------

    async def refresh_cache(self) -> None:
        """Fetch all BNB bots from Dataverse and populate the local cache."""
        url = (
            f"{self.dataverse_url}/api/data/v9.2/bots"
            "?$filter=startswith(schemaname,'BNB_')"
            "&$select=botid,name,schemaname,configuration,statecode,statuscode,createdon"
        )
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(url, headers=self._headers())
            resp.raise_for_status()
            data = resp.json()

        self._cache.clear()
        for bot in data.get("value", []):
            entry = self._bot_to_entry(bot)
            if entry:
                self._cache[entry.agent_id] = entry

        logger.info("Copilot Studio cache refreshed: %d agents loaded", len(self._cache))

    def _bot_to_entry(self, bot: dict) -> Optional[AgentRegistryEntry]:
        """Convert a Dataverse bot record into an AgentRegistryEntry."""
        schema = bot.get("schemaname", "")
        agent_id = _SCHEMA_TO_AGENT_ID.get(schema)
        if not agent_id:
            return None

        config = bot.get("configuration", "{}")
        if isinstance(config, str):
            try:
                config = json.loads(config)
            except json.JSONDecodeError:
                config = {}

        meta = config.get("bnbAgentMetadata", {})
        agent_type_str = meta.get("agentType", "specialist")
        try:
            agent_type = AgentType(agent_type_str)
        except ValueError:
            agent_type = AgentType.SPECIALIST

        return AgentRegistryEntry(
            agent_id=agent_id,
            display_name=bot.get("name", schema),
            description=meta.get("description", bot.get("name", "")),
            agent_type=agent_type,
            use_cases=meta.get("useCases", []),
            endpoint=meta.get("endpoint", f"/api/{agent_id}"),
            capabilities=meta.get("capabilities", []),
            llm_model=meta.get("model", "gpt-4o"),
            temperature=meta.get("temperature", 0.3),
            max_tokens=meta.get("maxTokens", 4096),
            status="active" if bot.get("statecode") == 0 else "inactive",
            # Copilot Studio bot ID for cross-referencing
            version=bot.get("botid", "1.0.0"),
        )

    # ------------------------------------------------------------------
    # Registry interface (drop-in replacement for old in-memory module)
    # ------------------------------------------------------------------

    def get_agent(self, agent_id: str) -> Optional[AgentRegistryEntry]:
        """Return a single agent by its logical ID."""
        return self._cache.get(agent_id)

    def list_agents(
        self,
        agent_type: Optional[AgentType] = None,
        use_case: Optional[str] = None,
    ) -> list[AgentRegistryEntry]:
        """List agents, optionally filtered by type or use case."""
        agents = list(self._cache.values())
        if agent_type:
            agents = [a for a in agents if a.agent_type == agent_type]
        if use_case:
            agents = [a for a in agents if use_case in a.use_cases]
        return agents

    def get_agents_for_intent(self, intent: str) -> list[AgentRegistryEntry]:
        """Return the ordered list of specialist agents for a given intent.

        The mapping intentionally mirrors the INTENT_AGENTS dict from the
        orchestrator so that agent discovery is fully driven by the registry.
        """
        intent_map: dict[str, list[str]] = {
            "onboarding": ["identity-verify", "kyc-aml", "document-agent", "account-provision"],
            "dispute": ["customer-360", "transaction-agent"],
            "balance_check": ["customer-360", "transaction-agent"],
            "card_block": ["customer-360", "card-mgmt"],
            "loan_inquiry": ["customer-360", "loan-advisor"],
            "financial_health": [
                "customer-360", "transaction-agent", "spending-analytics",
                "savings-advisor", "notification-agent", "compliance-guard",
                "voice-summary",
            ],
        }
        ids = intent_map.get(intent, ["customer-360"])
        return [self._cache[aid] for aid in ids if aid in self._cache]

    # ------------------------------------------------------------------
    # Dataverse write-back helpers (optional — for runtime stats)
    # ------------------------------------------------------------------

    async def update_agent_stats(
        self, agent_id: str, latency_ms: float, error: bool = False
    ) -> None:
        """Push runtime telemetry back to the bot record in Dataverse."""
        entry = self._cache.get(agent_id)
        if not entry:
            return

        bot_id = entry.version  # we stored botid in the version field
        entry.calls_last_24h += 1
        entry.avg_latency_ms = (
            entry.avg_latency_ms * 0.9 + latency_ms * 0.1
        )
        if error:
            entry.error_rate = min(1.0, entry.error_rate + 0.01)

        # Async PATCH to Dataverse (fire-and-forget for PoC)
        url = f"{self.dataverse_url}/api/data/v9.2/bots({bot_id})"
        config = {
            "bnbAgentMetadata": {
                "avgLatencyMs": entry.avg_latency_ms,
                "callsLast24h": entry.calls_last_24h,
                "errorRate": entry.error_rate,
            }
        }
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                await client.patch(
                    url,
                    headers={**self._headers(), "Content-Type": "application/json"},
                    json={"configuration": json.dumps(config)},
                )
        except Exception as exc:
            logger.warning("Failed to update bot stats in Dataverse: %s", exc)


# ------------------------------------------------------------------
# Module-level singleton (lazy-initialised)
# ------------------------------------------------------------------

_client: Optional[CopilotStudioClient] = None


def get_registry() -> CopilotStudioClient:
    """Return the module-level CopilotStudioClient singleton."""
    global _client
    if _client is None:
        _client = CopilotStudioClient()
    return _client

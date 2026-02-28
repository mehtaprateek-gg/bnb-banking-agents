"""Agent registry — backed by Copilot Studio (Dataverse bots table).

This module provides backward-compatible helper functions (get_agent,
list_agents, initialize_registry) that delegate to the CopilotStudioClient.
Existing code can keep calling these functions unchanged.
"""

import asyncio
import logging
from typing import Optional

from backend.shared.models.banking import AgentRegistryEntry, AgentType
from backend.shared.registry.copilot_studio_client import CopilotStudioClient, get_registry

logger = logging.getLogger(__name__)


def get_agent(agent_id: str) -> Optional[AgentRegistryEntry]:
    """Get agent by ID from Copilot Studio registry."""
    return get_registry().get_agent(agent_id)


def list_agents(
    agent_type: Optional[AgentType] = None,
    use_case: Optional[str] = None,
) -> list[AgentRegistryEntry]:
    """List agents from Copilot Studio, optionally filtered."""
    return get_registry().list_agents(agent_type=agent_type, use_case=use_case)


def initialize_registry() -> None:
    """Load agent catalog from Copilot Studio (Dataverse) into local cache.

    This replaces the old hard-coded in-memory initialization.
    Runs the async refresh synchronously so callers don't need to change.
    """
    registry = get_registry()
    try:
        loop = asyncio.get_running_loop()
        # If there's already an event loop, schedule and await
        loop.create_task(registry.refresh_cache())
        logger.info("Scheduled Copilot Studio cache refresh (async context)")
    except RuntimeError:
        # No event loop — run synchronously
        asyncio.run(registry.refresh_cache())
        logger.info("Copilot Studio cache refreshed (sync context)")

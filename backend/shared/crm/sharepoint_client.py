"""SharePoint CRM client for accessing M365 tenant via Microsoft Graph API."""

import os
from typing import Optional

import httpx


class SharePointCRMClient:
    """Accesses SharePoint Online CRM data via Microsoft Graph API using client credentials."""

    GRAPH_BASE = "https://graph.microsoft.com/v1.0"

    def __init__(
        self,
        tenant_id: Optional[str] = None,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        site_url: Optional[str] = None,
    ):
        self.tenant_id = tenant_id or os.getenv("M365_TENANT_ID")
        self.client_id = client_id or os.getenv("M365_APP_CLIENT_ID")
        self.client_secret = client_secret or os.getenv("M365_APP_CLIENT_SECRET")
        self.site_url = site_url or os.getenv("SHAREPOINT_SITE_URL")
        self._access_token: Optional[str] = None
        self._site_id: Optional[str] = None

    async def _get_token(self) -> str:
        """Get access token using client credentials flow."""
        if self._access_token:
            return self._access_token

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"https://login.microsoftonline.com/{self.tenant_id}/oauth2/v2.0/token",
                data={
                    "grant_type": "client_credentials",
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "scope": "https://graph.microsoft.com/.default",
                },
            )
            response.raise_for_status()
            self._access_token = response.json()["access_token"]
            return self._access_token

    async def _get_headers(self) -> dict:
        token = await self._get_token()
        return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    async def get_site_id(self) -> str:
        """Get the SharePoint site ID."""
        if self._site_id:
            return self._site_id

        headers = await self._get_headers()
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.GRAPH_BASE}/sites/root", headers=headers)
            response.raise_for_status()
            self._site_id = response.json()["id"]
            return self._site_id

    async def create_list(self, display_name: str, columns: list[dict]) -> dict:
        """Create a SharePoint list for CRM data."""
        site_id = await self.get_site_id()
        headers = await self._get_headers()

        body = {
            "displayName": display_name,
            "columns": columns,
            "list": {"template": "genericList"},
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.GRAPH_BASE}/sites/{site_id}/lists",
                headers=headers,
                json=body,
            )
            response.raise_for_status()
            return response.json()

    async def add_list_item(self, list_id: str, fields: dict) -> dict:
        """Add an item to a SharePoint list."""
        site_id = await self.get_site_id()
        headers = await self._get_headers()

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.GRAPH_BASE}/sites/{site_id}/lists/{list_id}/items",
                headers=headers,
                json={"fields": fields},
            )
            response.raise_for_status()
            return response.json()

    async def get_list_items(self, list_id: str, filter_query: Optional[str] = None) -> list[dict]:
        """Get items from a SharePoint list."""
        site_id = await self.get_site_id()
        headers = await self._get_headers()
        url = f"{self.GRAPH_BASE}/sites/{site_id}/lists/{list_id}/items?expand=fields"
        if filter_query:
            url += f"&$filter={filter_query}"

        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            return response.json().get("value", [])

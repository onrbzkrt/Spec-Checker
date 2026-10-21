"""Thin Microsoft Graph client for SharePoint sites, document libraries and lists.

Authentication uses the OAuth 2.0 client credentials flow (app-only), so the
service can run unattended, for example when Power Automate calls it.
"""
from __future__ import annotations

import time
from typing import Any, Iterator

import msal
import requests

GRAPH = "https://graph.microsoft.com/v1.0"
SCOPES = ["https://graph.microsoft.com/.default"]
RETRY_STATUSES = {429, 503, 504}


class GraphError(RuntimeError):
    """Raised when Graph returns an error response."""

    def __init__(self, method: str, url: str, status: int, body: str):
        super().__init__(f"{method} {url} -> HTTP {status}: {body[:500]}")
        self.status = status


class GraphClient:
    def __init__(self, tenant_id: str, client_id: str, client_secret: str,
                 session: requests.Session | None = None):
        self._app = msal.ConfidentialClientApplication(
            client_id,
            authority=f"https://login.microsoftonline.com/{tenant_id}",
            client_credential=client_secret,
        )
        self._session = session or requests.Session()

    # ------------------------------------------------------------------ core
    def _token(self) -> str:
        # MSAL caches the token in memory and refreshes it when it expires.
        result = self._app.acquire_token_for_client(scopes=SCOPES)
        if "access_token" not in result:
            raise RuntimeError(f"Token request failed: {result.get('error')}: "
                               f"{result.get('error_description')}")
        return result["access_token"]

    def request(self, method: str, path: str, *, json: Any = None,
                params: dict | None = None, raw: bool = False,
                max_retries: int = 4) -> Any:
        url = path if path.startswith("http") else f"{GRAPH}{path}"
        for attempt in range(max_retries + 1):
            resp = self._session.request(
                method, url, json=json, params=params, timeout=60,
                headers={"Authorization": f"Bearer {self._token()}"},
            )
            if resp.status_code in RETRY_STATUSES and attempt < max_retries:
                # Graph throttling: honour Retry-After, otherwise back off exponentially.
                time.sleep(float(resp.headers.get("Retry-After", 2 ** attempt)))
                continue
            if resp.status_code >= 400:
                raise GraphError(method, url, resp.status_code, resp.text)
            if raw:
                return resp.content
            return resp.json() if resp.content else {}
        raise AssertionError("unreachable")

    def get_all(self, path: str, params: dict | None = None) -> Iterator[dict]:
        """Yield every item of a collection, following @odata.nextLink pages."""
        page = self.request("GET", path, params=params)
        while True:
            yield from page.get("value", [])
            next_link = page.get("@odata.nextLink")
            if not next_link:
                return
            page = self.request("GET", next_link)

    # ----------------------------------------------------------- sites
    def get_site(self, host: str, server_relative_path: str) -> dict:
        path = "/" + server_relative_path.strip("/")
        return self.request("GET", f"/sites/{host}:{path}")

    # ------------------------------------------------- document libraries
    def get_drive(self, site_id: str, library_name: str) -> dict:
        for drive in self.get_all(f"/sites/{site_id}/drives"):
            if drive["name"].lower() == library_name.lower():
                return drive
        raise LookupError(f"Document library '{library_name}' not found on site")

    def list_files(self, drive_id: str) -> list[dict]:
        items = self.get_all(f"/drives/{drive_id}/root/children")
        return [item for item in items if "file" in item]

    def download(self, drive_id: str, item_id: str) -> bytes:
        return self.request("GET", f"/drives/{drive_id}/items/{item_id}/content", raw=True)

    # ------------------------------------------------------------ lists
    def find_list(self, site_id: str, display_name: str) -> dict | None:
        for lst in self.get_all(f"/sites/{site_id}/lists"):
            if lst["displayName"].lower() == display_name.lower():
                return lst
        return None

    def create_list(self, site_id: str, display_name: str, columns: list[dict]) -> dict:
        body = {"displayName": display_name, "columns": columns,
                "list": {"template": "genericList"}}
        return self.request("POST", f"/sites/{site_id}/lists", json=body)

    def list_columns(self, site_id: str, list_id: str) -> list[dict]:
        return list(self.get_all(f"/sites/{site_id}/lists/{list_id}/columns"))

    def add_column(self, site_id: str, list_id: str, column: dict) -> dict:
        return self.request("POST", f"/sites/{site_id}/lists/{list_id}/columns", json=column)

    def list_items(self, site_id: str, list_id: str) -> list[dict]:
        return list(self.get_all(f"/sites/{site_id}/lists/{list_id}/items",
                                 params={"expand": "fields"}))

    def create_item(self, site_id: str, list_id: str, fields: dict) -> dict:
        return self.request("POST", f"/sites/{site_id}/lists/{list_id}/items",
                            json={"fields": fields})

    def update_item(self, site_id: str, list_id: str, item_id: str, fields: dict) -> dict:
        return self.request("PATCH", f"/sites/{site_id}/lists/{list_id}/items/{item_id}/fields",
                            json=fields)

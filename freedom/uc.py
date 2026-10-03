"""Minimal Unity Catalog REST client.

Only uses /api/2.1/unity-catalog endpoints that exist in both Unity Catalog OSS
and Databricks Unity Catalog, so the same code can read metadata from either.
"""

from __future__ import annotations

import requests


class UnityCatalog:
    def __init__(self, base_url: str, token: str | None = None, timeout: float = 30):
        self.base = base_url.rstrip("/") + "/api/2.1/unity-catalog"
        self.session = requests.Session()
        if token:
            self.session.headers["Authorization"] = f"Bearer {token}"
        self.timeout = timeout

    def _get(self, path: str, **params):
        r = self.session.get(f"{self.base}/{path}", params=params, timeout=self.timeout)
        r.raise_for_status()
        return r.json()

    def _post(self, path: str, body: dict):
        r = self.session.post(f"{self.base}/{path}", json=body, timeout=self.timeout)
        if r.status_code >= 400:
            raise requests.HTTPError(f"{r.status_code} {r.text[:500]}", response=r)
        return r.json()

    def _delete(self, path: str, **params):
        r = self.session.delete(f"{self.base}/{path}", params=params, timeout=self.timeout)
        if r.status_code not in (200, 204, 404):
            raise requests.HTTPError(f"{r.status_code} {r.text[:500]}", response=r)

    # catalogs
    def catalogs(self) -> list[dict]:
        return self._get("catalogs").get("catalogs", []) or []

    def get_catalog(self, name: str) -> dict | None:
        try:
            return self._get(f"catalogs/{name}")
        except requests.HTTPError as e:
            if e.response is not None and e.response.status_code == 404:
                return None
            raise

    def create_catalog(self, name: str, comment: str | None = None, properties: dict | None = None):
        return self._post("catalogs", {"name": name, "comment": comment, "properties": properties or {}})

    def delete_catalog(self, name: str, force: bool = True):
        self._delete(f"catalogs/{name}", force=str(force).lower())

    # schemas
    def schemas(self, catalog: str) -> list[dict]:
        return self._get("schemas", catalog_name=catalog).get("schemas", []) or []

    def create_schema(self, catalog: str, name: str, comment: str | None = None,
                      properties: dict | None = None):
        return self._post("schemas", {"catalog_name": catalog, "name": name, "comment": comment,
                                      "properties": properties or {}})

    # tables
    def tables(self, catalog: str, schema: str) -> list[dict]:
        out, token = [], None
        while True:
            params = {"catalog_name": catalog, "schema_name": schema, "max_results": 50}
            if token:
                params["page_token"] = token
            page = self._get("tables", **params)
            out.extend(page.get("tables", []) or [])
            token = page.get("next_page_token")
            if not token:
                return out

    def get_table(self, full_name: str) -> dict:
        return self._get(f"tables/{full_name}")

    def create_table(self, body: dict) -> dict:
        return self._post("tables", body)

    def delete_table(self, full_name: str):
        self._delete(f"tables/{full_name}")

    # volumes
    def volumes(self, catalog: str, schema: str) -> list[dict]:
        return self._get("volumes", catalog_name=catalog, schema_name=schema).get("volumes", []) or []

    def create_volume(self, body: dict) -> dict:
        return self._post("volumes", body)

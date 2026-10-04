"""Unity Catalog OSS bootstrap for OpenLakehouse.

On Databricks the `portable_lakehouse` catalog is created once by an administrator (it
needs a managed location or external location decision). On UC OSS it is a
single REST call.
"""

from __future__ import annotations

from portability.uc import UnityCatalog

from . import adapter as ol


def client() -> UnityCatalog:
    return UnityCatalog(ol.UC_URL)


def ensure_catalog(name: str) -> None:
    uc = client()
    if uc.get_catalog(name) is None:
        uc.create_catalog(name, comment="Portable Lakehouse workload catalog")


def table_locations(catalog: str, schema: str, tables: list[str]) -> dict[str, str]:
    """Resolve storage locations through Unity Catalog, the way any engine would."""
    uc = client()
    return {t: uc.get_table(f"{catalog}.{schema}.{t}")["storage_location"] for t in tables}

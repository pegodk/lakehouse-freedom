"""Workload configuration shared by every platform.

The business logic never asks "am I on Databricks?". Instead each platform
adapter (platforms/<name>/entrypoint.py) builds a LakehouseConfig and hands it to
the shared tasks. Everything that legitimately differs between platforms is a
field here, which makes the platform-specific surface explicit and countable.
"""

from __future__ import annotations

from dataclasses import dataclass, field


def scale_tag(scale_factor: float) -> str:
    """sf1, sf10, sf0_1 ... used in schema names and storage paths."""
    if float(scale_factor).is_integer():
        return f"sf{int(scale_factor)}"
    return "sf" + str(scale_factor).replace(".", "_")


@dataclass(frozen=True)
class LakehouseConfig:
    platform: str
    """'databricks' or 'openlakehouse'. Recorded in outputs only, never branched on."""

    scale_factor: float

    raw_root: str
    """Where the generator lands raw Parquet. A UC Volume path on Databricks,
    an s3:// prefix on OpenLakehouse."""

    results_root: str
    """Directory for run artefacts (benchmark JSON, fingerprints). Must be
    writable with plain Python file IO from the driver."""

    table_root: str | None = None
    """Root for external Delta table locations. None means catalog-managed tables.
    The Portable Lakehouse Architecture uses external tables so the data stays readable
    consistently by both reference implementations."""

    catalog: str = "portable_lakehouse"

    engine_info: dict = field(default_factory=dict)
    """Free-form description of the compute (cluster size, serverless, laptop)."""

    @property
    def tag(self) -> str:
        return scale_tag(self.scale_factor)

    # Schema names are identical on every platform.
    @property
    def bronze_schema(self) -> str:
        return f"tpch_{self.tag}_bronze"

    @property
    def silver_schema(self) -> str:
        return f"tpch_{self.tag}"

    @property
    def gold_schema(self) -> str:
        return f"tpch_{self.tag}_gold"

    incremental_schema: str = "incremental"

    def table_name(self, schema: str, table: str) -> str:
        return f"{self.catalog}.{schema}.{table}"

    def table_location(self, schema: str, table: str) -> str | None:
        if self.table_root is None:
            return None
        return f"{self.table_root.rstrip('/')}/{schema}/{table}"

    def raw_path(self, table: str) -> str:
        return f"{self.raw_root.rstrip('/')}/{self.tag}/{table}"

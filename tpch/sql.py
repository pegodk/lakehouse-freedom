"""Access to the 22 TPC-H queries.

tpch/queries/qNN.sql is the canonical text, written as one would for Databricks
SQL / Spark SQL (TPC-H qualification parameters, spec-style date arithmetic).

tpch/queries/adapted/<engine>/qNN.sql holds an engine-specific variant only
where the canonical text does not run, or returns different results, on that
engine. Every adapted file is counted against the engine's SQL portability.
"""

from __future__ import annotations

from importlib import resources

QUERY_IDS = list(range(1, 23))


def _read(path) -> str:
    return path.read_text(encoding="utf-8").strip().rstrip(";")


def canonical(query: int) -> str:
    return _read(resources.files(__package__) / "queries" / f"q{query:02d}.sql")


def adapted(engine: str, query: int) -> str | None:
    path = resources.files(__package__) / "queries" / "adapted" / engine / f"q{query:02d}.sql"
    return _read(path) if path.is_file() else None

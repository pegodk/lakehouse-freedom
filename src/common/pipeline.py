"""The logical pipeline, defined once.

Databricks Workflows (platforms/databricks/resources/portable_lakehouse.job.yml),
Airflow (platforms/openlakehouse/airflow/dags/portable_lakehouse.py) and the
local runner all execute this graph. tests/portability/test_orchestration.py
fails if an orchestrator definition drifts from it.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Task:
    key: str
    depends_on: tuple[str, ...]
    description: str


TASKS: tuple[Task, ...] = (
    Task("generate", (), "Generate TPC-H Raw Parquet with DuckDB dbgen"),
    Task("bronze", ("generate",), "Raw Parquet -> Bronze Delta with lineage columns"),
    Task("silver", ("bronze",), "Bronze -> Silver, conformed TPC-H schema"),
    Task("gold", ("silver",), "Silver -> Gold revenue aggregate (DataFrame API)"),
    Task("quality", ("gold",), "Row counts, keys, FK integrity, fingerprints"),
    Task("incremental", (), "Synthetic change feed -> SCD2 dimension via MERGE"),
    Task("tpch_queries", ("quality",), "Run the 22 TPC-H queries and record results"),
)


def task(key: str) -> Task:
    return next(t for t in TASKS if t.key == key)


def topological_order() -> list[str]:
    done: list[str] = []
    pending = list(TASKS)
    while pending:
        ready = [t for t in pending if all(d in done for d in t.depends_on)]
        if not ready:
            raise ValueError("cycle in pipeline graph")
        for t in ready:
            done.append(t.key)
            pending.remove(t)
    return done

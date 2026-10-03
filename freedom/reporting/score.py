"""Freedom Score: every component is a ratio of measured counts.

Component                     Formula                                                  Source
----------------------------  -------------------------------------------------------  ---------------------------------
Data portability              Delta tables read by OSS Spark AND DuckDB with equal      reports/freedom-day-<sf>.json
                              row counts after re-registration from storage / tables
TPC-H SQL portability (Spark) queries PORTABLE on OpenLakehouse Spark / 22              benchmarks/results/.../spark
TPC-H SQL portability (DuckDB) queries PORTABLE on DuckDB / 22                          benchmarks/results/.../duckdb
Transformation portability    shared transformation LOC /                              freedom/assessment/inventory.yaml
                              (shared + OpenLakehouse-specific transformation LOC)
Catalog portability           Unity Catalog capabilities recreated in UC OSS /          reports/catalog-probe.json
                              capabilities used by the workload
Orchestration portability     shared orchestration LOC /                               freedom/assessment/inventory.yaml
                              (shared + OpenLakehouse-specific orchestration LOC)

Freedom Score = unweighted mean of the measured components, excluding the
DuckDB SQL component (DuckDB is an additional engine, not the migration
target). Components that could not be measured are left out of the mean and
listed as such; they are never counted as zero or as 100%.
"""

from __future__ import annotations

import json
from pathlib import Path

from freedom.assessment.inventory import measure
from freedom.validation import compare
from lakehouse_freedom.common.config import scale_tag

REPO = Path(__file__).resolve().parents[2]


def _load(path: Path):
    return json.loads(path.read_text()) if path.exists() else None


def components(scale_factor: float) -> list[dict]:
    tag = scale_tag(scale_factor)
    inv = measure()
    out = []

    day = _load(REPO / "reports" / f"freedom-day-{tag}.json")
    dp = day["data_portability"] if day else None
    out.append({"key": "data", "name": "Data portability",
                "value": dp["portable_tables"] / dp["total_tables"] if dp else None,
                "numerator": dp and dp["portable_tables"], "denominator": dp and dp["total_tables"],
                "formula": "Delta tables read by OSS Spark and DuckDB after re-registration / Delta tables",
                "in_score": True})

    prefer = [("databricks", "spark"), ("openlakehouse", "spark")]
    for engine, label, in_score in (("spark", "TPC-H SQL portability (Spark)", True),
                                    ("duckdb", "TPC-H SQL portability (DuckDB)", False)):
        classes = compare.classify("openlakehouse", engine, scale_factor, prefer)
        counts = compare.summarize(classes) if classes else None
        out.append({"key": f"sql_{engine}", "name": label,
                    "value": counts["PORTABLE"] / counts["total"] if counts else None,
                    "numerator": counts and counts["PORTABLE"], "denominator": counts and counts["total"],
                    "formula": f"TPC-H queries running unchanged with correct results on {engine} / 22",
                    "in_score": in_score})

    t = inv["transformation"]["openlakehouse"]
    out.append({"key": "transformation", "name": "Transformation portability", "value": t["score"],
                "numerator": t["shared_loc"], "denominator": t["shared_loc"] + t["platform_loc"],
                "formula": "shared transformation LOC / (shared + OpenLakehouse-specific transformation LOC)",
                "in_score": True})

    probe = _load(REPO / "reports" / "catalog-probe.json")
    out.append({"key": "catalog", "name": "Catalog portability",
                "value": probe["score"] if probe else None,
                "numerator": probe and probe["recreated"], "denominator": probe and probe["total"],
                "formula": "Unity Catalog capabilities recreated in UC OSS / capabilities used",
                "in_score": True})

    o = inv["orchestration"]["openlakehouse"]
    out.append({"key": "orchestration", "name": "Orchestration portability", "value": o["score"],
                "numerator": o["shared_loc"], "denominator": o["shared_loc"] + o["platform_loc"],
                "formula": "shared orchestration LOC / (shared + OpenLakehouse-specific orchestration LOC)",
                "in_score": True})
    return out


def freedom_score(comps: list[dict]) -> float | None:
    measured = [c["value"] for c in comps if c["in_score"] and c["value"] is not None]
    return sum(measured) / len(measured) if measured else None


def bar(value: float | None, width: int = 20) -> str:
    if value is None:
        return "·" * width + "  not measured"
    filled = round(value * width)
    return "█" * filled + "░" * (width - filled) + f" {value * 100:4.0f}%"

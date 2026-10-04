"""Portability Benchmark runner: executes the 22 TPC-H queries on one engine.

The same runner is used on Databricks (inside a job) and locally against
OpenLakehouse (Spark Connect) and DuckDB. One JSON file per query is written to
<out_dir>/qNN.json together with run.json describing the environment.

Each query is first attempted with the canonical SQL text. If an adapted
variant exists for the engine (tpch/queries/adapted/<engine>/), it is run as
well and becomes the reported result; the canonical attempt is kept so the
portability classification can see whether the original text ran and what it
returned.
"""

from __future__ import annotations

import datetime as dt
import decimal
import json
import os
import statistics
import time
from typing import Protocol

from portable_lakehouse.tpch import sql as tpch_sql

MAX_STORED_ROWS = 50_000


class Engine(Protocol):
    platform: str
    name: str

    def prepare(self) -> None: ...
    def execute(self, query: str) -> tuple[list[str], list[tuple]]: ...
    def info(self) -> dict: ...


def to_json_value(value):
    if value is None or isinstance(value, (bool, int, str)):
        return value
    if isinstance(value, float):
        return value
    if isinstance(value, decimal.Decimal):
        return str(value)
    if isinstance(value, (dt.date, dt.datetime)):
        return value.isoformat()
    return str(value)


def _attempt(engine: Engine, text: str, repeats: int) -> dict:
    durations, columns, rows, error = [], [], [], None
    for _ in range(repeats):
        start = time.perf_counter()
        try:
            columns, rows = engine.execute(text)
        except Exception as exc:  # the failure itself is the measurement
            error = f"{type(exc).__name__}: {str(exc).splitlines()[0][:500]}"
            durations.append(time.perf_counter() - start)
            break
        durations.append(time.perf_counter() - start)
    success = error is None
    return {
        "success": success,
        "error": error,
        "duration_s": round(statistics.median(durations), 4) if success else None,
        "durations_s": [round(d, 4) for d in durations],
        "row_count": len(rows) if success else None,
        "columns": list(columns) if success else None,
        "rows": [[to_json_value(v) for v in r] for r in rows[:MAX_STORED_ROWS]] if success else None,
    }


def run_benchmark(
    engine: Engine,
    scale_factor: float,
    out_dir: str,
    queries: list[int] | None = None,
    repeats: int = 1,
) -> dict:
    os.makedirs(out_dir, exist_ok=True)
    engine.prepare()
    info = engine.info()
    summary = {"platform": engine.platform, "engine": engine.name, "scale_factor": scale_factor,
               "repeats": repeats, "environment": info, "queries": {}}
    for q in queries or tpch_sql.QUERY_IDS:
        canonical = _attempt(engine, tpch_sql.canonical(q), repeats)
        adapted_text = tpch_sql.adapted(engine.name, q)
        adapted = _attempt(engine, adapted_text, repeats) if adapted_text else None
        final = adapted if adapted else canonical
        record = {
            "platform": engine.platform,
            "engine": engine.name,
            "engine_version": info.get("engine_version"),
            "query": f"q{q:02d}",
            "scale_factor": scale_factor,
            "variant": "adapted" if adapted else "canonical",
            "success": final["success"],
            "duration_s": final["duration_s"],
            "durations_s": final["durations_s"],
            "row_count": final["row_count"],
            "error": final["error"],
            "timestamp": dt.datetime.now(dt.timezone.utc).isoformat(),
            "environment": info,
            "columns": final["columns"],
            "rows": final["rows"],
            "canonical": None if final is canonical else canonical,
        }
        with open(os.path.join(out_dir, f"q{q:02d}.json"), "w") as fh:
            json.dump(record, fh, indent=1)
        summary["queries"][f"q{q:02d}"] = {
            k: record[k] for k in ("variant", "success", "duration_s", "row_count", "error")
        }
    with open(os.path.join(out_dir, "run.json"), "w") as fh:
        json.dump(summary, fh, indent=1)
    return summary

"""Shared task dispatcher.

`run_task(spark, cfg, key)` executes one node of the pipeline graph. Platform
entry points (platforms/*/entrypoint.py) only build the SparkSession and the
FreedomConfig, then call this.
"""

from __future__ import annotations

import json
import os
import uuid
from collections.abc import Callable

from pyspark.sql import SparkSession

from lakehouse_freedom.common.config import FreedomConfig
from lakehouse_freedom.common.pipeline import TASKS, topological_order


def results_dir(cfg: FreedomConfig, *parts: str) -> str:
    path = os.path.join(cfg.results_root, cfg.platform, cfg.tag, *parts)
    os.makedirs(path, exist_ok=True)
    return path


def write_json(path: str, payload) -> None:
    with open(path, "w") as fh:
        json.dump(payload, fh, indent=1, default=str)


def run_task(
    spark: SparkSession | None,
    cfg: FreedomConfig,
    key: str,
    duckdb_setup: Callable | None = None,
    repeats: int = 1,
) -> dict:
    if key == "generate":
        from lakehouse_freedom.tpch.generator.dbgen import generate

        manifest = generate(cfg.scale_factor, cfg.raw_root, duckdb_setup=duckdb_setup)
        write_json(os.path.join(results_dir(cfg), "generator.json"), manifest)
        return manifest

    if key == "bronze":
        from lakehouse_freedom.ingestion.bronze import build_bronze

        return build_bronze(spark, cfg, batch_id=uuid.uuid4().hex[:12])

    if key == "silver":
        from lakehouse_freedom.transformations.silver import build_silver

        return build_silver(spark, cfg)

    if key == "gold":
        from lakehouse_freedom.quality.checks import fingerprint
        from lakehouse_freedom.transformations.gold import build_gold

        build_gold(spark, cfg)
        fp = fingerprint(spark.table(cfg.table_name(cfg.gold_schema, "revenue_by_nation_year")))
        write_json(os.path.join(results_dir(cfg), "gold.json"), fp)
        return fp

    if key == "quality":
        from lakehouse_freedom.quality.checks import run_quality

        result = run_quality(spark, cfg)
        write_json(os.path.join(results_dir(cfg), "quality.json"), result)
        return result

    if key == "incremental":
        from lakehouse_freedom.ingestion.incremental import BATCHES, ingest_batch
        from lakehouse_freedom.transformations.scd2 import apply_batch, snapshot

        applied = []
        for batch_id, _, _ in BATCHES:
            if ingest_batch(spark, cfg, batch_id):
                apply_batch(spark, cfg, batch_id)
                applied.append(batch_id)
        before_replay = snapshot(spark, cfg)
        # Replaying the latest batch must not change the dimension, and
        # re-ingesting a loaded batch must be refused by the bronze log.
        apply_batch(spark, cfg, BATCHES[-1][0])
        reingested = ingest_batch(spark, cfg, BATCHES[-1][0])
        result = {
            "applied_batches": applied,
            "rows": before_replay,
            "replay_idempotent": snapshot(spark, cfg) == before_replay,
            "reingest_refused": not reingested,
        }
        # SCD2 output does not depend on the TPC-H scale factor.
        path = os.path.join(cfg.results_root, cfg.platform, "incremental")
        os.makedirs(path, exist_ok=True)
        write_json(os.path.join(path, "scd2.json"), result)
        return result

    if key == "tpch_queries":
        from lakehouse_freedom.benchmarks.engines import SparkSqlEngine
        from lakehouse_freedom.benchmarks.runner import run_benchmark

        engine = SparkSqlEngine(spark, cfg.catalog, cfg.silver_schema, cfg.platform, cfg.engine_info)
        return run_benchmark(
            engine, cfg.scale_factor, results_dir(cfg, "spark"), repeats=repeats
        )

    raise KeyError(f"unknown task {key!r}; known: {[t.key for t in TASKS]}")


def run_all(spark, cfg: FreedomConfig, duckdb_setup=None, skip: tuple[str, ...] = ()) -> dict:
    out = {}
    for key in topological_order():
        if key in skip:
            continue
        print(f"[freedom] {cfg.platform} {cfg.tag}: {key}", flush=True)
        out[key] = run_task(spark, cfg, key, duckdb_setup=duckdb_setup)
    return out

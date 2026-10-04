"""Portability Benchmark orchestration for the OpenLakehouse side.

Databricks runs the same runner inside its job (task `tpch_queries`); its
results are fetched with `make databricks-fetch-results`.
"""

from __future__ import annotations

import os

from portable_lakehouse.benchmarks.engines import DataFusionEngine, DuckDbEngine
from portable_lakehouse.benchmarks.runner import run_benchmark
from portable_lakehouse.common.tpch_schema import TABLES
from portable_lakehouse.run import run_task
from portable_lakehouse_platforms.openlakehouse import adapter as ol
from portable_lakehouse_platforms.openlakehouse.catalog import table_locations


def duckdb_engine(scale_factor: float) -> DuckDbEngine:
    cfg = ol.config(scale_factor)
    # Table locations come from Unity Catalog OSS; the bytes are read straight
    # from object storage by DuckDB's delta extension (delta-kernel-rs).
    locations = table_locations(cfg.catalog, cfg.silver_schema, TABLES)
    env = {
        "platform_label": "OpenLakehouse (local Docker) + DuckDB in-process on the host",
        "compute": "DuckDB in-process, all host cores",
        "table_resolution": "Unity Catalog OSS REST -> delta_scan(storage_location)",
        **ol.host_resources(),
    }
    return DuckDbEngine(locations, "openlakehouse", env, setup=ol.duckdb_s3_setup)


def datafusion_engine(scale_factor: float) -> DataFusionEngine:
    cfg = ol.config(scale_factor)
    locations = table_locations(cfg.catalog, cfg.silver_schema, TABLES)
    env = {
        "platform_label": "OpenLakehouse (local Docker) + DataFusion in-process on the host",
        "compute": "Apache DataFusion in-process, all host cores",
        "table_resolution": "Unity Catalog OSS REST -> Delta Lake -> Arrow dataset",
        **ol.host_resources(),
    }
    return DataFusionEngine(locations, "openlakehouse", env, storage_options=ol.delta_rs_s3_options())


def run(
    scale_factor: float,
    repeats: int = 3,
    engines: tuple[str, ...] = ("spark", "duckdb", "datafusion"),
) -> dict:
    cfg = ol.config(scale_factor)
    out = {}
    if "spark" in engines:
        out["spark"] = run_task(ol.spark_session(), cfg, "tpch_queries", repeats=repeats)
    if "duckdb" in engines:
        out_dir = os.path.join(cfg.results_root, cfg.platform, cfg.tag, "duckdb")
        out["duckdb"] = run_benchmark(duckdb_engine(scale_factor), scale_factor, out_dir,
                                      repeats=repeats)
    if "datafusion" in engines:
        out_dir = os.path.join(cfg.results_root, cfg.platform, cfg.tag, "datafusion")
        out["datafusion"] = run_benchmark(
            datafusion_engine(scale_factor), scale_factor, out_dir, repeats=repeats
        )
    return out

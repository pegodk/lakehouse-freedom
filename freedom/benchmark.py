"""Freedom Benchmark orchestration for the OpenLakehouse side.

Databricks runs the same runner inside its job (task `tpch_queries`); its
results are fetched with `make databricks-fetch-results`.
"""

from __future__ import annotations

import os

from freedom_platforms.openlakehouse import adapter as ol
from freedom_platforms.openlakehouse.catalog import table_locations
from lakehouse_freedom.benchmarks.engines import DuckDbEngine
from lakehouse_freedom.benchmarks.runner import run_benchmark
from lakehouse_freedom.common.tpch_schema import TABLES
from lakehouse_freedom.run import run_task


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


def run(scale_factor: float, repeats: int = 3, engines: tuple[str, ...] = ("spark", "duckdb")) -> dict:
    cfg = ol.config(scale_factor)
    out = {}
    if "spark" in engines:
        out["spark"] = run_task(ol.spark_session(), cfg, "tpch_queries", repeats=repeats)
    if "duckdb" in engines:
        out_dir = os.path.join(cfg.results_root, cfg.platform, cfg.tag, "duckdb")
        out["duckdb"] = run_benchmark(duckdb_engine(scale_factor), scale_factor, out_dir,
                                      repeats=repeats)
    return out

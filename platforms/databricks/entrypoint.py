"""Databricks entry point for one pipeline task (spark_python_task).

The Databricks counterpart of platforms/openlakehouse/entrypoint.py. It builds
the SparkSession and the LakehouseConfig, then hands over to the shared code in
the portable_lakehouse wheel. Nothing else is Databricks-specific.
"""

from __future__ import annotations

import argparse
import os

from pyspark.sql import SparkSession

from portable_lakehouse.common.config import LakehouseConfig
from portable_lakehouse.run import run_task


def environment(spark: SparkSession) -> dict:
    info = {
        "platform_label": "Databricks",
        "compute": os.environ.get("PORTABLE_LAKEHOUSE_COMPUTE_LABEL", "serverless jobs compute"),
        "databricks_runtime": os.environ.get("DATABRICKS_RUNTIME_VERSION"),
    }
    # Cluster tags exist on classic compute only; serverless refuses to read them.
    for key in ("spark.databricks.clusterUsageTags.sparkVersion",
                "spark.databricks.clusterUsageTags.clusterNodeType",
                "spark.databricks.clusterUsageTags.clusterWorkers"):
        try:
            info[key.rsplit(".", 1)[-1]] = spark.conf.get(key)
        except Exception:
            pass
    return info


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("task")
    parser.add_argument("--scale", type=float, required=True)
    parser.add_argument("--catalog", default="portable_lakehouse")
    parser.add_argument("--table-root", default="")
    parser.add_argument("--volume-root", required=True)
    parser.add_argument("--repeats", type=int, default=1)
    args = parser.parse_args(argv)

    spark = SparkSession.builder.getOrCreate()
    cfg = LakehouseConfig(
        platform="databricks",
        scale_factor=args.scale,
        raw_root=f"{args.volume_root}/raw",
        results_root=f"{args.volume_root}/results",
        table_root=args.table_root or None,
        catalog=args.catalog,
        engine_info=environment(spark),
    )
    run_task(spark, cfg, args.task, repeats=args.repeats if args.task == "tpch_queries" else 1)


if __name__ == "__main__":
    main()

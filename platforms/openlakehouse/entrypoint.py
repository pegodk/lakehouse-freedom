"""Run pipeline tasks on OpenLakehouse via Spark Connect.

    python -m portable_lakehouse_platforms.openlakehouse.entrypoint all --scale 1
    python -m portable_lakehouse_platforms.openlakehouse.entrypoint silver --scale 10

This is the OpenLakehouse counterpart of platforms/databricks/entrypoint.py.
Both only build a session and a config; the work happens in portable_lakehouse.
"""

from __future__ import annotations

import argparse

from portable_lakehouse.common.pipeline import TASKS
from portable_lakehouse.run import run_all, run_task

from . import adapter as ol
from .catalog import ensure_catalog


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("task", choices=["all"] + [t.key for t in TASKS])
    parser.add_argument("--scale", type=float, default=1)
    parser.add_argument("--repeats", type=int, default=1)
    parser.add_argument("--skip", nargs="*", default=[])
    args = parser.parse_args(argv)

    cfg = ol.config(args.scale)
    ensure_catalog(cfg.catalog)
    spark = None if args.task == "generate" else ol.spark_session()
    if args.task == "all":
        run_all(spark, cfg, duckdb_setup=ol.duckdb_s3_setup, skip=tuple(args.skip))
    else:
        result = run_task(spark, cfg, args.task, duckdb_setup=ol.duckdb_s3_setup,
                          repeats=args.repeats)
        print(result if not isinstance(result, dict) or len(str(result)) < 2000 else "done")


if __name__ == "__main__":
    main()

"""Portable Lakehouse command line.

    portable-lakehouse generate  --scale 1    TPC-H Raw Parquet into OpenLakehouse storage
    portable-lakehouse pipeline  --scale 1    run the whole pipeline on OpenLakehouse
    portable-lakehouse benchmark --scale 1    TPC-H on Spark, DuckDB and DataFusion
    portable-lakehouse check     --scale 1    Portability Check (exit code 1 on any FAIL)
    portable-lakehouse report    --scale 1    reports/portability-report.md
    portable-lakehouse assess    PATH         assess a repository for platform dependencies
    portable-lakehouse mlflow                  verify portable MLflow tracking
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def _scale(p: argparse.ArgumentParser) -> None:
    p.add_argument("--scale", type=float, default=1, help="TPC-H scale factor (default 1)")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="portable-lakehouse", description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="cmd", required=True)
    _scale(sub.add_parser("generate"))
    p = sub.add_parser("pipeline")
    _scale(p)
    p.add_argument("--task", default="all")
    p = sub.add_parser("benchmark")
    _scale(p)
    p.add_argument("--repeats", type=int, default=3)
    p.add_argument(
        "--engines",
        nargs="*",
        choices=("spark", "duckdb", "datafusion"),
        default=["spark", "duckdb", "datafusion"],
    )
    p = sub.add_parser("check")
    _scale(p)
    p.add_argument("--no-probe", action="store_true", help="skip the live catalog probe")
    _scale(sub.add_parser("report"))
    p = sub.add_parser("assess")
    p.add_argument("path", type=Path)
    p.add_argument("--json", action="store_true")
    p = sub.add_parser("mlflow")
    p.add_argument("--tracking-uri", default="sqlite:///mlflow.db")
    p.add_argument("--experiment", default="portable-lakehouse")
    p.add_argument("--output", type=Path, default=Path("reports/mlflow-tracking.json"))
    args = parser.parse_args(argv)

    if args.cmd in ("generate", "pipeline"):
        from portable_lakehouse_platforms.openlakehouse.entrypoint import main as run

        run(["generate" if args.cmd == "generate" else args.task, "--scale", str(args.scale)])
        return 0

    if args.cmd == "benchmark":
        from portability import benchmark
        from portability.validation.compare import results_exist

        if not results_exist("openlakehouse", args.scale, "quality.json"):
            print(f"No pipeline output for SF{args.scale:g}. Run: make pipeline SCALE={args.scale:g}")
            return 1
        out = benchmark.run(args.scale, repeats=args.repeats, engines=tuple(args.engines))
        for engine, run in out.items():
            ok = sum(q["success"] for q in run["queries"].values())
            total = sum(q["duration_s"] or 0 for q in run["queries"].values())
            print(f"{engine:7} {ok}/22 queries succeeded, {total:.1f} s total (median of {args.repeats})")
        return 0

    if args.cmd == "check":
        from portability.validation.check import FAIL, run

        print(f"PORTABILITY CHECK (SF{args.scale:g})")
        checks = run(args.scale, probe_catalog=not args.no_probe)
        failed = [c for c in checks if c.status == FAIL]
        print(f"{len(checks) - len(failed)}/{len(checks)} checks did not fail"
              + (f"; FAILED: {[c.key for c in failed]}" if failed else ""))
        return 1 if failed else 0

    if args.cmd == "report":
        from portability.reporting.report import write

        print(f"wrote {write(args.scale)}")
        return 0

    if args.cmd == "mlflow":
        from portable_lakehouse.ml.tracking import run_tracking_workload

        evidence = run_tracking_workload(args.tracking_uri, args.experiment, args.output)
        print(f"MLflow run {evidence['run_id']} finished; wrote {args.output}")
        return 0

    if args.cmd == "assess":
        from portability.assessment.scanner import scan

        hits = scan([args.path], args.path if args.path.is_dir() else None)
        if args.json:
            print(json.dumps(hits, indent=1))
            return 0
        by_class: dict[str, int] = {}
        for h in hits:
            by_class[h["classification"]] = by_class.get(h["classification"], 0) + 1
            print(f"{h['classification']:17} {h['file']}:{h['line']}  {h['capability']}")
            print(f"{'':17} -> {h['alternative']}")
        print(f"\n{len(hits)} findings: " + ", ".join(f"{k} {v}" for k, v in sorted(by_class.items()))
              if hits else "No Databricks-specific constructs found.")
        return 0
    return 2


if __name__ == "__main__":
    sys.exit(main())

"""Freedom Day: the managed platform is gone; the data is not.

The scenario starts from nothing but Delta tables in object storage:

  1. Inventory every object under the table root (key, size, ETag).
  2. Create an EMPTY Unity Catalog OSS catalog `freedom_day`. The original
     catalog is never consulted, as if Databricks Unity Catalog had vanished.
  3. Discover Delta tables by their _delta_log folders and register each one
     in UC OSS from what the Delta log says (schema, location). No data is
     copied, converted or regenerated.
  4. Query the registered tables with Spark (TPC-H 1-22) and DuckDB.
  5. Inventory the storage again and prove that not one object changed.

`--source` points at any S3-compatible prefix that holds the tables, e.g. a
byte-for-byte sync of a Databricks external location (see docs/freedom-path.md).
By default it uses the tables produced by the OpenLakehouse pipeline, which is
a rehearsal: the mechanics are identical, but the writer was not Databricks.
The report states which case it was, using the writer recorded in each table's
Delta history.
"""

from __future__ import annotations

import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

from freedom.validation.compare import classify, summarize
from freedom_platforms.openlakehouse import adapter as ol
from freedom_platforms.openlakehouse.catalog import client
from lakehouse_freedom.benchmarks.engines import DuckDbEngine, SparkSqlEngine
from lakehouse_freedom.benchmarks.runner import run_benchmark
from lakehouse_freedom.common.config import scale_tag
from lakehouse_freedom.common.tpch_schema import TABLES

CATALOG = "freedom_day"
REPO = Path(__file__).resolve().parents[1]
UC_TYPE_NAMES = {
    "boolean": "BOOLEAN", "byte": "BYTE", "short": "SHORT", "integer": "INT", "long": "LONG",
    "float": "FLOAT", "double": "DOUBLE", "date": "DATE", "timestamp": "TIMESTAMP",
    "timestamp_ntz": "TIMESTAMP_NTZ", "string": "STRING", "binary": "BINARY",
}


def _split(uri: str) -> tuple[str, str]:
    u = urlparse(uri)
    return u.netloc, u.path.lstrip("/").rstrip("/")


def inventory(root: str) -> dict[str, tuple[int, str]]:
    bucket, prefix = _split(root)
    s3 = ol.boto3_client()
    out = {}
    for page in s3.get_paginator("list_objects_v2").paginate(Bucket=bucket, Prefix=prefix + "/"):
        for obj in page.get("Contents", []):
            out[obj["Key"]] = (obj["Size"], obj["ETag"])
    return out


def discover_tables(objects: dict, root: str) -> dict[str, list[str]]:
    """schema -> [table] for every <root>/<schema>/<table>/_delta_log/ found."""
    _, prefix = _split(root)
    found: dict[str, set[str]] = {}
    for key in objects:
        rel = key[len(prefix) + 1:].split("/")
        if len(rel) >= 4 and rel[2] == "_delta_log":
            found.setdefault(rel[0], set()).add(rel[1])
    return {s: sorted(t) for s, t in sorted(found.items())}


def uc_column(field: dict, position: int) -> dict:
    t = field["type"]
    if isinstance(t, str) and t.startswith("decimal"):
        name, text = "DECIMAL", t
    elif isinstance(t, str):
        name, text = UC_TYPE_NAMES.get(t, "STRING"), t
    else:
        name, text = t["type"].upper(), t["type"]
    col = {
        "name": field["name"], "type_name": name, "type_text": text,
        "type_json": json.dumps(field), "position": position, "nullable": field.get("nullable", True),
    }
    if t.startswith("decimal") if isinstance(t, str) else False:
        p, s = t[len("decimal("):-1].split(",")
        col.update(type_precision=int(p), type_scale=int(s))
    comment = (field.get("metadata") or {}).get("comment")
    if comment:
        col["comment"] = comment
    return col


def run(scale_factor: float, source_root: str | None = None) -> dict:
    started = time.time()
    source_root = (source_root or ol.TABLE_ROOT).rstrip("/")
    tag = scale_tag(scale_factor)
    silver = f"tpch_{tag}"
    report: dict = {"scale_factor": scale_factor, "source_root": source_root,
                    "started_at": datetime.now(timezone.utc).isoformat(), "steps": []}

    def step(name: str, ok: bool, detail: str):
        report["steps"].append({"step": name, "ok": ok, "detail": detail})
        print(f"  {'ok ' if ok else 'FAIL'} {name}: {detail}", flush=True)

    before = inventory(source_root)
    layout = {s: t for s, t in discover_tables(before, source_root).items()
              if s in (f"tpch_{tag}_bronze", silver, f"tpch_{tag}_gold", "incremental")}
    if silver not in layout:
        raise SystemExit(f"No Delta tables for {silver} under {source_root}. Run the pipeline first.")
    n_tables = sum(len(t) for t in layout.values())
    data_bytes = sum(size for size, _ in before.values())
    step("inventory", True, f"{len(before)} objects, {data_bytes / 1e9:.2f} GB, {n_tables} Delta tables")

    uc = client()
    if uc.get_catalog(CATALOG):
        uc.delete_catalog(CATALOG, force=True)
    uc.create_catalog(CATALOG, comment="Freedom Day: rebuilt from storage only")
    step("empty catalog", True, f"created UC OSS catalog '{CATALOG}' with no prior metadata")

    spark = ol.spark_session()
    tables = []
    for schema, names in layout.items():
        uc.create_schema(CATALOG, schema, comment="Re-registered from storage on Freedom Day")
        for name in names:
            path = f"{source_root}/{schema}/{name}"
            detail = spark.sql(f"DESCRIBE DETAIL delta.`{path}`").collect()[0].asDict()
            history = spark.sql(f"DESCRIBE HISTORY delta.`{path}`").select(
                "version", "operation", "engineInfo").orderBy("version").collect()
            fields = json.loads(spark.read.format("delta").load(path).schema.json())["fields"]
            uc.create_table({
                "name": name, "catalog_name": CATALOG, "schema_name": schema,
                "table_type": "EXTERNAL", "data_source_format": "DELTA",
                "storage_location": path,
                "columns": [uc_column(f, i) for i, f in enumerate(fields)],
                "comment": "Registered from its Delta log on Freedom Day",
            })
            tables.append({
                "table": f"{schema}.{name}",
                "location": path,
                "min_reader_version": detail.get("minReaderVersion"),
                "min_writer_version": detail.get("minWriterVersion"),
                "table_features": sorted(detail.get("tableFeatures") or []),
                "files": detail.get("numFiles"),
                "size_bytes": detail.get("sizeInBytes"),
                "versions": len(history),
                "writers": sorted({h["engineInfo"] for h in history if h["engineInfo"]}),
            })
    report["tables"] = tables
    writers = sorted({w for t in tables for w in t["writers"]})
    report["writers"] = writers
    report["rehearsal"] = not any("databricks" in w.lower() for w in writers)
    step("register", True, f"{len(tables)} tables registered from _delta_log, "
                           f"written by: {', '.join(writers)}")

    # Every table, not only the TPC-H ones, must be readable by both engines.
    import duckdb

    con = duckdb.connect()
    con.execute("INSTALL delta; LOAD delta;")
    ol.duckdb_s3_setup(con)
    for t in tables:
        schema, name = t["table"].split(".")
        try:
            t["spark_rows"] = spark.table(f"{CATALOG}.{schema}.{name}").count()
        except Exception as e:
            t["spark_rows"], t["spark_error"] = None, str(e).splitlines()[0][:300]
        try:
            loc = uc.get_table(f"{CATALOG}.{schema}.{name}")["storage_location"]
            t["duckdb_rows"] = con.execute(f"SELECT count(*) FROM delta_scan('{loc}')").fetchone()[0]
        except Exception as e:
            t["duckdb_rows"], t["duckdb_error"] = None, str(e).splitlines()[0][:300]
        t["portable"] = t["spark_rows"] is not None and t["spark_rows"] == t["duckdb_rows"]
    portable = sum(t["portable"] for t in tables)
    report["data_portability"] = {"portable_tables": portable, "total_tables": len(tables)}
    step("read every table", portable == len(tables),
         f"{portable}/{len(tables)} tables read by Spark and DuckDB with identical row counts")

    out_root = os.path.join(ol.RESULTS_ROOT, "freedom_day", tag)
    env = {"platform_label": "Freedom Day: OpenLakehouse, catalog rebuilt from storage",
           "source_root": source_root, **ol.discover_versions(), **ol.host_resources()}
    spark_engine = SparkSqlEngine(spark, CATALOG, silver, "freedom_day", env)
    spark_run = run_benchmark(spark_engine, scale_factor, os.path.join(out_root, "spark"))
    ok = all(q["success"] for q in spark_run["queries"].values())
    step("spark", ok, f"{sum(q['success'] for q in spark_run['queries'].values())}/22 TPC-H "
                      f"queries ran on Spark against {CATALOG}.{silver}")

    locations = {t: client().get_table(f"{CATALOG}.{silver}.{t}")["storage_location"] for t in TABLES}
    duck = DuckDbEngine(locations, "freedom_day", env, setup=ol.duckdb_s3_setup)
    duck_run = run_benchmark(duck, scale_factor, os.path.join(out_root, "duckdb"))
    ok = all(q["success"] for q in duck_run["queries"].values())
    step("duckdb", ok, f"{sum(q['success'] for q in duck_run['queries'].values())}/22 TPC-H "
                       f"queries ran on DuckDB via UC OSS-resolved locations")

    prefer = [("databricks", "spark"), ("openlakehouse", "spark")]
    for engine in ("spark", "duckdb"):
        classes = classify("freedom_day", engine, scale_factor, prefer)
        counts = summarize(classes)
        report[f"{engine}_classification"] = counts
        step(f"{engine} results", counts["PORTABLE"] == 22,
             f"{counts['PORTABLE']}/22 results identical to the reference "
             f"({next(iter(classes.values()))['reference']})")

    after = inventory(source_root)
    changed = [k for k in before if after.get(k) != before[k]]
    added = [k for k in after if k not in before]
    report["data_unchanged"] = not changed and not added
    step("data untouched", report["data_unchanged"],
         f"{len(before)} objects before, {len(after)} after, {len(changed)} changed, {len(added)} added")

    report["duration_s"] = round(time.time() - started, 1)
    report["passed"] = all(s["ok"] for s in report["steps"])
    path = REPO / "reports" / f"freedom-day-{tag}.json"
    path.parent.mkdir(exist_ok=True)
    path.write_text(json.dumps(report, indent=1, default=str))
    return report

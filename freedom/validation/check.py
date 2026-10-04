"""Freedom Check: does the workload still work without Databricks?

Every check is PASS, FAIL or SKIP with the evidence behind it. Nothing is
patched up on the fly: a failing check is reported as failing.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path

import duckdb
import yaml

from freedom.validation import compare
from freedom_platforms.openlakehouse import adapter as ol
from freedom_platforms.openlakehouse.catalog import client
from lakehouse_freedom.common.config import scale_tag
from lakehouse_freedom.common.pipeline import TASKS
from lakehouse_freedom.common.tpch_schema import TABLES, TPCH_SCHEMA, expected_row_count

REPO = Path(__file__).resolve().parents[2]
PASS, FAIL, SKIP = "PASS", "FAIL", "SKIP"


@dataclass
class Check:
    key: str
    title: str
    status: str
    detail: str


def _load(path: Path):
    return json.loads(path.read_text()) if path.exists() else None


def _results(platform: str, sf: float, *parts: str) -> Path:
    return compare.RESULTS.joinpath(platform, scale_tag(sf), *parts)


def _duck():
    con = duckdb.connect()
    con.execute("INSTALL delta; LOAD delta;")
    ol.duckdb_s3_setup(con)
    return con


def _profile_sql(source: str, table: str, conform: bool) -> str:
    """Column profile: count, plus per column sum/length-sum/day-sum. DuckDB SQL."""
    parts = ["count(*)"]
    for col, sql_type in TPCH_SCHEMA[table]:
        expr = f"trim(CAST({col} AS VARCHAR))" if (conform and sql_type == "STRING") else col
        if sql_type == "STRING":
            parts.append(f"sum(length({expr}))")
        elif sql_type == "DATE":
            parts.append(f"sum(epoch({expr}) // 86400)")
        else:
            parts.append(f"sum(CAST({expr} AS DECIMAL(38,2)))")
    return f"SELECT {', '.join(parts)} FROM {source}"


def run(scale_factor: float, probe_catalog: bool = True) -> list[Check]:
    sf, tag = scale_factor, scale_tag(scale_factor)
    checks: list[Check] = []

    def add(key, title, status, detail):
        checks.append(Check(key, title, status, detail))
        print(f"  {status:4}  {title}: {detail}", flush=True)

    quality = _load(_results("openlakehouse", sf, "quality.json"))
    dbx_quality = _load(_results("databricks", sf, "quality.json"))
    uc = client()

    # 1. Delta tables readable by OSS Spark
    try:
        spark = ol.spark_session()
        names = [f"freedom.{s}.{t}" for s in (f"tpch_{tag}_bronze", f"tpch_{tag}") for t in TABLES]
        names += [f"freedom.tpch_{tag}_gold.revenue_by_nation_year",
                  "freedom.incremental.customer_changes", "freedom.incremental.customer_scd2"]
        bad = []
        for n in names:
            try:
                spark.table(n).limit(1).collect()
            except Exception as e:
                bad.append(f"{n}: {str(e).splitlines()[0][:120]}")
        add("delta_readable", "Delta tables readable", FAIL if bad else PASS,
            f"{len(names) - len(bad)}/{len(names)} tables read by Spark {spark.version} through UC OSS"
            + (f"; failed: {bad}" if bad else ""))
    except Exception as e:
        spark = None
        add("delta_readable", "Delta tables readable", FAIL, f"Spark Connect unavailable: {e}")

    # 2. Schemas
    if quality is None:
        add("schemas", "Schemas compatible", FAIL, "quality.json missing; run the pipeline")
    else:
        mism = [t for t, v in quality["tables"].items() if not v["schema_matches"]]
        detail = f"{8 - len(mism)}/8 Silver tables match the canonical TPC-H schema"
        if dbx_quality:
            cross = [t for t in TABLES if dbx_quality["tables"][t]["schema"] != quality["tables"][t]["schema"]]
            mism += cross
            detail += f"; Databricks vs OpenLakehouse schemas identical for {8 - len(cross)}/8"
        else:
            detail += "; Databricks schemas not available"
        add("schemas", "Schemas compatible", FAIL if mism else PASS, detail)

    # 3. Row counts and keys
    if quality:
        problems = []
        for t, v in quality["tables"].items():
            if v["expected_rows"] is not None and v["rows"] != v["expected_rows"]:
                problems.append(f"{t} {v['rows']}!={v['expected_rows']}")
            if not (v["pk_unique"] and v["pk_not_null"]):
                problems.append(f"{t} primary key")
        problems += [f"{fk['child']} orphans={fk['orphans']}" for fk in quality["foreign_keys"] if fk["orphans"]]
        add("row_counts", "Expected row counts and keys", FAIL if problems else PASS,
            "dbgen row counts, primary keys and 7 foreign keys hold" if not problems else "; ".join(problems))

    # 4. Transformation outputs equivalent (independent DuckDB oracle + cross-platform fingerprints)
    try:
        con = _duck()
        diffs = []
        locs = {t: uc.get_table(f"freedom.tpch_{tag}.{t}")["storage_location"] for t in TABLES}
        for t in TABLES:
            raw = f"read_parquet('{ol.RAW_ROOT}/{tag}/{t}/*.parquet')"
            expected = con.execute(_profile_sql(raw, t, conform=True)).fetchone()
            actual = con.execute(_profile_sql(f"delta_scan('{locs[t]}')", t, conform=False)).fetchone()
            if expected != actual:
                diffs.append(t)
        gold_loc = uc.get_table(f"freedom.tpch_{tag}_gold.revenue_by_nation_year")["storage_location"]
        oracle = con.execute(f"""
            SELECT n_name, year(o_orderdate), count(DISTINCT o_orderkey), sum(l_quantity),
                   CAST(sum(l_extendedprice * (1 - l_discount)) AS DECIMAL(38,4))
            FROM delta_scan('{locs['orders']}') o
            JOIN delta_scan('{locs['lineitem']}') l ON o_orderkey = l_orderkey
            JOIN delta_scan('{locs['customer']}') c ON o_custkey = c_custkey
            JOIN delta_scan('{locs['nation']}') n ON c_nationkey = n_nationkey
            GROUP BY ALL ORDER BY 1, 2""").fetchall()
        gold = con.execute(f"SELECT nation, order_year, orders, quantity, net_revenue "
                           f"FROM delta_scan('{gold_loc}') ORDER BY 1, 2").fetchall()
        gold_ok = compare.rows_equal([list(r) for r in gold], [list(r) for r in oracle])[0]
        detail = (f"Silver equals DuckDB's independent conform of Raw for {8 - len(diffs)}/8 tables; "
                  f"Gold equals DuckDB SQL oracle: {gold_ok}")
        status = PASS if not diffs and gold_ok else FAIL
        if dbx_quality:
            fp_diff = [t for t in TABLES if dbx_quality["tables"][t]["fingerprint"]["hash_sum"]
                       != quality["tables"][t]["fingerprint"]["hash_sum"]]
            detail += f"; Databricks fingerprints identical for {8 - len(fp_diff)}/8"
            status = FAIL if fp_diff else status
        else:
            detail += "; Databricks fingerprints not available"
        add("transformations", "Transformation outputs equivalent", status, detail)
    except Exception as e:
        add("transformations", "Transformation outputs equivalent", FAIL, str(e).splitlines()[0][:300])

    # 5. TPC-H results
    prefer = [("databricks", "spark"), ("openlakehouse", "spark")]
    parts, failed = [], False
    for platform, engine in (("openlakehouse", "spark"), ("openlakehouse", "duckdb"), ("databricks", "spark")):
        classes = compare.classify(platform, engine, sf, prefer)
        if classes is None:
            parts.append(f"{platform}/{engine}: not run")
            if platform == "openlakehouse":
                failed = True
            continue
        counts = compare.summarize(classes)
        failed |= counts["FAILED"] > 0
        ref = next(iter(classes.values()))["reference"]
        parts.append(f"{platform}/{engine}: {22 - counts['FAILED']}/22 correct vs {ref}")
    add("tpch_results", "TPC-H results equivalent", FAIL if failed else PASS, "; ".join(parts))

    # 6. Spark transformations executable
    missing = [f for f in ("generator.json", "quality.json", "gold.json", "spark/run.json")
               if not _results("openlakehouse", sf, f).exists()]
    run_json = _load(_results("openlakehouse", sf, "spark", "run.json"))
    ok_q = sum(q["success"] for q in run_json["queries"].values()) if run_json else 0
    add("spark_executable", "Spark transformations executable", FAIL if missing or ok_q < 22 else PASS,
        f"pipeline tasks {[t.key for t in TASKS]} completed on OpenLakehouse Spark; {ok_q}/22 queries ran"
        if not missing else f"missing outputs: {missing}")

    # 7. Unity Catalog metadata
    try:
        silver_tables = uc.tables("freedom", f"tpch_{tag}")
        ok = len(silver_tables) == 8 and all(
            t["data_source_format"] == "DELTA" and t["storage_location"] for t in silver_tables)
        detail = f"UC OSS lists {len(silver_tables)} Silver tables with DELTA format and storage location"
        if probe_catalog:
            from freedom.validation.catalog_portability import probe

            p = probe()
            (REPO / "reports").mkdir(exist_ok=True)
            (REPO / "reports" / "catalog-probe.json").write_text(json.dumps(p, indent=1))
            gaps = [i["key"] for i in p["items"] if not i["recreated"]]
            rest = next(i for i in p["items"] if i["key"] == "rest_registration")["recreated"]
            ok = ok and rest
            detail += (f"; catalog probe: {p['recreated']}/{p['total']} Databricks UC capabilities recreated "
                       f"(gaps: {', '.join(gaps) or 'none'})")
        add("unity_catalog", "Unity Catalog metadata accessible/recreated", PASS if ok else FAIL, detail)
    except Exception as e:
        add("unity_catalog", "Unity Catalog metadata accessible/recreated", FAIL, str(e)[:300])

    # 8. DuckDB access
    try:
        loc = uc.get_table(f"freedom.tpch_{tag}.lineitem")["storage_location"]
        n = _duck().execute(f"SELECT count(*) FROM delta_scan('{loc}')").fetchone()[0]
        exp = expected_row_count("lineitem", sf)
        add("duckdb_access", "DuckDB can access selected tables", PASS if exp in (None, n) else FAIL,
            f"DuckDB {duckdb.__version__} read lineitem ({n:,} rows) via UC OSS-resolved location {loc}")
    except Exception as e:
        add("duckdb_access", "DuckDB can access selected tables", FAIL, str(e).splitlines()[0][:300])

    # 9 + 10. Incremental and SCD2
    scd = _load(compare.RESULTS / "openlakehouse" / "incremental" / "scd2.json")
    if scd is None:
        add("incremental", "Incremental pipeline works", FAIL, "scd2.json missing; run the pipeline")
    else:
        ok = scd["reingest_refused"] and scd["replay_idempotent"] and len(scd["rows"]) > 0
        add("incremental", "Incremental pipeline works", PASS if ok else FAIL,
            f"3 batches applied incrementally; duplicate batch refused: {scd['reingest_refused']}; "
            f"replay idempotent: {scd['replay_idempotent']}")
    parts, status = [], PASS
    for platform in ("openlakehouse", "databricks"):
        ok, why = compare.scd2_matches(platform)
        if ok is None:
            parts.append(f"{platform}: not run")
            status = FAIL if platform == "openlakehouse" else status
        else:
            parts.append(f"{platform}: {'equal' if ok else 'DIFFERENT'} to the Python oracle")
            status = status if ok else FAIL
    add("scd2", "SCD2 behaviour equivalent", status, "; ".join(parts))

    # 11. Shared code free of Databricks-specific constructs
    from freedom.assessment.inventory import measure
    from freedom.assessment.scanner import RULES, scan

    inv = measure()
    shared = [REPO / f["path"] for f in inv["files"] if f["group"] == "shared"]
    hits = scan(shared, REPO)
    add("shared_code", "Shared code has no Databricks-specific APIs", FAIL if hits else PASS,
        f"{len(shared)} shared files scanned with {len(RULES)} rules"
        + (f"; hits: {[(h['file'], h['line'], h['rule']) for h in hits]}" if hits else "; no hits"))

    # 12. Orchestration definitions match the shared graph
    job = yaml.safe_load((REPO / "platforms/databricks/resources/lakehouse_freedom.job.yml").read_text())
    tasks = job["resources"]["jobs"]["lakehouse_freedom"]["tasks"]
    job_graph = {t["task_key"]: tuple(d["task_key"] for d in t.get("depends_on", [])) for t in tasks}
    graph = {t.key: t.depends_on for t in TASKS}
    dag_src = (REPO / "platforms/openlakehouse/airflow/dags/lakehouse_freedom.py").read_text()
    dag_ok = "from lakehouse_freedom.common.pipeline import TASKS" in dag_src
    add("orchestration", "Orchestration matches the shared task graph",
        PASS if job_graph == graph and dag_ok else FAIL,
        f"Databricks job: {'identical' if job_graph == graph else 'DIFFERENT'}; "
        f"Airflow DAG: {'generated from' if dag_ok else 'NOT generated from'} the shared graph")

    # 13. Databricks side
    dbx = _load(_results("databricks", sf, "spark", "run.json"))
    if dbx is None:
        add("databricks", "Databricks reference run available", SKIP,
            "no Databricks results for this scale factor; see platforms/databricks/README.md")
    else:
        ok = sum(q["success"] for q in dbx["queries"].values())
        add("databricks", "Databricks reference run available", PASS if ok == 22 else FAIL,
            f"{ok}/22 queries succeeded on Databricks ({dbx['environment'].get('compute')})")

    out = REPO / "reports" / f"freedom-check-{tag}.json"
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps([asdict(c) for c in checks], indent=1))
    return checks

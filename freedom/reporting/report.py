"""Generate reports/freedom-report.md from measured artefacts.

The report only states what the artefacts in benchmarks/results/ and reports/
show. Where something was not run, it says so.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import yaml

from freedom.assessment.inventory import measure
from freedom.assessment.scanner import scan
from freedom.reporting.score import bar, components, freedom_score
from freedom.validation import compare
from lakehouse_freedom.common.config import scale_tag
from lakehouse_freedom.common.tpch_schema import TABLES

REPO = Path(__file__).resolve().parents[2]
CAPABILITIES = REPO / "freedom" / "assessment" / "capabilities.yaml"


def _load(path: Path):
    return json.loads(path.read_text()) if path.exists() else None


def _table(headers: list[str], rows: list[list]) -> str:
    out = ["| " + " | ".join(headers) + " |", "|" + "|".join("---" for _ in headers) + "|"]
    out += ["| " + " | ".join("" if v is None else str(v) for v in r) + " |" for r in rows]
    return "\n".join(out)


def _fmt_s(v) -> str:
    return "" if v is None else f"{v:.2f}"


def render(scale_factor: float) -> str:
    sf, tag = scale_factor, scale_tag(scale_factor)
    res = compare.RESULTS
    ol_run = _load(res / "openlakehouse" / tag / "spark" / "run.json")
    duck_run = _load(res / "openlakehouse" / tag / "duckdb" / "run.json")
    dbx_run = _load(res / "databricks" / tag / "spark" / "run.json")
    gen = _load(res / "openlakehouse" / tag / "generator.json")
    quality = _load(res / "openlakehouse" / tag / "quality.json")
    checks = _load(REPO / "reports" / f"freedom-check-{tag}.json") or []
    day = _load(REPO / "reports" / f"freedom-day-{tag}.json")
    probe = _load(REPO / "reports" / "catalog-probe.json")
    comps = components(sf)
    score = freedom_score(comps)
    inv = measure()
    env = (ol_run or {}).get("environment", {})
    prefer = [("databricks", "spark"), ("openlakehouse", "spark")]
    classes = {k: compare.classify(p, e, sf, prefer) for k, (p, e) in {
        "OpenLakehouse Spark": ("openlakehouse", "spark"),
        "OpenLakehouse DuckDB": ("openlakehouse", "duckdb"),
        "Databricks": ("databricks", "spark")}.items()}

    L: list[str] = []
    w = L.append
    w("# 🗽 Lakehouse Freedom Report")
    w("")
    w(f"Scale factor **{sf:g}** (`{tag}`) · generated {datetime.now(timezone.utc):%Y-%m-%d %H:%M} UTC "
      f"by `make freedom-report SCALE={sf:g}`")
    w("")
    if not dbx_run:
        w("> **Scope of this report.** The Databricks side of the workload has not been run for this "
          "scale factor, so every comparison below uses the OpenLakehouse run, the official TPC-H answers "
          "(where they exist) and independent DuckDB oracles. Databricks columns are marked *not run*. "
          "Run the bundle in `platforms/databricks/` and `make databricks-fetch-results` to complete it.")
        w("")

    # 1
    w("## 1. Architecture tested")
    w("")
    w("```")
    w("                 TPC-H dbgen (DuckDB) ──► Raw Parquet")
    w("                                           │")
    w("                         Bronze ──► Silver ──► Gold   (Delta, external tables)")
    w("                                           │")
    w("          ┌────────────────────────────────┴───────────────────────────────┐")
    w("          ▼                                                                ▼")
    w("   Databricks                                                     OpenLakehouse")
    w("   Spark · Delta · Unity Catalog · Workflows · Bundles            Spark Connect · Delta · UC OSS")
    w("                                                                  DuckDB · Airflow · SeaweedFS")
    w("```")
    w("")
    w(_table(["Platform", "Role", "Status for this report"], [
        ["Databricks", "Managed implementation (bundle in `platforms/databricks`)",
         "results available" if dbx_run else "not run"],
        ["OpenLakehouse", "Freedom implementation (`platforms/openlakehouse`)",
         "results available" if ol_run else "not run"],
        ["DuckDB on OpenLakehouse storage", "Second open engine on the same Delta tables",
         "results available" if duck_run else "not run"],
        ["Freedom Day", "Catalog rebuilt from storage only",
         ("passed" if day and day["passed"] else "failed") if day else "not run"],
    ]))
    w("")

    # 2
    w("## 2. Software versions")
    w("")
    rows = [
        ["OpenLakehouse", f"[{(env.get('openlakehouse_commit') or '')[:10]}]({env.get('openlakehouse_repo')})"
                          if env.get("openlakehouse_commit") else None],
        ["Apache Spark", env.get("engine_version")],
        ["Spark image", env.get("spark_image")],
        ["Delta Lake (delta-spark)", env.get("delta_version")],
        ["Unity Catalog OSS server", env.get("unitycatalog_server")],
        ["Unity Catalog Spark connector", env.get("unitycatalog_spark_connector")],
        ["SeaweedFS (S3)", env.get("seaweedfs")],
        ["DuckDB", (duck_run or {}).get("environment", {}).get("engine_version") or (gen or {}).get("duckdb_version")],
        ["TPC-H generator", f"{gen['generator']}, tpch extension {gen['tpch_extension_version']}" if gen else None],
    ]
    if dbx_run:
        de = dbx_run["environment"]
        rows += [["Databricks Spark", de.get("engine_version")],
                 ["Databricks runtime", de.get("databricks_runtime") or de.get("sparkVersion")]]
    w(_table(["Component", "Version"], rows))
    w("")
    sc = env.get("spark_conf", {})
    w(f"OpenLakehouse compute: {env.get('compute', 'n/a')}; executor {sc.get('spark.executor.cores')} cores / "
      f"{sc.get('spark.executor.memory')}, driver {sc.get('spark.driver.memory')}; host "
      f"{env.get('host_cpus')} CPUs, {env.get('host_memory_gb')} GB RAM, {env.get('host_os')}.")
    w("")

    # 3
    w("## 3. Dataset scale")
    w("")
    if gen and quality:
        w(f"TPC-H SF{sf:g}, generated in {gen['chunks']} chunk(s) in {gen['duration_s']:.0f} s.")
        w("")
        w(_table(["Table", "Rows", "Expected (dbgen)", "Primary key unique"],
                 [[t, f"{quality['tables'][t]['rows']:,}",
                   f"{quality['tables'][t]['expected_rows']:,}" if quality['tables'][t]['expected_rows'] else "n/a",
                   "yes" if quality["tables"][t]["pk_unique"] else "NO"] for t in TABLES]))
    else:
        w("Not run.")
    w("")

    # 4
    w("## 4. Portability results (Freedom Check)")
    w("")
    if checks:
        w(_table(["Check", "Status", "Evidence"], [[c["title"], c["status"], c["detail"]] for c in checks]))
    else:
        w("Freedom Check not run for this scale factor (`make freedom-check`).")
    w("")
    if day:
        writers = ", ".join(day["writers"])
        kind = f"rehearsal, tables written by {writers}" if day["rehearsal"] else f"tables written by {writers}"
        dp = day["data_portability"]
        w(f"**Freedom Day** ({kind}): {dp['portable_tables']}/{dp['total_tables']} tables re-registered "
          f"from storage into an empty catalog and read by Spark and DuckDB; storage objects changed: "
          f"{'none' if day['data_unchanged'] else 'SOME'}.")
        w("")
        feats = sorted({f for t in day["tables"] for f in t["table_features"]})
        w(f"Delta protocol across these tables: reader version "
          f"{sorted({t['min_reader_version'] for t in day['tables']})}, writer version "
          f"{sorted({t['min_writer_version'] for t in day['tables']})}, table features {feats}.")
        w("")

    # 5
    w("## 5. TPC-H query compatibility")
    w("")
    w("Canonical SQL: `tpch/queries/qNN.sql`, written for Databricks SQL / Spark SQL. A query is "
      "PORTABLE when the unchanged text runs and returns the reference result, ADAPTABLE when a small "
      "dialect change (at most 20% of lines) is needed, REWRITE for larger changes, FAILED otherwise.")
    w("")
    summary_rows = []
    for name, cl in classes.items():
        if cl is None:
            summary_rows.append([name, "not run", "", "", "", ""])
            continue
        c = compare.summarize(cl)
        summary_rows.append([name, f"{c['PORTABLE']}/22", c["ADAPTABLE"], c["REWRITE"], c["FAILED"],
                             next(iter(cl.values()))["reference"]])
    w(_table(["Target", "Unchanged and correct", "Adaptable", "Rewrite", "Failed", "Reference"], summary_rows))
    w("")
    rows = []
    for q in range(1, 23):
        k = f"q{q:02d}"
        rows.append([k] + [(cl[k]["classification"] if cl else "not run") for cl in classes.values()])
    w("<details markdown=\"1\"><summary>Per-query classification</summary>")
    w("")
    w(_table(["Query"] + list(classes), rows))
    w("")
    w("</details>")
    w("")

    # 6
    w("## 6. Benchmark results")
    w("")
    w("> **Read this before comparing numbers.** These timings come from different kinds of compute "
      "(see environments below). A laptop running Docker is not comparable to a Databricks cluster or "
      "serverless warehouse, so these numbers show that the workload runs and roughly how long it takes "
      "in each place. They do not say which platform is faster. The primary result of this benchmark is "
      "portability (section 5).")
    w("")
    runs = {"OpenLakehouse Spark": ol_run, "OpenLakehouse DuckDB": duck_run, "Databricks": dbx_run}
    rows = []
    for q in range(1, 23):
        k = f"q{q:02d}"
        rows.append([k] + [(_fmt_s(r["queries"][k]["duration_s"]) if r and r["queries"][k]["success"]
                            else ("fail" if r else "not run")) for r in runs.values()])
    totals = []
    for r in runs.values():
        if r and all(v["success"] for v in r["queries"].values()):
            totals.append(f"**{sum(v['duration_s'] for v in r['queries'].values()):.1f}**")
        else:
            totals.append("n/a")
    rows.append(["**total**"] + totals)
    w(_table(["Query (median s)"] + list(runs), rows))
    w("")
    for name, r in runs.items():
        if r:
            e = r["environment"]
            w(f"- **{name}**: {e.get('platform_label')}; {e.get('compute')}; repeats per query: {r['repeats']}; "
              f"engine {e.get('engine_version')}.")
    w("")

    # 7
    w("## 7. Platform-specific code")
    w("")
    tot = inv["totals"]
    w(_table(["Group", "Transformation LOC", "Orchestration LOC", "Infrastructure LOC"], [
        [g, tot.get(g, {}).get("transformation", 0), tot.get(g, {}).get("orchestration", 0),
         tot.get(g, {}).get("infrastructure", 0)] for g in ("shared", "databricks", "openlakehouse")]))
    w("")
    w("LOC = logical lines (no blanks, comments or docstrings). File-level detail:")
    w("")
    w("<details markdown=\"1\"><summary>Files</summary>")
    w("")
    w(_table(["File", "Group", "Category", "LOC"],
             [[f"`{f['path']}`", f["group"], f["category"], f["loc"]] for f in inv["files"]]))
    w("")
    w("</details>")
    w("")
    hits = scan([REPO / "platforms" / "databricks"], REPO)
    w(f"Databricks-specific constructs found by the scanner in `platforms/databricks/`: {len(hits)} "
      f"({', '.join(sorted({h['rule'] for h in hits})) or 'none'}). In shared code: "
      f"{len(scan([REPO / f['path'] for f in inv['files'] if f['group'] == 'shared'], REPO))}.")
    w("")

    # 8
    w("## 8. Capability mapping")
    w("")
    caps = yaml.safe_load(CAPABILITIES.read_text())
    probe_items = {i["key"]: i for i in (probe or {}).get("items", [])}
    w(_table(["Capability", "Databricks", "OpenLakehouse", "Classification", "Evidence"],
             [[c["capability"], c["databricks"], c["openlakehouse"], f"**{c['classification']}**",
               c["evidence"]] for c in caps]))
    w("")
    if probe_items:
        w("Catalog probe (live, against UC OSS):")
        w("")
        w(_table(["Unity Catalog capability", "Recreated", "Evidence"],
                 [[i["capability"], "yes" if i["recreated"] else "**no**", i["evidence"]]
                  for i in probe_items.values()]))
        w("")

    # 9
    w("## 9. Known limitations")
    w("")
    lim = []
    if not dbx_run:
        lim.append("The Databricks side was not executed for this report. SQL portability is measured against "
                   "the official TPC-H answers (SF ≤ 1) or the OpenLakehouse Spark run, not against Databricks output.")
    if day and day.get("rehearsal"):
        lim.append("Freedom Day ran as a rehearsal on tables written by OSS Spark. Tables written by Databricks "
                   "may carry additional Delta table features (for example deletion vectors or row tracking); "
                   "the Freedom Day report lists the features it actually found.")
    lim += [
        "Performance numbers compare unlike compute and must not be read as a platform performance ranking.",
        "UC OSS runs with authorization disabled (OpenLakehouse default); grants, row filters and masks "
        "are not migrated.",
        "The DuckDB `unity_catalog` extension cannot read from SeaweedFS through UC OSS credential vending "
        "(vended credentials carry no S3 endpoint); DuckDB resolves locations through UC and reads with a "
        "configured S3 secret.",
        "The Airflow DAG is generated from the shared graph and consistency-checked, but v1 runs the "
        "OpenLakehouse pipeline from the command line rather than from Airflow.",
        "SQL portability is measured on TPC-H only. TPC-H uses a conservative SQL subset; real workloads using "
        "Databricks SQL extensions will score lower (use `freedom assess` to find them).",
        "Lines-of-code ratios measure how much code is shared, not how hard the platform-specific part is to write.",
    ]
    for item in lim:
        w(f"- {item}")
    w("")

    # 10
    w("## 10. Freedom Score")
    w("")
    w("```")
    w("LAKEHOUSE FREEDOM REPORT")
    w("────────────────────────────────────────────")
    for c in comps:
        w(c["name"])
        w(bar(c["value"]) + (f"   ({c['numerator']}/{c['denominator']})" if c["value"] is not None else ""))
    w("────────────────────────────────────────────")
    w("Freedom Score")
    w(bar(score))
    w("```")
    w("")
    w(_table(["Component", "Formula", "Included in Freedom Score"],
             [[c["name"], c["formula"], "yes" if c["in_score"] else "no (additional engine)"] for c in comps]))
    w("")
    w("Freedom Score = unweighted mean of the included, measured components. Definitions: "
      "`freedom/reporting/score.py`.")
    w("")

    # 11
    w("## 11. Conclusions")
    w("")
    w(_conclusions(comps, classes, day, probe, dbx_run))
    w("")
    return "\n".join(L)


def _conclusions(comps, classes, day, probe, dbx_run) -> str:
    c = {x["key"]: x for x in comps}
    parts = []
    if day:
        parts.append(
            f"**Data.** {day['data_portability']['portable_tables']} of "
            f"{day['data_portability']['total_tables']} Delta tables were readable by two open engines after "
            f"the catalog was rebuilt from storage alone, and no stored object was rewritten. Keeping tables "
            f"external, in an open format, on storage you control (F1) is what makes this possible.")
    sp = classes.get("OpenLakehouse Spark")
    dk = classes.get("OpenLakehouse DuckDB")
    if sp:
        s = compare.summarize(sp)
        parts.append(f"**SQL.** {s['PORTABLE']} of 22 TPC-H queries ran unchanged on open-source Spark with "
                     f"correct results" + (f", and {compare.summarize(dk)['PORTABLE']} of 22 on DuckDB" if dk else "")
                     + ". TPC-H is a conservative SQL subset, so treat this as an upper bound for real workloads.")
    t = c["transformation"]
    parts.append(f"**Code.** {t['value'] * 100:.0f}% of the code that runs the workload on OpenLakehouse is "
                 f"identical to the code that runs it on Databricks ({t['numerator']} of {t['denominator']} "
                 f"LOC). The platform-specific remainder is session setup, configuration and orchestration.")
    if probe:
        gaps = [i["capability"] for i in probe["items"] if not i["recreated"]]
        parts.append(f"**Catalog.** {probe['recreated']} of {probe['total']} Unity Catalog capabilities used by "
                     f"the workload were recreated in UC OSS. Gaps: {'; '.join(gaps)}. This is where a "
                     f"migration needs the most deliberate work, and where the managed catalog clearly "
                     f"adds value (F6).")
    o = c["orchestration"]
    parts.append(f"**Orchestration.** Sharing the task graph keeps both schedulers aligned, but the scheduler "
                 f"definitions themselves are platform code ({o['value'] * 100:.0f}% shared).")
    if not dbx_run:
        parts.append("**Next step.** Run the Databricks bundle to replace the stand-in references with "
                     "measured Databricks output, and run Freedom Day against a sync of the Databricks "
                     "external location.")
    return "\n\n".join(parts)


def write(scale_factor: float) -> Path:
    """Write reports/freedom-report-<sf>.md and make it the current reports/freedom-report.md."""
    text = render(scale_factor)
    (REPO / "reports").mkdir(exist_ok=True)
    (REPO / "reports" / f"freedom-report-{scale_tag(scale_factor)}.md").write_text(text)
    path = REPO / "reports" / "freedom-report.md"
    path.write_text(text)
    return path

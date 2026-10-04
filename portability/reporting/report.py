"""Generate reports/portability-report.md from measured artefacts.

The report only states what the artefacts in benchmarks/results/ and reports/
show. Where something was not run, it says so.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import yaml

from portability.assessment.feature_coverage import load as load_feature_matrix
from portability.assessment.feature_coverage import summarize as summarize_features
from portability.assessment.inventory import measure
from portability.assessment.scanner import scan
from portability.reporting.score import bar, components, portability_score
from portability.validation import compare
from portable_lakehouse.common.config import scale_tag
from portable_lakehouse.common.tpch_schema import TABLES
from portable_lakehouse.governance.datafusion import SUPPORTED_OBLIGATIONS

REPO = Path(__file__).resolve().parents[2]
CAPABILITIES = REPO / "portability" / "assessment" / "capabilities.yaml"


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
    datafusion_run = _load(res / "openlakehouse" / tag / "datafusion" / "run.json")
    dbx_run = _load(res / "databricks" / tag / "spark" / "run.json")
    gen = _load(res / "openlakehouse" / tag / "generator.json")
    quality = _load(res / "openlakehouse" / tag / "quality.json")
    probe = _load(REPO / "reports" / "catalog-probe.json")
    comps = components(sf)
    score = portability_score(comps)
    inv = measure()
    feature_matrix = load_feature_matrix()
    env = (ol_run or {}).get("environment", {})
    L: list[str] = []
    w = L.append
    w("# 🗽 Portable Lakehouse Report")
    w("")
    w(f"Scale factor **{sf:g}** (`{tag}`) · generated {datetime.now(timezone.utc):%Y-%m-%d %H:%M} UTC "
      f"by `make portability-report SCALE={sf:g}`")
    w("")
    if not dbx_run:
        w("> **Scope of this report.** The Databricks side of the workload has not been run for this "
          "scale factor, so every comparison below uses the OpenLakehouse run, the official TPC-H answers "
          "(where they exist) and separate DuckDB reference results. Databricks columns are marked *not run*. "
          "Run the bundle in `platforms/databricks/` and `make databricks-fetch-results` to complete it.")
        w("")

    w("## Portability Score")
    w("")
    w("```")
    w("Portability Score")
    w(bar(score))
    w("────────────────────────────────────────────")
    for c in comps:
        w(c["name"])
        w(bar(c["value"]) + (f"   ({c['numerator']}/{c['denominator']})" if c["value"] is not None else ""))
    w("```")
    w("")
    detail_links = {
        "transformation": "[view files](#5-platform-specific-code)",
        "catalog": "[view 10 capabilities](#catalog-portability-details)",
        "orchestration": "[view files](#5-platform-specific-code)",
        "governance": "[view obligations](#governance-portability-details)",
    }
    w(_table(["Component", "Formula", "Included in Portability Score", "Details"],
             [[c["name"], c["formula"], "yes" if c["in_score"] else "no (additional engine)",
               detail_links[c["key"]]] for c in comps]))
    w("")
    w("The score is the unweighted mean of the included, measured components. The capability coverage "
      "later in this report provides the broader comparison of native support, alternatives, workarounds and gaps.")
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
    w("                                                        DuckDB · DataFusion · Airflow · SeaweedFS")
    w("```")
    w("")
    w(_table(["Platform", "Role", "Status for this report"], [
        ["Databricks", "Managed implementation (bundle in `platforms/databricks`)",
         "results available" if dbx_run else "not run"],
        ["OpenLakehouse", "Open-source implementation (`platforms/openlakehouse`)",
         "results available" if ol_run else "not run"],
        ["DuckDB on OpenLakehouse storage", "Second open engine on the same Delta tables",
         "results available" if duck_run else "not run"],
        ["DataFusion on OpenLakehouse storage", "Third engine and future governed-query enforcement point",
         "results available" if datafusion_run else "not run"],
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
        ["Apache DataFusion", (datafusion_run or {}).get("environment", {}).get("engine_version")],
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
    w("## 4. Benchmark results")
    w("")
    w("> **Read this before comparing numbers.** These timings come from different kinds of compute "
      "(see environments below). A laptop running Docker is not comparable to a Databricks cluster or "
      "serverless warehouse, so these numbers show that the workload runs and roughly how long it takes "
      "in each place. They do not say which platform is faster.")
    w("")
    runs = {
        "OpenLakehouse Spark": ol_run,
        "OpenLakehouse DuckDB": duck_run,
        "OpenLakehouse DataFusion": datafusion_run,
        "Databricks": dbx_run,
    }
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
    w("## 5. Platform-specific code")
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
    w("## 6. Capability mapping")
    w("")
    caps = yaml.safe_load(CAPABILITIES.read_text())
    probe_items = {i["key"]: i for i in (probe or {}).get("items", [])}
    w(_table(["Capability", "Databricks", "OpenLakehouse", "Classification", "Evidence"],
             [[c["capability"], c["databricks"], c["openlakehouse"], f"**{c['classification']}**",
               c["evidence"]] for c in caps]))
    w("")
    if probe_items:
        w("### Catalog portability details")
        w("")
        w("These are the ten capabilities behind the catalog score. The six marked **yes** are supported "
          "in the tested UC OSS configuration.")
        w("")
        w(_table(["Unity Catalog capability", "Recreated", "Evidence"],
                 [[i["capability"], "yes" if i["recreated"] else "**no**", i["evidence"]]
                  for i in probe_items.values()]))
        w("")

    w("### Governance portability details")
    w("")
    w("These are the reviewed obligations behind the governance score. Support means the DataFusion "
      "adapter enforces the obligation; unsupported obligations fail closed.")
    w("")
    governance_registry = yaml.safe_load((REPO / "governance" / "obligations.yaml").read_text())
    governance_names = {
        ("row_filter", "tenant_isolation"): "Tenant row filtering",
        ("column_mask", "mask_email"): "Email column masking",
    }
    governance_rows = []
    for policy_id, obligations in governance_registry.items():
        for obligation in obligations:
            key = (obligation["kind"], obligation["name"])
            supported = key in SUPPORTED_OBLIGATIONS
            governance_rows.append([
                governance_names.get(key, obligation["name"].replace("_", " ").title()),
                f"`{obligation['kind']}/{obligation['name']}`",
                policy_id,
                "yes" if supported else "**no**",
                "compiled into a DataFusion expression" if supported else "fails closed; not implemented",
            ])
    w(_table(["Governance feature", "Obligation", "Policy", "Enforced", "Evidence"], governance_rows))
    w("")

    # 9
    w("## 7. Platform capability coverage")
    w("")
    w("This broader, curated comparison is separate from the Portability Score: it includes important managed "
      "features even when this workload does not use them. Outcome coverage includes native capabilities, "
      "alternatives and workarounds; native parity counts only substantially equivalent capabilities. "
      f"Matrix as of **{feature_matrix['as_of']}**.")
    w("")
    for profile in feature_matrix["profiles"]:
        summary = summarize_features(profile)
        w(f"### {profile['component']}")
        w("")
        w(f"`{profile['source']}` → `{profile['target']}`")
        w("")
        w("```")
        w("Outcome coverage  " + bar(summary["outcome_coverage"]) +
          f"   ({summary['covered']}/{summary['total']})")
        w("Native parity     " + bar(summary["native_parity"]) +
          f"   ({summary['native']}/{summary['total']})")
        w("```")
        w("")
        counts = summary["counts"]
        w(f"Native **{counts['NATIVE']}** · alternatives **{counts['ALTERNATIVE']}** · "
          f"workarounds **{counts['WORKAROUND']}** · missing **{counts['MISSING']}** · "
          f"not assessed **{counts['NOT_ASSESSED']}** · workload-required coverage "
          f"**{summary['required_covered']}/{summary['required_total']}**")
        w("")
        w("<details markdown=\"1\"><summary>Every capability and gap</summary>")
        w("")
        rows = []
        for feature in profile["features"]:
            detail = feature.get("gap") or feature.get("alternative") or "—"
            rows.append([feature["area"], feature["capability"], f"**{feature['status']}**",
                         "yes" if feature["workload"] == "required" else "no", detail,
                         feature["evidence"]])
        w(_table(["Area", "Capability", "Status", "Required here", "Gap or alternative", "Evidence"], rows))
        w("")
        w("</details>")
        w("")
    w("Definitions and maintenance rules: `docs/platform-capability-coverage.md`.")
    w("")

    # 10
    w("## 8. Known limitations")
    w("")
    lim = []
    if not dbx_run:
        lim.append("The Databricks side was not executed for this report. SQL portability is measured against "
                   "the official TPC-H answers (SF ≤ 1) or the OpenLakehouse Spark run, not against Databricks output.")
    lim += [
        "Performance numbers compare unlike compute and must not be read as a platform performance ranking.",
        "UC OSS runs with authorization disabled (OpenLakehouse default); grants, row filters and masks "
        "are not enabled in this reference architecture.",
        "The DuckDB `unity_catalog` extension cannot read from SeaweedFS through UC OSS credential vending "
        "(vended credentials carry no S3 endpoint); DuckDB resolves locations through UC and reads with a "
        "configured S3 secret.",
        "The Airflow DAG is generated from the shared graph and consistency-checked, but v1 runs the "
        "OpenLakehouse pipeline from the command line rather than from Airflow.",
        "SQL portability is measured on TPC-H only. TPC-H uses a conservative SQL subset; real workloads using "
        "Databricks SQL extensions may require adaptation (use `portable-lakehouse assess` to identify them).",
        "Lines-of-code ratios measure how much code is shared, not how hard the platform-specific part is to write.",
    ]
    for item in lim:
        w(f"- {item}")
    w("")

    # 10
    w("## 9. Conclusions")
    w("")
    w(_conclusions(comps, probe, dbx_run))
    w("")
    return "\n".join(L)


def _conclusions(comps, probe, dbx_run) -> str:
    c = {x["key"]: x for x in comps}
    parts = []
    t = c["transformation"]
    parts.append(f"**Code.** {t['value'] * 100:.0f}% of the code that runs the workload on OpenLakehouse is "
                 f"shared with the code that runs it on Databricks ({t['numerator']} of {t['denominator']} "
                 f"LOC). The platform-specific remainder is session setup, configuration and orchestration.")
    if probe:
        gaps = [i["capability"] for i in probe["items"] if not i["recreated"]]
        parts.append(f"**Catalog.** {probe['recreated']} of {probe['total']} Unity Catalog capabilities used by "
                     f"the workload are also supported by UC OSS. Gaps: {'; '.join(gaps)}. This is where the "
                     f"managed catalog has the clearest capability advantage (P7).")
    o = c["orchestration"]
    parts.append(f"**Orchestration.** Sharing the task graph keeps both schedulers aligned, but the scheduler "
                 f"definitions themselves are platform code ({o['value'] * 100:.0f}% shared).")
    g = c["governance"]
    parts.append(f"**Governance.** The DataFusion adapter enforces {g['numerator']} of {g['denominator']} "
                 "reviewed obligations. This measures obligation coverage, not production identity or "
                 "gateway readiness.")
    if not dbx_run:
        parts.append("**Next step.** Run the Databricks bundle to replace the stand-in references with "
                     "measured Databricks output and complete the two-implementation comparison.")
    return "\n\n".join(parts)


def write(scale_factor: float) -> Path:
    """Write reports/portability-report-<sf>.md and make it the current reports/portability-report.md."""
    text = render(scale_factor)
    (REPO / "reports").mkdir(exist_ok=True)
    (REPO / "reports" / f"portability-report-{scale_tag(scale_factor)}.md").write_text(text)
    path = REPO / "reports" / "portability-report.md"
    path.write_text(text)
    return path

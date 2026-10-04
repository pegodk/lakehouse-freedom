# 🗽 Lakehouse Freedom

**Build managed. Stay open. Keep your freedom.**

[![ci](https://github.com/pegodk/lakehouse-freedom/actions/workflows/ci.yml/badge.svg)](https://github.com/pegodk/lakehouse-freedom/actions/workflows/ci.yml)
[![docs](https://img.shields.io/badge/docs-pegodk.github.io%2Flakehouse--freedom-teal)](https://pegodk.github.io/lakehouse-freedom/)
[![license](https://img.shields.io/badge/license-Apache--2.0-blue)](LICENSE)

Databricks provides a powerful managed lakehouse platform built around open technologies such as Apache Spark and Delta Lake.

Lakehouse Freedom provides two executable reference architectures: Databricks and a fully open-source stack built on [OpenLakehouse.io](https://openlakehouse.io). The same workload makes their supported capabilities and operational tradeoffs directly comparable.

📖 **Documentation: <https://pegodk.github.io/lakehouse-freedom/>**

## Latest result

TPC-H SF10 on OpenLakehouse (local Docker, 8 cores). From [`reports/freedom-report.md`](reports/freedom-report.md):

```
Freedom Score                   █████████████░░░░░░░   67%
─────────────────────────────────────────────────────
Transformation portability      ██████████████████░░   89%   1512/1702 LOC shared
Catalog portability             ████████████░░░░░░░░   60%   6/10 UC capabilities
Orchestration portability       ██████████░░░░░░░░░░   51%   29/57 LOC shared
Governance portability          ····················   not scored
```

Every percentage is a ratio of measured counts. Governance is shown separately because the current implementation is a foundation, not a complete measured enforcement path.

- **[Transformation portability](https://pegodk.github.io/lakehouse-freedom/freedom-score/#transformation-portability):** shared versus platform-specific transformation code.
- **[Catalog portability](https://pegodk.github.io/lakehouse-freedom/freedom-score/#catalog-portability):** Unity Catalog capabilities supported by both implementations.
- **[Orchestration portability](https://pegodk.github.io/lakehouse-freedom/freedom-score/#orchestration-portability):** shared task graph versus scheduler-specific code.
- **[Governance portability](https://pegodk.github.io/lakehouse-freedom/governance/):** portable RBAC/ABAC decisions and typed enforcement obligations using Cedar, with DataFusion as the reference enforcement point.

The Databricks side of the workload is defined and validated but **has not been run** for these results. Until it is, comparisons use the official TPC-H answers and independent DuckDB and Python oracles. See [limitations](#limitations) and the [score formulas](https://pegodk.github.io/lakehouse-freedom/freedom-score/).

## What it does

```
                       workload
                          │
                ┌─────────┴─────────┐
                ▼                   ▼
          🧱 Databricks       🏠 OpenLakehouse.io
           Delta Lake          Delta Lake 4.3.1
           Spark               ⚡ Spark 4.1.0 (Spark Connect)
           Unity Catalog       Unity Catalog OSS 0.5.0 · 🦆 DuckDB 1.5.6
                └─────────┬─────────┘
                          ▼
          CAPABILITY COMPARISON → FREEDOM REPORT
```

- **[Freedom Score](https://pegodk.github.io/lakehouse-freedom/freedom-score/).** Measured ratios summarise shared transformation code, catalog behaviour and orchestration.
- **[Capability coverage](https://pegodk.github.io/lakehouse-freedom/platform-capability-coverage/).** Curated matrices compare native support, alternatives, workarounds and gaps across the two architectures.
- **[Freedom Benchmark](https://pegodk.github.io/lakehouse-freedom/freedom-benchmark/).** One TPC-H workload compares SQL compatibility and execution characteristics across Spark, DuckDB and Apache DataFusion.
- **[Governance portability](https://pegodk.github.io/lakehouse-freedom/governance/).** Cedar provides portable RBAC/ABAC decisions that map reviewed policies to typed row-filter, column-allow and column-mask obligations.
- **[Freedom Assess](https://pegodk.github.io/lakehouse-freedom/reference/commands/#workload-and-measurements).** `make freedom-assess REPO_PATH=...` scans any Databricks project for platform-specific constructs.

## Quickstart

Requires Docker (about 10 GB RAM for containers), [`uv`](https://docs.astral.sh/uv/), `git` and `make`.

```bash
git clone --recurse-submodules https://github.com/pegodk/lakehouse-freedom.git
cd lakehouse-freedom
make setup              # Python env, OpenLakehouse config, Spark JARs
make openlakehouse-up   # SeaweedFS, PostgreSQL, Unity Catalog OSS, Spark 4.1 + Connect
make demo SCALE=1       # pipeline → benchmark → Freedom Check → report
```

`SCALE=0.01` is a one-minute smoke run; `SCALE=10` is the larger reference size. More in [Get started](https://pegodk.github.io/lakehouse-freedom/getting-started/) and [Commands](https://pegodk.github.io/lakehouse-freedom/reference/commands/).

The Databricks side is an Asset Bundle in [`platforms/databricks`](platforms/databricks): `make databricks-run DATABRICKS_PROFILE=... TABLE_ROOT=abfss://...`, then `make databricks-fetch-results`.

## Freedom Principles

| | Principle |
|---|---|
| F1 | Own the data: open table format, external tables, storage you control |
| F2 | Separate business logic from platform logic |
| F3 | Prefer open interfaces: Spark, Delta SQL, Unity Catalog REST, object storage |
| F4 | Isolate managed capabilities so they can be compared directly |
| F5 | Portability must be tested |
| F6 | Managed services are allowed to be better |

The project is about architectural optionality, not an argument against Databricks: keep ownership of your data, logic and future choices while you use a managed platform. [Read more](https://pegodk.github.io/lakehouse-freedom/freedom-principles/).

## Limitations

- The Databricks job has not been run for the committed results (see above).
- Timings come from unlike compute (a laptop vs. a managed service) and are not a platform performance comparison.
- TPC-H is a conservative SQL subset; real workloads using Databricks SQL extensions will score lower.
- Measured Unity Catalog OSS 0.5.0 gaps: no column metadata or custom properties for Spark-created tables, no `ALTER TABLE` via the Spark connector, no grants while authorization is disabled (OpenLakehouse default).
- The Airflow DAG is generated and consistency-checked, but not executed in v1.

Full list in the [report](https://pegodk.github.io/lakehouse-freedom/report/#9-known-limitations).

## Roadmap

v1 is Freedom Challenge #1 (TPC-H / SQL / Delta). Next: streaming and Auto Loader, Lakeflow Declarative Pipelines, Unity Catalog governance, MLflow, Databricks SQL / BI, AI and Vector Search, observability, disaster recovery. See [Freedom Challenges](https://pegodk.github.io/lakehouse-freedom/freedom-challenges/).

## License

[Apache License 2.0](LICENSE). OpenLakehouse is included as a git submodule under its own Apache 2.0 license. Databricks, Delta Lake, Apache Spark and Unity Catalog are trademarks of their respective owners; this project is independent and not affiliated with or endorsed by Databricks or OpenLakehouse.

# Portable Lakehouse

**Build on Databricks. Stay open by design.**

[![ci](https://github.com/pegodk/portable-lakehouse/actions/workflows/ci.yml/badge.svg)](https://github.com/pegodk/portable-lakehouse/actions/workflows/ci.yml)
[![docs](https://img.shields.io/badge/docs-pegodk.github.io%2Fportable--lakehouse-teal)](https://pegodk.github.io/portable-lakehouse/)
[![license](https://img.shields.io/badge/license-Apache--2.0-blue)](LICENSE)

Databricks provides a powerful managed lakehouse platform while building much of its foundation around open technologies such as Apache Spark, Delta Lake and MLflow.

But what does that openness give a lakehouse design in practice?

Portable Lakehouse is an open-source reference architecture, implementation pattern and portability toolkit. It builds a realistic workload for Databricks and then runs the same data—and as much of the same code as practical—on an open-source lakehouse based on [OpenLakehouse.io](https://openlakehouse.io).

Portability should be part of the design of every lakehouse from the start. Databricks is the primary managed implementation because its integrated platform, managed infrastructure and higher-level services provide substantial value. Portable Lakehouse makes the boundary between an open foundation and managed capabilities visible, so teams can use those benefits while preserving ownership of their data, core logic and future architectural choices.

📖 **Documentation: <https://pegodk.github.io/portable-lakehouse/>**

## Latest result

TPC-H SF10 on OpenLakehouse (local Docker, 8 cores). From [`reports/portability-report.md`](reports/portability-report.md):

```
Portability Score                   ████████████░░░░░░░░   62%
─────────────────────────────────────────────────────
Transformation portability      ██████████████████░░   89%   1512/1702 LOC shared
Catalog portability             ████████████░░░░░░░░   60%   6/10 UC capabilities
Orchestration portability       ██████████░░░░░░░░░░   51%   29/57 LOC shared
Governance portability          ██████████░░░░░░░░░░   50%   1/2 obligations enforced
```

Every percentage is a ratio of measured counts. Governance measures reviewed obligation coverage in the DataFusion adapter; it does not claim that production identity integration or gateway hardening is complete.

- **[Transformation portability](https://pegodk.github.io/portable-lakehouse/portability-score/#transformation-portability):** shared versus platform-specific transformation code.
- **[Catalog portability](https://pegodk.github.io/portable-lakehouse/report/#catalog-portability-details):** see exactly which 6 of 10 Unity Catalog capabilities are supported in the tested configuration.
- **[Orchestration portability](https://pegodk.github.io/portable-lakehouse/portability-score/#orchestration-portability):** shared task graph versus scheduler-specific code.
- **[Governance portability](https://pegodk.github.io/portable-lakehouse/report/#governance-portability-details):** see which reviewed features—currently tenant row filtering and email column masking—are enforced by the DataFusion adapter.

The Databricks workload has been run at SF1 and SF10 on serverless jobs compute. The committed results include all 22 TPC-H queries, table-quality and fingerprint evidence, and the incremental SCD2 scenario. See [limitations](#limitations) and the [score formulas](https://pegodk.github.io/portable-lakehouse/portability-score/).

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
          PORTABILITY CHECK → PORTABILITY REPORT
```

- **[Portability Score](https://pegodk.github.io/portable-lakehouse/portability-score/).** Measured ratios summarise shared transformation code, catalog behaviour, orchestration and governance obligation coverage.
- **[Capability coverage](https://pegodk.github.io/portable-lakehouse/platform-capability-coverage/).** Curated matrices compare native support, alternatives, workarounds and gaps across the two architectures.
- **[Portability Benchmark](https://pegodk.github.io/portable-lakehouse/portability-benchmark/).** One TPC-H workload compares SQL compatibility and execution characteristics across Spark, DuckDB and Apache DataFusion.
- **[Governance portability](https://pegodk.github.io/portable-lakehouse/governance/).** Cedar provides portable RBAC/ABAC decisions that map reviewed policies to typed row-filter, column-allow and column-mask obligations.
- **[Portability Assessment](https://pegodk.github.io/portable-lakehouse/reference/commands/#workload-and-measurements).** `make portability-assess REPO_PATH=...` scans any Databricks project for platform-specific constructs.

## Quickstart

Requires Docker (about 10 GB RAM for containers), [`uv`](https://docs.astral.sh/uv/), `git` and `make`.

```bash
git clone --recurse-submodules https://github.com/pegodk/portable-lakehouse.git
cd portable-lakehouse
make setup              # Python env, OpenLakehouse config, Spark JARs
make openlakehouse-up   # SeaweedFS, PostgreSQL, Unity Catalog OSS, Spark 4.1 + Connect
make demo SCALE=1       # pipeline → benchmark → Portability Check → report
```

`SCALE=0.01` is a one-minute smoke run; `SCALE=10` is the larger reference size. More in [Get started](https://pegodk.github.io/portable-lakehouse/getting-started/) and [Commands](https://pegodk.github.io/portable-lakehouse/reference/commands/).

The Databricks side is an Asset Bundle in [`platforms/databricks`](platforms/databricks): `make databricks-run DATABRICKS_PROFILE=... TABLE_ROOT=abfss://...`, then `make databricks-fetch-results`.

## Portability Principles

| | Principle |
|---|---|
| P1 | Own the data: use open table formats on object storage where practical |
| P2 | Separate business logic from platform logic |
| P3 | Prefer open interfaces where practical |
| P4 | Isolate managed capabilities so their migration impact is measurable |
| P5 | Test portability by executing workloads outside Databricks |
| P6 | Portability does not require platform equivalence |
| P7 | Managed services are allowed to be better |

Portability is a design requirement for architectural optionality. It should be considered from the first architectural decisions, including when a managed service is the clear platform choice. [Read more](https://pegodk.github.io/portable-lakehouse/portability-principles/).

## Limitations

- Timings come from unlike compute (a laptop vs. a managed service) and are not a platform performance comparison.
- TPC-H is a conservative SQL subset; other workloads may require more adaptation.
- Measured Unity Catalog OSS 0.5.0 gaps: no column metadata or custom properties for Spark-created tables, no `ALTER TABLE` via the Spark connector, no grants while authorization is disabled (OpenLakehouse default).
- The Airflow DAG is generated and consistency-checked, but not executed in v1.

Full list in the [report](https://pegodk.github.io/portable-lakehouse/report/#9-known-limitations).

## Roadmap

v1 is Portability Challenge #1 (TPC-H / SQL / Delta), with governance and portable MLflow tracking foundations. Next: streaming and Auto Loader, Lakeflow Declarative Pipelines, Databricks SQL / BI, AI and Vector Search, observability, disaster recovery. See [Portability Challenges](https://pegodk.github.io/portable-lakehouse/portability-challenges/).

## License

[Apache License 2.0](LICENSE). OpenLakehouse is included as a git submodule under its own Apache 2.0 license. Databricks, Delta Lake, Apache Spark and Unity Catalog are trademarks of their respective owners; this project is independent and not affiliated with or endorsed by Databricks or OpenLakehouse.

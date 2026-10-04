# Databricks vs. OpenLakehouse

An evidence-based comparison of a managed Databricks lakehouse and an open-source lakehouse built with [OpenLakehouse](https://openlakehouse.io).

[![ci](https://github.com/pegodk/portable-lakehouse/actions/workflows/ci.yml/badge.svg)](https://github.com/pegodk/portable-lakehouse/actions/workflows/ci.yml)
[![docs](https://img.shields.io/badge/read-the-comparison-teal)](https://pegodk.github.io/portable-lakehouse/)
[![license](https://img.shields.io/badge/license-Apache--2.0-blue)](LICENSE)

This repository asks three questions:

1. Which Databricks capabilities have credible open-source counterparts?
2. Where do the experience, operations, or semantics differ?
3. Which design choices preserve future options without giving up useful managed services?

It is **not** a Databricks migration tool or a production OpenLakehouse installer. The executable workload exists to test the comparison.

## Main findings

- **The data layer is the most portable.** External Delta tables were read by Spark and DuckDB without conversion.
- **Core workload logic travels well.** 89% of measured transformation code is shared in the latest SF10 report.
- **Catalog compatibility is partial.** 6 of 10 catalog behaviours used by the workload passed against Unity Catalog OSS 0.5.0.
- **Open alternatives reproduce outcomes, not the managed experience.** Airflow, Spark, DuckDB, DataFusion, MLflow OSS, SeaweedFS, and Cedar cover useful parts of the platform, but require integration and operation.
- **Performance is inconclusive across platforms.** The committed Databricks and local OpenLakehouse results use unlike compute. They prove execution and expose engine characteristics; they do not establish which platform is faster.
- **Databricks' strongest advantage is integration.** Serverless compute, elastic operations, governance, lineage, BI, and platform-wide user experience are not reproduced by assembling the tested OSS stack.

## Open-source capability map

| Databricks capability | Open approach tested or assessed |
|---|---|
| Delta Lake | Delta Lake OSS 4.3.1 |
| Databricks Runtime / Spark | Apache Spark 4.1.0 |
| Databricks SQL | Spark SQL, DuckDB, DataFusion |
| Unity Catalog | Unity Catalog OSS 0.5.0 |
| Lakeflow Jobs | Apache Airflow 3.1.6 |
| Managed MLflow | MLflow OSS 3.14 |
| Cloud object storage | SeaweedFS S3 for the local reference environment |
| Fine-grained policy decisions | Cedar with a DataFusion enforcement prototype |

Read the [comparison](https://pegodk.github.io/portable-lakehouse/comparison/), [latest evidence](https://pegodk.github.io/portable-lakehouse/report/), and [portability principles](https://pegodk.github.io/portable-lakehouse/portability-principles/).

## Scope and limits

The executable comparison covers TPC-H batch SQL, Delta tables, an SCD2 merge, catalog behaviour, orchestration structure, MLflow tracking, and a small governance prototype. Broader platform coverage is a curated assessment and is labelled as documented or planned rather than measured.

The single 62% portability score is only an index over four measured ratios. Read its components; it is not a claim that the platforms are 62% equivalent.

Technical instructions for reproducing the evidence remain in [docs/reproduce.md](docs/reproduce.md).

## Principles

Own the data; separate business logic from platform logic; prefer open interfaces; isolate managed dependencies; test portability; do not confuse portability with equivalence; and allow managed services to be better.

## License

[Apache License 2.0](LICENSE). This independent project is not affiliated with or endorsed by Databricks or OpenLakehouse.

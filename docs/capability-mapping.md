# Capability mapping

How each Databricks capability used by this workload maps to OpenLakehouse. The source of truth is
[`freedom/assessment/capabilities.yaml`](../freedom/assessment/capabilities.yaml). The Freedom Report
renders it next to the live catalog probe, and `tests/portability/test_docs.py` keeps this page in sync.

| Classification | Meaning |
|---|---|
| **PORTABLE** | Runs unchanged on OpenLakehouse |
| **ADAPTABLE** | Small, mechanical change: configuration, or swapping one idiom for another |
| **REWRITE** | The same outcome is reachable, but the code has to be rewritten |
| **PLATFORM-SPECIFIC** | A managed capability with no drop-in open equivalent in this stack |

Evidence `measured:<x>` is checked on every run (Freedom Check key, catalog probe item,
benchmark). `documented` is a reasoned statement that is not tested automatically.

| Capability | Databricks | OpenLakehouse | Classification | Evidence |
|---|---|---|---|---|
| Table format | Delta Lake (Databricks Runtime) | Delta Lake 4.3.1 (delta-spark), delta-kernel-rs (DuckDB and DataFusion) | **PORTABLE** | measured:delta_readable |
| Batch compute | Apache Spark on serverless or classic compute (Photon optional) | Apache Spark 4.1.0 standalone, clients via Spark Connect | **PORTABLE** | measured:spark_executable |
| SQL analytics | Databricks SQL / Spark SQL | Spark SQL; DuckDB and DataFusion for single-node analytics | **PORTABLE** | measured:tpch_results |
| DataFrame transformations | PySpark DataFrame API | PySpark DataFrame API over Spark Connect | **PORTABLE** | measured:transformations |
| Incremental upserts / SCD2 | Delta MERGE INTO | Delta MERGE INTO (OSS Delta) | **PORTABLE** | measured:scd2 |
| Full refresh of an external table | CREATE OR REPLACE TABLE ... LOCATION ... AS SELECT | create once, then INSERT OVERWRITE | **ADAPTABLE** | measured:delta_io |
| Table and column metadata changes | ALTER TABLE ... SET TBLPROPERTIES / COMMENT | set comments and properties at creation time | **ADAPTABLE** | measured:catalog_probe.alter_metadata |
| Catalog (namespaces, external tables, volumes) | Unity Catalog | Unity Catalog OSS 0.5.0 | **ADAPTABLE** | measured:catalog_probe |
| Access control | Unity Catalog grants, row filters, column masks | UC OSS metadata and grants; Cedar decisions; DataFusion enforcement foundation | **PLATFORM-SPECIFIC** | measured:catalog_probe.grants |
| Non-Spark engine access through the catalog | credential vending to DuckDB, Trino, ... (UC external access) | UC OSS resolves the location; DuckDB reads with its own S3 secret | **ADAPTABLE** | measured:duckdb_access |
| Raw file landing | Unity Catalog Volumes (/Volumes FUSE path) | S3 prefix on SeaweedFS (UC OSS volumes exist as metadata) | **ADAPTABLE** | measured:spark_executable |
| Orchestration | Lakeflow Jobs (Workflows) defined in an Asset Bundle | Apache Airflow 3.1.6 DAG generated from the same task graph | **ADAPTABLE** | measured:orchestration |
| Deployment | Databricks Asset Bundles | Docker Compose (OpenLakehouse) plus scripts in platforms/openlakehouse | **PLATFORM-SPECIFIC** | documented |
| Elastic, managed compute | Serverless compute, autoscaling, Photon | Fixed-size Spark standalone cluster you operate | **PLATFORM-SPECIFIC** | documented |
| Table maintenance | Predictive optimization, auto compaction | Scheduled OPTIMIZE / VACUUM (supported by OSS Delta) | **ADAPTABLE** | documented |
| Lineage, audit and system tables | Unity Catalog lineage, system tables | OpenLineage (not part of v1) | **PLATFORM-SPECIFIC** | documented |

## Notes

- **Table format.** Tables are re-registered from their _delta_log and read without conversion.
- **Batch compute.** Same PySpark code; only session creation differs (entrypoint.py).
- **Full refresh of an external table.** The UC OSS 0.5 Spark connector rejects CREATE OR REPLACE with a location. The INSERT OVERWRITE idiom works on both platforms and is what the shared code uses.
- **Catalog (namespaces, external tables, volumes).** Catalogs, schemas, external Delta tables, comments and volumes recreate. Column metadata and custom properties of Spark-created tables are not stored by UC OSS; registering through the REST API keeps them.
- **Access control.** OpenLakehouse ships with authorization disabled; grants are not stored. Freedom Challenge #4 adds a Cedar decision contract and makes DataFusion the reference enforcement point; end-to-end gateway enforcement remains to be measured.
- **Non-Spark engine access through the catalog.** UC OSS vends credentials without an S3 endpoint, so DuckDB's unity_catalog extension sends requests to AWS instead of SeaweedFS. Location lookup through the catalog plus delta_scan works.
- **Raw file landing.** The path is configuration (FreedomConfig.raw_root); the generator handles both.
- **Orchestration.** The task graph is shared; each scheduler definition is platform code. The Airflow DAG is checked for consistency but not executed in v1.
- **Elastic, managed compute.** Principle F6. This is where the managed platform earns its keep; the benchmark section shows the effect when comparable compute is used.
- **Lineage, audit and system tables.** Freedom Challenge

## Not covered by v1

Capabilities outside Freedom Challenge #1 (streaming, declarative pipelines, governance, ML, BI, AI, observability) are listed on the [Freedom Challenges](freedom-challenges.md) page.

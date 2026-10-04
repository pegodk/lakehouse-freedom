# Comparison

## What is being compared

The same TPC-H batch workload runs on two reference architectures:

| | Layer | Databricks | OpenLakehouse reference |
|---|---|---|---|
| <img class="tech-icon" src="assets/icons/delta-lake.svg" alt="Delta Lake"> | Storage format | Delta Lake | Delta Lake OSS 4.3.1 |
| <img class="tech-icon" src="assets/icons/apache-spark.svg" alt="Apache Spark"> | Compute | Databricks Runtime, serverless Spark | Apache Spark 4.1.0 and Spark Connect |
| <img class="tech-icon" src="assets/icons/duckdb.svg" alt="DuckDB"> <img class="tech-icon" src="assets/icons/datafusion.svg" alt="Apache DataFusion"> | Additional engines | — | DuckDB and Apache DataFusion |
| <img class="tech-icon tech-icon-wide" src="assets/icons/unity-catalog.png" alt="Unity Catalog"> | Catalog | Managed Unity Catalog | Unity Catalog OSS 0.5.0 |
| <img class="tech-icon" src="assets/icons/apache-airflow.svg" alt="Apache Airflow"> | Orchestration | Lakeflow Jobs | Apache Airflow 3.1.6 |
| <img class="tech-icon" src="assets/icons/mlflow.svg" alt="MLflow"> | ML tracking | Managed MLflow | MLflow OSS 3.14 |
| <img class="tech-icon" src="assets/icons/seaweedfs.svg" alt="SeaweedFS"> <img class="tech-icon" src="assets/icons/postgresql.svg" alt="PostgreSQL"> | Storage services | Cloud external location and managed metadata | SeaweedFS S3 and PostgreSQL in the local test environment |
| <img class="tech-icon" src="assets/icons/cedar.png" alt="Cedar"> | Governance | Integrated platform controls | UC OSS metadata plus a Cedar/DataFusion prototype |
| <img class="tech-icon" src="assets/icons/python.svg" alt="Python"> | Workload language | Python wheel | The same Python wheel |

The workload includes Raw-to-Bronze-to-Silver-to-Gold transformations, all 22 TPC-H queries, data-quality checks, and an incremental SCD2 merge.

## Findings by layer

### Data and transactions: closest match

Delta Lake provided the strongest common foundation. External tables, schema enforcement, reads, and `MERGE` worked in the tested workload. Databricks-only managed features such as liquid clustering and predictive optimization still change the operational picture.

### Compute and SQL: compatible core, different service

The PySpark transformations and canonical TPC-H SQL ran on both Spark environments. DuckDB also read the same Delta tables and returned the expected query results. The open stack does not reproduce Databricks serverless provisioning, Photon, compute policies, or managed upgrades.

### Catalog and governance: useful but incomplete

Unity Catalog OSS recreated catalogs, schemas, external tables, comments, REST registration, and volumes in the tested configuration. Spark-created column metadata, custom properties, `ALTER TABLE`, and grants did not pass the probe. Databricks fine-grained governance, lineage, audit, identity integration, and workspace isolation have no equivalent integrated experience here.

### Orchestration and deployment: replaceable, not interchangeable

Airflow can represent the same task graph, and Python wheels plus Compose can deploy the open implementation. This replaces outcomes, not semantics or operations: compute lifecycle, identities, state, and upgrades cross several independently operated services.

### ML, BI, and AI: APIs travel further than services

MLflow tracking uses the same public API with a different backend. Managed registry governance, feature engineering, serving, BI, vector search, and agent services either need separate products or remain gaps in this repository.

## SQL compatibility

All 22 canonical TPC-H queries completed with the expected results in the committed Databricks Spark, OpenLakehouse Spark, and DuckDB runs. No engine-specific SQL variants were needed for those runs. DataFusion remains unmeasured at SF10.

This evidence covers a conservative analytical SQL workload. It establishes compatibility for the tested queries, not universal SQL dialect parity.

## What the comparison means

| If you value... | The evidence suggests... |
|---|---|
| Integrated governance and operations | Databricks has the stronger tested architecture. |
| Control of data and infrastructure | The open architecture provides more ownership, with more operational responsibility. |
| Reusable batch transformations | Spark, Delta, and disciplined boundaries preserve substantial portability. |
| Best-of-breed engine choice | Open tables allow additional engines such as DuckDB and DataFusion. |
| Drop-in platform equivalence | Neither the evidence nor this project supports that expectation. |

See [capability coverage](platform-capability-coverage.md) for the broad matrix and the [latest report](report.md) for every measured detail.

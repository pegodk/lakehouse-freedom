# OpenLakehouse reference

<img class="page-mark page-mark-round" src="../assets/icons/openlakehouse.jpg" alt="OpenLakehouse">

OpenLakehouse is the open-source side of the comparison. The repository pins an OpenLakehouse release and uses its components to reproduce selected Databricks outcomes.

| | Component | Role in this comparison |
|---|---|---|
| <img class="tech-icon" src="../assets/icons/apache-spark.svg" alt="Apache Spark"> | Apache Spark 4.1.0 | Shared transformations and SQL through Spark Connect |
| <img class="tech-icon" src="../assets/icons/delta-lake.svg" alt="Delta Lake"> | Delta Lake 4.3.1 | Table format and transactions |
| <img class="tech-icon tech-icon-wide" src="../assets/icons/unity-catalog.png" alt="Unity Catalog"> | Unity Catalog OSS 0.5.0 | Catalog and metadata |
| <img class="tech-icon" src="../assets/icons/duckdb.svg" alt="DuckDB"> | DuckDB 1.5.6 | Independent analytics and result validation |
| <img class="tech-icon" src="../assets/icons/datafusion.svg" alt="Apache DataFusion"> | DataFusion | Additional engine and governance-enforcement prototype |
| <img class="tech-icon" src="../assets/icons/apache-airflow.svg" alt="Apache Airflow"> | Apache Airflow 3.1.6 | Alternative workflow orchestrator |
| <img class="tech-icon" src="../assets/icons/seaweedfs.svg" alt="SeaweedFS"> | SeaweedFS | Local S3-compatible object storage |
| <img class="tech-icon" src="../assets/icons/postgresql.svg" alt="PostgreSQL"> | PostgreSQL | Service metadata storage |
| <img class="tech-icon" src="../assets/icons/mlflow.svg" alt="MLflow"> | MLflow OSS | Open experiment-tracking counterpart |

## Interpretation

The stack shows that open components can reproduce much of the core data workload and many platform outcomes. It does not provide a drop-in Databricks replacement. The operator must integrate identities, credentials, policy enforcement, observability, scaling, upgrades, backups, and service reliability.

SeaweedFS and the single-node Spark deployment are test-environment choices, not recommendations for production architecture. See [Reproducing the evidence](../reproduce.md) only if you need to run the comparison.

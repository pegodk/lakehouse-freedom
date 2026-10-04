# OpenLakehouse reference

OpenLakehouse is the open-source side of the comparison. The repository pins an OpenLakehouse release and uses its components to reproduce selected Databricks outcomes.

| Component | Role in this comparison |
|---|---|
| Apache Spark 4.1.0 | Shared transformations and SQL through Spark Connect |
| Delta Lake 4.3.1 | Table format and transactions |
| Unity Catalog OSS 0.5.0 | Catalog and metadata |
| DuckDB 1.5.6 | Independent analytics and result validation |
| DataFusion | Additional engine and governance-enforcement prototype |
| Apache Airflow 3.1.6 | Alternative workflow orchestrator |
| SeaweedFS | Local S3-compatible object storage |
| PostgreSQL | Service metadata storage |
| MLflow OSS | Open experiment-tracking counterpart |

## Interpretation

The stack shows that open components can reproduce much of the core data workload and many platform outcomes. It does not provide a drop-in Databricks replacement. The operator must integrate identities, credentials, policy enforcement, observability, scaling, upgrades, backups, and service reliability.

SeaweedFS and the single-node Spark deployment are test-environment choices, not recommendations for production architecture. See [Reproducing the evidence](../reproduce.md) only if you need to run the comparison.

# Portability Challenges

v1 of Portable Lakehouse is **Portability Challenge #1**. Each later challenge asks the same question of one more Databricks capability:

> How much of this capability remains portable, and what is required to reproduce it using the open lakehouse ecosystem?

| # | Challenge | Databricks capability | Open counterpart to measure | Status |
|---|---|---|---|---|
| 1 | TPC-H / SQL / Delta | Spark, Delta Lake, Databricks SQL, Unity Catalog | Spark 4.1, Delta 4.3.1, DuckDB, DataFusion, UC OSS 0.5.0 | **v1 + DataFusion** |
| 2 | Streaming + Auto Loader | Auto Loader, Structured Streaming | Structured Streaming file source; Kafka (in OpenLakehouse) | planned |
| 3 | Lakeflow Declarative Pipelines | `dlt`, streaming tables, materialized views | Spark Declarative Pipelines (Spark 4.1, in OpenLakehouse) | planned |
| 4 | Unity Catalog governance | grants, row filters, column masks, tags | UC OSS metadata, Cedar decisions, DataFusion enforcement | foundation |
| 5 | MLflow / ML workloads | Managed MLflow, Model Serving | MLflow 3.14 (in OpenLakehouse) | tracking foundation |
| 6 | Databricks SQL / BI | SQL warehouses, dashboards | Spark Connect / Thrift, DuckDB, open BI tools | planned |
| 7 | AI / Vector Search / Agents | AI functions, Vector Search, Agent Framework | open models, vector stores, MLflow tracing | planned |
| 8 | Observability | system tables, lineage | OpenLineage, Spark event logs | planned |
| 9 | Disaster recovery | managed DR | Backup and restore validation against a replicated bucket | not implemented |

## How a challenge plugs in

The v1 building blocks are meant to take new challenges without changing the existing ones:

| Building block | Extend with |
|---|---|
| Task graph (`src/common/pipeline.py`) | new tasks; both orchestrators pick them up |
| Inventory (`portability/assessment/inventory.yaml`) | new files in their portability group |
| Scanner (`portability/assessment/scanner.py`) | rules for the capability's Databricks-specific constructs |
| Capability mapping (`portability/assessment/capabilities.yaml`) | rows with classification and evidence |
| Portability Check (`portability/validation/check.py`) | checks with PASS / FAIL / SKIP and evidence |
| Portability Score (`portability/reporting/score.py`) | a component with a formula over measured counts |

# Architectures compared

Both architectures run the same workload and produce external Delta tables with matching names.

```text
TPC-H data -> Bronze -> Silver -> Gold -> 22 SQL queries
                              \-> quality checks
Change feed -------------------> SCD2 merge
```

| Concern | Shared choice | Databricks | OpenLakehouse |
|---|---|---|---|
| Data | External Delta tables | Cloud object storage | SeaweedFS S3 in the local test |
| Transformations | PySpark and Spark SQL | Databricks Runtime | Apache Spark via Spark Connect |
| Catalog | Matching three-part names | Managed Unity Catalog | Unity Catalog OSS |
| Analytics | Canonical TPC-H SQL | Databricks Spark | Spark, DuckDB, DataFusion |
| Scheduling | One logical task graph | Lakeflow Jobs | Airflow DAG |
| Packaging | One Python wheel | Asset Bundle | Python package and Compose |

## Why this structure matters

Business transformations receive a Spark session and configuration; they do not select a platform. Storage paths, credentials, session creation, and scheduling stay in platform adapters. This boundary makes shared logic measurable and exposes the parts that really depend on a platform.

The comparison also uses independent checks. DuckDB recomputes table and Gold results, while a plain-Python implementation validates the SCD2 scenario. Agreement is therefore stronger evidence than running the same implementation twice.

## Important differences

Matching the task graph does not make the architectures equivalent. Databricks supplies an integrated control plane, managed compute, identity, governance, and operations. The open architecture assembles separate services, and its operator owns their integration, security, scaling, upgrades, and recovery.

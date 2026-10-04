# Portability Principles

Seven principles for treating portability as a design objective. Each one explains how this repository applies the principle and what evidence is collected.

## P1: Own the data

Business data lives in an open table format on object storage you control. Delta Lake is the format for v1.

**In this repository.** Every Bronze, Silver and Gold table is an *external* Delta table under a `table_root` you choose (`LakehouseConfig.table_root`; on Databricks the `table_root` bundle variable, typically an `abfss://` or `s3://` external location). The catalog holds pointers, and the bytes stay where you put them.

External tables keep storage layout and ownership explicit, making the two implementations easier to compare and the data accessible to additional engines.

**Checked by.** The Portability Check reads the Delta tables through OpenLakehouse Spark and independently through DuckDB.

## P2: Separate business logic from platform logic

Transformations contain as little platform-specific code as reasonably possible.

```python
def conform(df: DataFrame, table: str) -> DataFrame:          # src/transformations/silver.py
    return df.select(*[F.col(c).cast(t).alias(c) for c, t in TPCH_SCHEMA[table]])
```

Session creation, paths, catalog names, compute sizing and scheduling live in `platforms/<name>/`. The shared code receives a `SparkSession` and a `LakehouseConfig` and never asks which platform it is on.

**Checked by.** `portability/assessment/inventory.yaml` assigns every workload file to `shared`, `databricks` or `openlakehouse`; the Portability Report turns that into lines-of-code ratios. `tests/portability/test_inventory.py` fails if a new file is not classified.

## P3: Prefer open interfaces

Where practical, use Apache Spark (SQL and DataFrame API), Delta Lake SQL, the Unity Catalog REST API, MLflow APIs and object-storage APIs inside business logic. Proprietary interfaces remain valid choices when their benefits justify the dependency.

**In this repository.** The shared code uses Spark SQL, the PySpark DataFrame API, Delta `MERGE`, `INSERT OVERWRITE` and `CREATE TABLE ... LOCATION`. Catalog metadata is read through `/api/2.1/unity-catalog`, which Databricks and UC OSS both serve.

**Checked by.** `portability/assessment/scanner.py` has 21 rules for Databricks-specific constructs (`dbutils`, Auto Loader, `dlt`, `/Volumes/` paths, AI functions, `spark.databricks.*` configuration, and more). The Portability Check fails if any shared file matches.

## P4: Isolate managed capabilities

Using Databricks-specific functionality is fine. Make the dependency visible and keep it in one place, so the capability and its open alternative can be compared directly.

**In this repository.** `platforms/databricks/entrypoint.py` is the Databricks-specific Python adapter. It reads cluster tags for the benchmark record, an intentional use that the scanner reports as `PLATFORM-SPECIFIC`. `portable-lakehouse assess <path>` applies the same assessment rules to another repository.

## P5: Portability must be tested

Open-source components alone do not establish portability. Evidence comes from executing the workload in another environment and comparing its behavior and results.

**In this repository.** Evidence comes from separate DuckDB and Python reference implementations, catalog probes, workload fingerprints and orchestration comparisons. These checks support claims for the tested workload and environments; they are not universal guarantees.

## P6: Portability does not mean equivalence

The open implementation does not need to reproduce every Databricks capability. The Portability Report distinguishes reusable data and business logic from capabilities that require adaptation, reimplementation, or remain platform-specific.

## P7: Managed services are allowed to be better

The objective is not to show that an open-source stack is superior to Databricks. Managed services may offer better performance, operations, developer experience, governance, autoscaling and observability. Portability means making architectural options and dependencies visible, not producing identical platforms.

**In this repository.** The capability mapping marks serverless compute, governance (grants, masks, row filters), lineage and system tables as `PLATFORM-SPECIFIC`. The catalog probe shows exactly which Unity Catalog behaviours UC OSS 0.5.0 does not reproduce. The benchmark refuses to rank platforms on unlike hardware.

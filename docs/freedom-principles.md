# Freedom Principles

Six principles for building on Databricks while keeping a practical path to an open-source lakehouse. Each one says what to do, how this repository applies it, and how the repository checks that it holds. A principle that cannot be checked is only an aspiration, which is why F5 exists.

## F1: Own the data

Business data lives in an open table format on object storage you control. Delta Lake is the format for v1.

**In this repository.** Every Bronze, Silver and Gold table is an *external* Delta table under a `table_root` you choose (`FreedomConfig.table_root`; on Databricks the `table_root` bundle variable, typically an `abfss://` or `s3://` external location). The catalog holds pointers, and the bytes stay where you put them.

External tables keep storage layout and ownership explicit, making the two implementations easier to compare and the data accessible to additional engines.

**Checked by.** The Freedom Check reads the Delta tables through OpenLakehouse Spark and independently through DuckDB.

## F2: Separate business logic from platform logic

Transformations contain as little platform-specific code as reasonably possible.

```python
def conform(df: DataFrame, table: str) -> DataFrame:          # src/transformations/silver.py
    return df.select(*[F.col(c).cast(t).alias(c) for c, t in TPCH_SCHEMA[table]])
```

Session creation, paths, catalog names, compute sizing and scheduling live in `platforms/<name>/`. The shared code receives a `SparkSession` and a `FreedomConfig` and never asks which platform it is on.

**Checked by.** `freedom/assessment/inventory.yaml` assigns every workload file to `shared`, `databricks` or `openlakehouse`; the Freedom Report turns that into lines-of-code ratios. `tests/portability/test_inventory.py` fails if a new file is not classified.

## F3: Prefer open interfaces

Inside business logic, use Apache Spark (SQL and DataFrame API), Delta Lake SQL, the Unity Catalog REST API, MLflow APIs and object-storage APIs, rather than proprietary interfaces.

**In this repository.** The shared code uses Spark SQL, the PySpark DataFrame API, Delta `MERGE`, `INSERT OVERWRITE` and `CREATE TABLE ... LOCATION`. Catalog metadata is read through `/api/2.1/unity-catalog`, which Databricks and UC OSS both serve.

**Checked by.** `freedom/assessment/scanner.py` has 21 rules for Databricks-specific constructs (`dbutils`, Auto Loader, `dlt`, `/Volumes/` paths, AI functions, `spark.databricks.*` configuration, and more). The Freedom Check fails if any shared file matches.

## F4: Isolate managed capabilities

Using Databricks-specific functionality is fine. Make the dependency visible and keep it in one place, so its migration cost can be read off the repository.

**In this repository.** `platforms/databricks/entrypoint.py` (42 logical lines) is the only Databricks-specific Python. It reads cluster tags for the benchmark record, which is a legitimate use that the scanner reports as `PLATFORM-SPECIFIC`. `freedom assess <path>` runs the same scanner over any repository.

## F5: Portability must be tested

A workload is not portable because its components are open source. It is portable when it has been run somewhere else and produced the same answers.

**In this repository.** `make freedom-check` runs 13 checks across the reference implementations: tables readable, schemas, row counts and keys, transformation output against an independent DuckDB oracle, TPC-H answers, Unity Catalog metadata, DuckDB access, incremental loads, SCD2 against a pure-Python oracle, shared-code scan, orchestration consistency and the Databricks reference run. Failures are reported as failures. No check falls back to a platform-specific workaround.

## F6: Managed services are allowed to be better

The open implementation does not need to match every Databricks capability or its performance. Freedom means having an alternative, and the alternative does not have to be identical.

**In this repository.** The capability mapping marks serverless compute, governance (grants, masks, row filters), lineage and system tables as `PLATFORM-SPECIFIC`. The catalog probe shows exactly which Unity Catalog behaviours UC OSS 0.5.0 does not reproduce. The benchmark refuses to rank platforms on unlike hardware.

# Freedom Architecture

The recommended way to structure a Databricks workload so that it can also run on OpenLakehouse. This repository is a working instance of it.

## Layers

```
                      TPC-H dbgen (DuckDB tpch extension)
                                   │  Parquet
                                   ▼
   Raw      <raw_root>/<sf>/<table>/part-NNNNN.parquet
            Databricks: /Volumes/freedom/landing/raw     OpenLakehouse: s3://lakehouse/freedom/raw
                                   │  spark.read.parquet + lineage columns
                                   ▼
   Bronze   freedom.tpch_<sf>_bronze.<table>    external Delta, _source_file/_batch_id/_ingested_at
                                   │  conform(): canonical TPC-H types, trimmed strings
                                   ▼
   Silver   freedom.tpch_<sf>.<table>           external Delta, TPC-H v3 schema
                                   │  DataFrame API aggregate         TPC-H queries 1-22
                                   ▼                                         │
   Gold     freedom.tpch_<sf>_gold.revenue_by_nation_year                   ▼
                                                                  benchmarks/results/

   Incremental  freedom.incremental.customer_changes  ──MERGE──►  freedom.incremental.customer_scd2
```

Table names are identical on both platforms. On Databricks, `freedom` is a Unity Catalog catalog. On OpenLakehouse it is a Unity Catalog OSS catalog of the same name, exposed to Spark through `io.unitycatalog.spark.UCSingleCatalog` (`platforms/openlakehouse/config/spark-defaults.freedom.conf`).

## Shared code and platform code

```
src/                       shared   ingestion, transformations, quality, config, task dispatch
tpch/                      shared   generator, 22 canonical queries, reference answers
benchmarks/runner/         shared   query runner and engines
platforms/databricks/      Databricks   entrypoint.py, Asset Bundle, job definition
platforms/openlakehouse/   OpenLakehouse adapter.py, entrypoint.py, catalog.py, Airflow DAG,
                                        config overlay, stack scripts, pinned submodule
freedom/                   tooling  assessment, validation and reporting
```

The contract between the two halves is small:

| Platform supplies | Example (Databricks) | Example (OpenLakehouse) |
|---|---|---|
| a `SparkSession` | `SparkSession.builder.getOrCreate()` | `SparkSession.builder.remote("sc://localhost:15002")` |
| `raw_root` | `/Volumes/freedom/landing/raw` | `s3://lakehouse/freedom/raw` |
| `table_root` | `abfss://…/freedom` (external location) | `s3://lakehouse/freedom/tables` |
| `results_root` | `/Volumes/freedom/landing/results` | `./benchmarks/results` |
| storage setup for DuckDB | none (FUSE path) | S3 secret for SeaweedFS |
| orchestration | Lakeflow Jobs via Asset Bundle | Airflow DAG / Makefile |

Everything else is `run_task(spark, cfg, key)` in `src/run.py`.

## One task graph

`src/common/pipeline.py` defines the pipeline once:

```
generate ──► bronze ──► silver ──► gold ──► quality ──► tpch_queries
incremental
```

The Databricks job (`platforms/databricks/resources/lakehouse_freedom.job.yml`) and the Airflow DAG (`platforms/openlakehouse/airflow/dags/lakehouse_freedom.py`) both implement it. The DAG is generated from the graph at parse time. The job YAML is written by hand, because Asset Bundles want static YAML, and a test fails if it drifts from the graph.

## Portable write idioms

These idioms work on Databricks Unity Catalog and on the UC OSS 0.5 Spark connector (`src/common/delta_io.py`):

| Need | Use | Avoid (fails on UC OSS 0.5) |
|---|---|---|
| first write | `CREATE TABLE … USING DELTA LOCATION … COMMENT … TBLPROPERTIES … AS SELECT` | |
| full refresh | `INSERT OVERWRITE` | `CREATE OR REPLACE TABLE … LOCATION` |
| incremental | `MERGE INTO` | |
| metadata | comments and properties at creation | `ALTER TABLE … SET TBLPROPERTIES`, `COMMENT ON` |
| statistics | rely on Delta file statistics | `ANALYZE TABLE` |

## Determinism

Equivalence across platforms needs deterministic outputs. The generator is deterministic for a given scale factor. The SCD2 scenario takes validity dates from the data, never from the clock. Lineage columns that legitimately differ per run (`_ingested_at`, `_batch_id`, `_source_file`) start with an underscore and are excluded from fingerprints.

Fingerprints (`src/quality/checks.py`) are `count(*)` plus `sum(xxhash64(all columns))` cast to `DECIMAL(38,0)`, so they cannot overflow under ANSI mode. They match on any engine that implements Spark's `xxhash64` (seed 42) identically. Databricks Runtime is expected to, and the Freedom Check compares the two whenever Databricks results are present, so a mismatch would show up as a failed check rather than go unnoticed.

## Two independent oracles

A check that reuses the code it checks proves little. Two oracles share no code with the Spark pipeline:

* **DuckDB.** `freedom/validation/check.py` profiles every Silver table read through `delta_scan` against the same profile computed from the Raw Parquet with DuckDB SQL, and recomputes the Gold aggregate in DuckDB SQL.
* **Python.** `freedom/validation/scd2_reference.py` replays the change feed in plain Python. The committed `tests/data/scd2_expected.json` is its output.

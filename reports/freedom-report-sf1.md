# 🗽 Lakehouse Freedom Report

Scale factor **1** (`sf1`) · generated 2026-10-03 22:17 UTC by `make freedom-report SCALE=1`

> **Scope of this report.** The Databricks side of the workload has not been run for this scale factor, so every comparison below uses the OpenLakehouse run, the official TPC-H answers (where they exist) and independent DuckDB oracles. Databricks columns are marked *not run*. Run the bundle in `platforms/databricks/` and `make databricks-fetch-results` to complete it.

## 1. Architecture tested

```
                 TPC-H dbgen (DuckDB) ──► Raw Parquet
                                           │
                         Bronze ──► Silver ──► Gold   (Delta, external tables)
                                           │
          ┌────────────────────────────────┴───────────────────────────────┐
          ▼                                                                ▼
   Databricks                                                     OpenLakehouse
   Spark · Delta · Unity Catalog · Workflows · Bundles            Spark Connect · Delta · UC OSS
                                                                  DuckDB · Airflow · SeaweedFS
```

| Platform | Role | Status for this report |
|---|---|---|
| Databricks | Managed implementation (bundle in `platforms/databricks`) | not run |
| OpenLakehouse | Freedom implementation (`platforms/openlakehouse`) | results available |
| DuckDB on OpenLakehouse storage | Second open engine on the same Delta tables | results available |
| Freedom Day | Catalog rebuilt from storage only | passed |

## 2. Software versions

| Component | Version |
|---|---|
| OpenLakehouse | [77f9ebb214](https://github.com/open-lakehouse/open-lakehouse) |
| Apache Spark | 4.1.0 |
| Spark image | 4.1.0-scala2.13-java21-python3-r-ubuntu |
| Delta Lake (delta-spark) | 4.3.1 |
| Unity Catalog OSS server | v0.5.0 |
| Unity Catalog Spark connector | 0.4.1 |
| SeaweedFS (S3) | 3.80 |
| DuckDB | 1.5.6 |
| TPC-H generator | duckdb tpch extension (embedded TPC-H dbgen), tpch extension v1.5.6 |

OpenLakehouse compute: Spark standalone: 1 master, 1 worker, Spark Connect server, all on one host; executor 6 cores / 7g, driver 2g; host 8 CPUs, 13.6 GB RAM, Linux 7.2.5-3-omarchy.

## 3. Dataset scale

TPC-H SF1, generated in 1 chunk(s) in 14 s.

| Table | Rows | Expected (dbgen) | Primary key unique |
|---|---|---|---|
| region | 5 | 5 | yes |
| nation | 25 | 25 | yes |
| supplier | 10,000 | 10,000 | yes |
| customer | 150,000 | 150,000 | yes |
| part | 200,000 | 200,000 | yes |
| partsupp | 800,000 | 800,000 | yes |
| orders | 1,500,000 | 1,500,000 | yes |
| lineitem | 6,001,215 | 6,001,215 | yes |

## 4. Portability results (Freedom Check)

| Check | Status | Evidence |
|---|---|---|
| Delta tables readable | PASS | 19/19 tables read by Spark 4.1.0 through UC OSS |
| Schemas compatible | PASS | 8/8 Silver tables match the canonical TPC-H schema; Databricks schemas not available |
| Expected row counts and keys | PASS | dbgen row counts, primary keys and 7 foreign keys hold |
| Transformation outputs equivalent | PASS | Silver equals DuckDB's independent conform of Raw for 8/8 tables; Gold equals DuckDB SQL oracle: True; Databricks fingerprints not available |
| TPC-H results equivalent | PASS | openlakehouse/spark: 22/22 correct vs TPC-H answers (DuckDB tpch_answers); openlakehouse/duckdb: 22/22 correct vs TPC-H answers (DuckDB tpch_answers); databricks/spark: not run |
| Spark transformations executable | PASS | pipeline tasks ['generate', 'bronze', 'silver', 'gold', 'quality', 'incremental', 'tpch_queries'] completed on OpenLakehouse Spark; 22/22 queries ran |
| Unity Catalog metadata accessible/recreated | PASS | UC OSS lists 8 Silver tables with DELTA format and storage location; catalog probe: 6/10 Databricks UC capabilities recreated (gaps: spark_columns, spark_properties, alter_metadata, grants) |
| DuckDB can access selected tables | PASS | DuckDB 1.5.6 read lineitem (6,001,215 rows) via UC OSS-resolved location s3://lakehouse/freedom/tables/tpch_sf1/lineitem |
| Incremental pipeline works | PASS | 3 batches applied incrementally; duplicate batch refused: True; replay idempotent: True |
| SCD2 behaviour equivalent | PASS | openlakehouse: equal to the Python oracle; databricks: not run |
| Shared code has no Databricks-specific APIs | PASS | 37 shared files scanned with 21 rules; no hits |
| Orchestration matches the shared task graph | PASS | Databricks job: identical; Airflow DAG: generated from the shared graph |
| Databricks reference run available | SKIP | no Databricks results for this scale factor; see platforms/databricks/README.md |
| Freedom Day | PASS | 19/19 tables re-registered from storage and read by Spark and DuckDB; data unchanged: True (rehearsal: tables written by OSS Spark) |

**Freedom Day** (rehearsal, tables written by Apache-Spark/4.1.0 Delta-Lake/4.3.1): 19/19 tables re-registered from storage into an empty catalog and read by Spark and DuckDB; storage objects changed: none.

Delta protocol across these tables: reader version [1], writer version [2], table features ['appendOnly', 'invariants'].

## 5. TPC-H query compatibility

Canonical SQL: `tpch/queries/qNN.sql`, written for Databricks SQL / Spark SQL. A query is PORTABLE when the unchanged text runs and returns the reference result, ADAPTABLE when a small dialect change (at most 20% of lines) is needed, REWRITE for larger changes, FAILED otherwise.

| Target | Unchanged and correct | Adaptable | Rewrite | Failed | Reference |
|---|---|---|---|---|---|
| OpenLakehouse Spark | 22/22 | 0 | 0 | 0 | TPC-H answers (DuckDB tpch_answers) |
| OpenLakehouse DuckDB | 22/22 | 0 | 0 | 0 | TPC-H answers (DuckDB tpch_answers) |
| Databricks | not run |  |  |  |  |

<details markdown="1"><summary>Per-query classification</summary>

| Query | OpenLakehouse Spark | OpenLakehouse DuckDB | Databricks |
|---|---|---|---|
| q01 | PORTABLE | PORTABLE | not run |
| q02 | PORTABLE | PORTABLE | not run |
| q03 | PORTABLE | PORTABLE | not run |
| q04 | PORTABLE | PORTABLE | not run |
| q05 | PORTABLE | PORTABLE | not run |
| q06 | PORTABLE | PORTABLE | not run |
| q07 | PORTABLE | PORTABLE | not run |
| q08 | PORTABLE | PORTABLE | not run |
| q09 | PORTABLE | PORTABLE | not run |
| q10 | PORTABLE | PORTABLE | not run |
| q11 | PORTABLE | PORTABLE | not run |
| q12 | PORTABLE | PORTABLE | not run |
| q13 | PORTABLE | PORTABLE | not run |
| q14 | PORTABLE | PORTABLE | not run |
| q15 | PORTABLE | PORTABLE | not run |
| q16 | PORTABLE | PORTABLE | not run |
| q17 | PORTABLE | PORTABLE | not run |
| q18 | PORTABLE | PORTABLE | not run |
| q19 | PORTABLE | PORTABLE | not run |
| q20 | PORTABLE | PORTABLE | not run |
| q21 | PORTABLE | PORTABLE | not run |
| q22 | PORTABLE | PORTABLE | not run |

</details>

## 6. Benchmark results

> **Read this before comparing numbers.** These timings come from different kinds of compute (see environments below). A laptop running Docker is not comparable to a Databricks cluster or serverless warehouse, so these numbers show that the workload runs and roughly how long it takes in each place. They do not say which platform is faster. The primary result of this benchmark is portability (section 5).

| Query (median s) | OpenLakehouse Spark | OpenLakehouse DuckDB | Databricks |
|---|---|---|---|
| q01 | 4.57 | 0.25 | not run |
| q02 | 3.56 | 0.39 | not run |
| q03 | 2.55 | 0.25 | not run |
| q04 | 2.02 | 0.18 | not run |
| q05 | 5.10 | 0.34 | not run |
| q06 | 0.82 | 0.08 | not run |
| q07 | 4.87 | 0.38 | not run |
| q08 | 4.53 | 0.42 | not run |
| q09 | 4.57 | 0.49 | not run |
| q10 | 3.99 | 0.33 | not run |
| q11 | 2.98 | 0.25 | not run |
| q12 | 2.15 | 0.19 | not run |
| q13 | 2.97 | 0.42 | not run |
| q14 | 1.57 | 0.16 | not run |
| q15 | 2.35 | 0.11 | not run |
| q16 | 2.12 | 0.23 | not run |
| q17 | 3.37 | 0.19 | not run |
| q18 | 5.70 | 0.38 | not run |
| q19 | 1.92 | 0.23 | not run |
| q20 | 3.18 | 0.27 | not run |
| q21 | 6.62 | 0.56 | not run |
| q22 | 2.60 | 0.21 | not run |
| **total** | **74.1** | **6.3** | n/a |

- **OpenLakehouse Spark**: OpenLakehouse (local Docker); Spark standalone: 1 master, 1 worker, Spark Connect server, all on one host; repeats per query: 3; engine 4.1.0.
- **OpenLakehouse DuckDB**: OpenLakehouse (local Docker) + DuckDB in-process on the host; DuckDB in-process, all host cores; repeats per query: 3; engine 1.5.6.

## 7. Platform-specific code

| Group | Transformation LOC | Orchestration LOC | Infrastructure LOC |
|---|---|---|---|
| shared | 1385 | 29 | 0 |
| databricks | 42 | 66 | 64 |
| openlakehouse | 139 | 28 | 115 |

LOC = logical lines (no blanks, comments or docstrings). File-level detail:

<details markdown="1"><summary>Files</summary>

| File | Group | Category | LOC |
|---|---|---|---|
| `src/common/config.py` | shared | transformation | 45 |
| `src/common/delta_io.py` | shared | transformation | 47 |
| `src/common/tpch_schema.py` | shared | transformation | 117 |
| `src/ingestion/bronze.py` | shared | transformation | 28 |
| `src/ingestion/incremental.py` | shared | transformation | 54 |
| `src/transformations/gold.py` | shared | transformation | 38 |
| `src/transformations/scd2.py` | shared | transformation | 52 |
| `src/transformations/silver.py` | shared | transformation | 30 |
| `src/quality/checks.py` | shared | transformation | 56 |
| `src/run.py` | shared | transformation | 82 |
| `tpch/generator/dbgen.py` | shared | transformation | 74 |
| `tpch/sql.py` | shared | transformation | 10 |
| `tpch/queries/q01.sql` | shared | transformation | 21 |
| `tpch/queries/q02.sql` | shared | transformation | 43 |
| `tpch/queries/q03.sql` | shared | transformation | 23 |
| `tpch/queries/q04.sql` | shared | transformation | 20 |
| `tpch/queries/q05.sql` | shared | transformation | 24 |
| `tpch/queries/q06.sql` | shared | transformation | 10 |
| `tpch/queries/q07.sql` | shared | transformation | 38 |
| `tpch/queries/q08.sql` | shared | transformation | 38 |
| `tpch/queries/q09.sql` | shared | transformation | 30 |
| `tpch/queries/q10.sql` | shared | transformation | 32 |
| `tpch/queries/q11.sql` | shared | transformation | 27 |
| `tpch/queries/q12.sql` | shared | transformation | 30 |
| `tpch/queries/q13.sql` | shared | transformation | 19 |
| `tpch/queries/q14.sql` | shared | transformation | 14 |
| `tpch/queries/q15.sql` | shared | transformation | 29 |
| `tpch/queries/q16.sql` | shared | transformation | 29 |
| `tpch/queries/q17.sql` | shared | transformation | 16 |
| `tpch/queries/q18.sql` | shared | transformation | 33 |
| `tpch/queries/q19.sql` | shared | transformation | 29 |
| `tpch/queries/q20.sql` | shared | transformation | 34 |
| `tpch/queries/q21.sql` | shared | transformation | 38 |
| `tpch/queries/q22.sql` | shared | transformation | 31 |
| `benchmarks/runner/engines.py` | shared | transformation | 54 |
| `benchmarks/runner/runner.py` | shared | transformation | 90 |
| `src/common/pipeline.py` | shared | orchestration | 29 |
| `platforms/databricks/entrypoint.py` | databricks | transformation | 42 |
| `platforms/databricks/resources/lakehouse_freedom.job.yml` | databricks | orchestration | 66 |
| `platforms/databricks/databricks.yml` | databricks | infrastructure | 42 |
| `platforms/databricks/resources/landing.yml` | databricks | infrastructure | 22 |
| `platforms/openlakehouse/entrypoint.py` | openlakehouse | transformation | 24 |
| `platforms/openlakehouse/adapter.py` | openlakehouse | transformation | 103 |
| `platforms/openlakehouse/catalog.py` | openlakehouse | transformation | 12 |
| `platforms/openlakehouse/airflow/dags/lakehouse_freedom.py` | openlakehouse | orchestration | 28 |
| `platforms/openlakehouse/scripts/configure.sh` | openlakehouse | infrastructure | 31 |
| `platforms/openlakehouse/scripts/stack.sh` | openlakehouse | infrastructure | 59 |
| `platforms/openlakehouse/config/freedom.env` | openlakehouse | infrastructure | 14 |
| `platforms/openlakehouse/config/spark-defaults.freedom.conf` | openlakehouse | infrastructure | 11 |

</details>

Databricks-specific constructs found by the scanner in `platforms/databricks/`: 10 (spark_databricks_conf, volumes_path). In shared code: 0.

## 8. Capability mapping

| Capability | Databricks | OpenLakehouse | Classification | Evidence |
|---|---|---|---|---|
| Table format | Delta Lake (Databricks Runtime) | Delta Lake 4.3.1 (delta-spark), delta-kernel-rs (DuckDB) | **PORTABLE** | measured:freedom_day |
| Batch compute | Apache Spark on serverless or classic compute (Photon optional) | Apache Spark 4.1.0 standalone, clients via Spark Connect | **PORTABLE** | measured:spark_executable |
| SQL analytics | Databricks SQL / Spark SQL | Spark SQL; DuckDB for single-node analytics | **PORTABLE** | measured:tpch_results |
| DataFrame transformations | PySpark DataFrame API | PySpark DataFrame API over Spark Connect | **PORTABLE** | measured:transformations |
| Incremental upserts / SCD2 | Delta MERGE INTO | Delta MERGE INTO (OSS Delta) | **PORTABLE** | measured:scd2 |
| Full refresh of an external table | CREATE OR REPLACE TABLE ... LOCATION ... AS SELECT | create once, then INSERT OVERWRITE | **ADAPTABLE** | measured:delta_io |
| Table and column metadata changes | ALTER TABLE ... SET TBLPROPERTIES / COMMENT | set comments and properties at creation time | **ADAPTABLE** | measured:catalog_probe.alter_metadata |
| Catalog (namespaces, external tables, volumes) | Unity Catalog | Unity Catalog OSS 0.5.0 | **ADAPTABLE** | measured:catalog_probe |
| Access control | Unity Catalog grants, row filters, column masks | UC OSS permissions require server.authorization=enable plus an identity provider | **PLATFORM-SPECIFIC** | measured:catalog_probe.grants |
| Non-Spark engine access through the catalog | credential vending to DuckDB, Trino, ... (UC external access) | UC OSS resolves the location; DuckDB reads with its own S3 secret | **ADAPTABLE** | measured:duckdb_access |
| Raw file landing | Unity Catalog Volumes (/Volumes FUSE path) | S3 prefix on SeaweedFS (UC OSS volumes exist as metadata) | **ADAPTABLE** | measured:spark_executable |
| Orchestration | Lakeflow Jobs (Workflows) defined in an Asset Bundle | Apache Airflow 3.1.6 DAG generated from the same task graph | **ADAPTABLE** | measured:orchestration |
| Deployment | Databricks Asset Bundles | Docker Compose (OpenLakehouse) plus scripts in platforms/openlakehouse | **PLATFORM-SPECIFIC** | documented |
| Elastic, managed compute | Serverless compute, autoscaling, Photon | Fixed-size Spark standalone cluster you operate | **PLATFORM-SPECIFIC** | documented |
| Table maintenance | Predictive optimization, auto compaction | Scheduled OPTIMIZE / VACUUM (supported by OSS Delta) | **ADAPTABLE** | documented |
| Lineage, audit and system tables | Unity Catalog lineage, system tables | OpenLineage (not part of v1) | **PLATFORM-SPECIFIC** | documented |

Catalog probe (live, against UC OSS):

| Unity Catalog capability | Recreated | Evidence |
|---|---|---|
| Catalogs | yes | created and read back |
| Schemas | yes | created and listed |
| External Delta tables created from Spark SQL | yes | table_type=EXTERNAL, format=DELTA, location=s3://lakehouse/freedom/probe/39c64ab3/spark_created |
| Column metadata for tables created from Spark | **no** | catalog API returned 0 of 2 columns |
| Table comments set from Spark SQL | yes | catalog API comment='probe comment' |
| Custom table properties set from Spark SQL | **no** | catalog API properties={"table_type": "EXTERNAL"} |
| ALTER TABLE for comments and properties | **no** | Altering a table is not supported yet |
| Registering an existing Delta table with full column metadata | yes | 2 columns, column comment 'identifier', properties {"freedom.layer": "probe"}, Spark read 1 row(s) |
| Volumes for raw files | yes | 1 volume(s) listed |
| Grants (GRANT USE SCHEMA ... TO principal) | **no** | grant read back: []; server.authorization is 'disable' in the OpenLakehouse default config |

## 9. Known limitations

- The Databricks side was not executed for this report. SQL portability is measured against the official TPC-H answers (SF ≤ 1) or the OpenLakehouse Spark run, not against Databricks output.
- Freedom Day ran as a rehearsal on tables written by OSS Spark. Tables written by Databricks may carry additional Delta table features (for example deletion vectors or row tracking); the Freedom Day report lists the features it actually found.
- Performance numbers compare unlike compute and must not be read as a platform performance ranking.
- UC OSS runs with authorization disabled (OpenLakehouse default); grants, row filters and masks are not migrated.
- The DuckDB `unity_catalog` extension cannot read from SeaweedFS through UC OSS credential vending (vended credentials carry no S3 endpoint); DuckDB resolves locations through UC and reads with a configured S3 secret.
- The Airflow DAG is generated from the shared graph and consistency-checked, but v1 runs the OpenLakehouse pipeline from the command line rather than from Airflow.
- SQL portability is measured on TPC-H only. TPC-H uses a conservative SQL subset; real workloads using Databricks SQL extensions will score lower (use `freedom assess` to find them).
- Lines-of-code ratios measure how much code is shared, not how hard the platform-specific part is to write.

## 10. Freedom Score

```
LAKEHOUSE FREEDOM REPORT
────────────────────────────────────────────
Data portability
████████████████████  100%   (19/19)
TPC-H SQL portability (Spark)
████████████████████  100%   (22/22)
TPC-H SQL portability (DuckDB)
████████████████████  100%   (22/22)
Transformation portability
██████████████████░░   91%   (1385/1524)
Catalog portability
████████████░░░░░░░░   60%   (6/10)
Orchestration portability
██████████░░░░░░░░░░   51%   (29/57)
────────────────────────────────────────────
Freedom Score
████████████████░░░░   80%
```

| Component | Formula | Included in Freedom Score |
|---|---|---|
| Data portability | Delta tables read by OSS Spark and DuckDB after re-registration / Delta tables | yes |
| TPC-H SQL portability (Spark) | TPC-H queries running unchanged with correct results on spark / 22 | yes |
| TPC-H SQL portability (DuckDB) | TPC-H queries running unchanged with correct results on duckdb / 22 | no (additional engine) |
| Transformation portability | shared transformation LOC / (shared + OpenLakehouse-specific transformation LOC) | yes |
| Catalog portability | Unity Catalog capabilities recreated in UC OSS / capabilities used | yes |
| Orchestration portability | shared orchestration LOC / (shared + OpenLakehouse-specific orchestration LOC) | yes |

Freedom Score = unweighted mean of the included, measured components. Definitions: `freedom/reporting/score.py`.

## 11. Conclusions

**Data.** 19 of 19 Delta tables were readable by two open engines after the catalog was rebuilt from storage alone, and no stored object was rewritten. Keeping tables external, in an open format, on storage you control (F1) is what makes this possible.

**SQL.** 22 of 22 TPC-H queries ran unchanged on open-source Spark with correct results, and 22 of 22 on DuckDB. TPC-H is a conservative SQL subset, so treat this as an upper bound for real workloads.

**Code.** 91% of the code that runs the workload on OpenLakehouse is identical to the code that runs it on Databricks (1385 of 1524 LOC). The platform-specific remainder is session setup, configuration and orchestration.

**Catalog.** 6 of 10 Unity Catalog capabilities used by the workload were recreated in UC OSS. Gaps: Column metadata for tables created from Spark; Custom table properties set from Spark SQL; ALTER TABLE for comments and properties; Grants (GRANT USE SCHEMA ... TO principal). This is where a migration needs the most deliberate work, and where the managed catalog clearly adds value (F6).

**Orchestration.** Sharing the task graph keeps both schedulers aligned, but the scheduler definitions themselves are platform code (51% shared).

**Next step.** Run the Databricks bundle to replace the stand-in references with measured Databricks output, and run Freedom Day against a sync of the Databricks external location.

# 🗽 Lakehouse Freedom Report

Scale factor **10** (`sf10`) · generated 2026-10-04 00:12 UTC by `make freedom-report SCALE=10`

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

TPC-H SF10, generated in 10 chunk(s) in 204 s.

| Table | Rows | Expected (dbgen) | Primary key unique |
|---|---|---|---|
| region | 5 | 5 | yes |
| nation | 25 | 25 | yes |
| supplier | 100,000 | 100,000 | yes |
| customer | 1,500,000 | 1,500,000 | yes |
| part | 2,000,000 | 2,000,000 | yes |
| partsupp | 8,000,000 | 8,000,000 | yes |
| orders | 15,000,000 | 15,000,000 | yes |
| lineitem | 59,986,052 | 59,986,052 | yes |

## 4. Portability results (Freedom Check)

| Check | Status | Evidence |
|---|---|---|
| Delta tables readable | PASS | 19/19 tables read by Spark 4.1.0 through UC OSS |
| Schemas compatible | PASS | 8/8 Silver tables match the canonical TPC-H schema; Databricks schemas not available |
| Expected row counts and keys | PASS | dbgen row counts, primary keys and 7 foreign keys hold |
| Transformation outputs equivalent | PASS | Silver equals DuckDB's independent conform of Raw for 8/8 tables; Gold equals DuckDB SQL oracle: True; Databricks fingerprints not available |
| TPC-H results equivalent | PASS | openlakehouse/spark: 22/22 correct vs None; openlakehouse/duckdb: 22/22 correct vs openlakehouse/spark results; databricks/spark: not run |
| Spark transformations executable | PASS | pipeline tasks ['generate', 'bronze', 'silver', 'gold', 'quality', 'incremental', 'tpch_queries'] completed on OpenLakehouse Spark; 22/22 queries ran |
| Unity Catalog metadata accessible/recreated | PASS | UC OSS lists 8 Silver tables with DELTA format and storage location; catalog probe: 6/10 Databricks UC capabilities recreated (gaps: spark_columns, spark_properties, alter_metadata, grants) |
| DuckDB can access selected tables | PASS | DuckDB 1.5.6 read lineitem (59,986,052 rows) via UC OSS-resolved location s3://lakehouse/freedom/tables/tpch_sf10/lineitem |
| Incremental pipeline works | PASS | 3 batches applied incrementally; duplicate batch refused: True; replay idempotent: True |
| SCD2 behaviour equivalent | PASS | openlakehouse: equal to the Python oracle; databricks: not run |
| Shared code has no Databricks-specific APIs | PASS | 37 shared files scanned with 21 rules; no hits |
| Orchestration matches the shared task graph | PASS | Databricks job: identical; Airflow DAG: generated from the shared graph |
| Databricks reference run available | SKIP | no Databricks results for this scale factor; see platforms/databricks/README.md |

## 5. TPC-H query compatibility

Canonical SQL: `tpch/queries/qNN.sql`, written for Databricks SQL / Spark SQL. A query is PORTABLE when the unchanged text runs and returns the reference result, ADAPTABLE when a small dialect change (at most 20% of lines) is needed, REWRITE for larger changes, FAILED otherwise.

| Target | Unchanged and correct | Adaptable | Rewrite | Failed | Reference |
|---|---|---|---|---|---|
| OpenLakehouse Spark | 22/22 | 0 | 0 | 0 |  |
| OpenLakehouse DuckDB | 22/22 | 0 | 0 | 0 | openlakehouse/spark results |
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
| q01 | 51.51 | 3.47 | not run |
| q02 | 23.22 | 1.41 | not run |
| q03 | 20.21 | 2.82 | not run |
| q04 | 11.99 | 1.50 | not run |
| q05 | 29.51 | 2.97 | not run |
| q06 | 4.47 | 0.49 | not run |
| q07 | 26.24 | 1.32 | not run |
| q08 | 12.04 | 2.33 | not run |
| q09 | 23.70 | 4.58 | not run |
| q10 | 13.56 | 1.48 | not run |
| q11 | 8.61 | 0.56 | not run |
| q12 | 8.04 | 0.83 | not run |
| q13 | 13.76 | 2.88 | not run |
| q14 | 5.15 | 0.86 | not run |
| q15 | 10.57 | 0.77 | not run |
| q16 | 7.92 | 0.57 | not run |
| q17 | 26.38 | 0.88 | not run |
| q18 | 38.86 | 2.57 | not run |
| q19 | 8.25 | 1.31 | not run |
| q20 | 9.56 | 0.94 | not run |
| q21 | 41.55 | 2.82 | not run |
| q22 | 7.02 | 0.52 | not run |
| **total** | **402.1** | **37.9** | n/a |

- **OpenLakehouse Spark**: OpenLakehouse (local Docker); Spark standalone: 1 master, 1 worker, Spark Connect server, all on one host; repeats per query: 1; engine 4.1.0.
- **OpenLakehouse DuckDB**: OpenLakehouse (local Docker) + DuckDB in-process on the host; DuckDB in-process, all host cores; repeats per query: 1; engine 1.5.6.

## 7. Platform-specific code

| Group | Transformation LOC | Orchestration LOC | Infrastructure LOC |
|---|---|---|---|
| shared | 1385 | 29 | 0 |
| databricks | 42 | 66 | 64 |
| openlakehouse | 139 | 28 | 112 |

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
| `platforms/openlakehouse/config/spark-defaults.freedom.conf` | openlakehouse | infrastructure | 8 |

</details>

Databricks-specific constructs found by the scanner in `platforms/databricks/`: 10 (spark_databricks_conf, volumes_path). In shared code: 0.

## 8. Capability mapping

| Capability | Databricks | OpenLakehouse | Classification | Evidence |
|---|---|---|---|---|
| Table format | Delta Lake (Databricks Runtime) | Delta Lake 4.3.1 (delta-spark), delta-kernel-rs (DuckDB) | **PORTABLE** | measured:delta_readable |
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
| External Delta tables created from Spark SQL | yes | table_type=EXTERNAL, format=DELTA, location=s3://lakehouse/freedom/probe/43b9de8e/spark_created |
| Column metadata for tables created from Spark | **no** | catalog API returned 0 of 2 columns |
| Table comments set from Spark SQL | yes | catalog API comment='probe comment' |
| Custom table properties set from Spark SQL | **no** | catalog API properties={"table_type": "EXTERNAL"} |
| ALTER TABLE for comments and properties | **no** | Altering a table is not supported yet |
| Registering an existing Delta table with full column metadata | yes | 2 columns, column comment 'identifier', properties {"freedom.layer": "probe"}, Spark read 1 row(s) |
| Volumes for raw files | yes | 1 volume(s) listed |
| Grants (GRANT USE SCHEMA ... TO principal) | **no** | grant read back: []; server.authorization is 'disable' in the OpenLakehouse default config |

## 9. Platform capability coverage

This broader, curated comparison is separate from the Freedom Score: it includes important managed features even when this workload does not use them. Outcome coverage includes native capabilities, alternatives and workarounds; native parity counts only substantially equivalent capabilities. Matrix as of **2026-10-04**.

### Table format and transactions

`Databricks Delta Lake` → `Delta Lake OSS 4.3.1`

```
Outcome coverage  ████████████████░░░░   80%   (8/10)
Native parity     ██████████████░░░░░░   70%   (7/10)
```

Native **7** · alternatives **1** · workarounds **0** · missing **2** · not assessed **0** · workload-required coverage **3/3**

<details markdown="1"><summary>Every capability and gap</summary>

| Area | Capability | Status | Required here | Gap or alternative | Evidence |
|---|---|---|---|---|---|
| Core format | ACID transaction log | **NATIVE** | yes | — | measured:delta_readable |
| Core format | Schema enforcement and evolution | **NATIVE** | yes | — | measured:schema |
| Core format | Time travel and table history | **NATIVE** | no | — | documented |
| DML | MERGE / UPDATE / DELETE | **NATIVE** | yes | — | measured:scd2 |
| DML | Change Data Feed | **NATIVE** | no | — | documented |
| Advanced format | Deletion vectors | **NATIVE** | no | — | documented |
| Advanced format | Row tracking | **NATIVE** | no | — | documented |
| Layout | Liquid clustering | **MISSING** | no | Databricks-managed clustering is not available in this stack. | documented |
| Maintenance | Predictive optimization | **ALTERNATIVE** | no | Scheduled OPTIMIZE and VACUUM jobs. | documented |
| Transactions | Catalog-managed coordinated commits | **MISSING** | no | Open reads are validated for external Delta tables; catalog-managed commit parity is not claimed. | documented |

</details>

### Batch compute

`Databricks Runtime and serverless compute` → `Apache Spark 4.1.0 standalone`

```
Outcome coverage  ██████████████░░░░░░   70%   (7/10)
Native parity     ████████░░░░░░░░░░░░   40%   (4/10)
```

Native **4** · alternatives **1** · workarounds **2** · missing **3** · not assessed **0** · workload-required coverage **4/4**

<details markdown="1"><summary>Every capability and gap</summary>

| Area | Capability | Status | Required here | Gap or alternative | Evidence |
|---|---|---|---|---|---|
| Runtime | Spark SQL and DataFrame execution | **NATIVE** | yes | — | measured:spark_executable |
| Runtime | PySpark and Spark Connect | **NATIVE** | yes | — | measured:spark_executable |
| Runtime | Delta Lake integration | **NATIVE** | yes | — | measured:delta_readable |
| Runtime | Cluster libraries and custom code | **NATIVE** | yes | — | measured:transformations |
| Elasticity | Autoscaling workers | **WORKAROUND** | no | Requires an external cluster manager; the tested stack has fixed workers. | documented |
| Operations | Serverless provisioning | **MISSING** | no | Compute must be provisioned and operated by the user. | documented |
| Performance | Photon vectorized engine | **MISSING** | no | Photon is proprietary; Spark uses its OSS execution engine. | documented |
| Operations | Runtime-managed upgrades and patching | **MISSING** | no | Image and dependency lifecycle belongs to the operator. | documented |
| Elasticity | Spot/preemptible instance orchestration | **ALTERNATIVE** | no | Cloud or Kubernetes cluster-manager configuration. | documented |
| Governance | Managed compute policies | **WORKAROUND** | no | Must be implemented with infrastructure policy and deployment controls. | documented |

</details>

### SQL analytics

`Databricks SQL` → `Spark SQL and DuckDB`

```
Outcome coverage  ████████████████░░░░   80%   (8/10)
Native parity     ████░░░░░░░░░░░░░░░░   20%   (2/10)
```

Native **2** · alternatives **4** · workarounds **2** · missing **2** · not assessed **0** · workload-required coverage **3/3**

<details markdown="1"><summary>Every capability and gap</summary>

| Area | Capability | Status | Required here | Gap or alternative | Evidence |
|---|---|---|---|---|---|
| Query | ANSI SQL query execution | **NATIVE** | yes | — | measured:tpch_results |
| Query | Delta table queries | **NATIVE** | yes | — | measured:tpch_results |
| Connectivity | JDBC/ODBC connectivity | **ALTERNATIVE** | no | Spark Thrift Server or a compatible query service. | documented |
| Query | Multi-engine local analytics | **ALTERNATIVE** | yes | DuckDB reads the same Delta storage. | measured:duckdb_access |
| Operations | Serverless SQL warehouses | **MISSING** | no | No managed serverless warehouse is included. | documented |
| Operations | Warehouse autoscaling and auto-stop | **WORKAROUND** | no | Requires deployment-level automation. | documented |
| Performance | Result cache and managed query acceleration | **WORKAROUND** | no | Engine caches differ and are not managed as a single service. | documented |
| Observability | Query history and profiles | **ALTERNATIVE** | no | Spark event logs and engine-specific profiling. | documented |
| Automation | SQL alerts and scheduled queries | **ALTERNATIVE** | no | Airflow scheduling and alert integrations. | documented |
| BI | Integrated dashboards | **MISSING** | no | An external BI tool is required. | documented |

</details>

### Streaming and file ingestion

`Auto Loader and Databricks Structured Streaming` → `Apache Spark Structured Streaming and Kafka`

```
Outcome coverage  ██████████████████░░   90%   (9/10)
Native parity     ████████░░░░░░░░░░░░   40%   (4/10)
```

Native **4** · alternatives **2** · workarounds **3** · missing **1** · not assessed **0** · workload-required coverage **0/0**

<details markdown="1"><summary>Every capability and gap</summary>

| Area | Capability | Status | Required here | Gap or alternative | Evidence |
|---|---|---|---|---|---|
| Processing | Micro-batch streaming | **NATIVE** | no | — | planned:challenge-2 |
| Processing | Exactly-once checkpointed processing | **NATIVE** | no | — | documented |
| Connectivity | Kafka source and sink | **NATIVE** | no | — | documented |
| Files | File source ingestion | **NATIVE** | no | — | planned:challenge-2 |
| Files | Incremental file discovery at cloud scale | **WORKAROUND** | no | OSS file listing does not reproduce Auto Loader notification and discovery behavior. | planned:challenge-2 |
| Schema | Managed schema inference and schema location | **WORKAROUND** | no | Requires explicit schema state and evolution handling. | planned:challenge-2 |
| Schema | Rescued data column for unexpected input | **ALTERNATIVE** | no | Parse permissively and retain corrupt or unknown fields explicitly. | planned:challenge-2 |
| Operations | Managed file notification setup | **MISSING** | no | Cloud queues events and permissions must be provisioned separately. | documented |
| Operations | Auto Loader backfill controls | **WORKAROUND** | no | Requires custom discovery state or batch backfill orchestration. | planned:challenge-2 |
| Observability | Integrated streaming operational UI | **ALTERNATIVE** | no | Spark UI metrics and external monitoring. | documented |

</details>

### Catalog and governance

`Databricks managed Unity Catalog` → `Unity Catalog OSS 0.5.0`

```
Outcome coverage  █████████████░░░░░░░   67%   (12/18)
Native parity     ██████░░░░░░░░░░░░░░   28%   (5/18)
```

Native **5** · alternatives **2** · workarounds **5** · missing **6** · not assessed **0** · workload-required coverage **5/5**

<details markdown="1"><summary>Every capability and gap</summary>

| Area | Capability | Status | Required here | Gap or alternative | Evidence |
|---|---|---|---|---|---|
| Metadata | Catalog and schema hierarchy | **NATIVE** | yes | — | measured:catalog_probe.namespaces |
| Metadata | External Delta table registration | **NATIVE** | yes | — | measured:catalog_probe.external_table |
| Metadata | Volumes | **NATIVE** | yes | — | measured:catalog_probe.volume |
| Interoperability | REST catalog API | **NATIVE** | yes | — | measured:catalog_probe.rest_registration |
| Interoperability | Iceberg REST interoperability | **NATIVE** | no | — | documented |
| Storage | Storage credentials and credential vending | **WORKAROUND** | yes | Vended credentials omit the custom S3 endpoint used by SeaweedFS. | measured:duckdb_access |
| Authorization | Object privileges and grants | **WORKAROUND** | no | Supported by UC OSS but disabled in the tested stack and requires identity integration. | measured:catalog_probe.grants |
| Identity | Enterprise identity federation | **WORKAROUND** | no | OAuth/OIDC integration must be configured and operated. | documented |
| Governance | Governed tags | **MISSING** | no | No equivalent governed tag control plane is implemented. | documented |
| Authorization | Tag-driven ABAC policies | **MISSING** | no | Requires a policy service plus catalog and engine integration. | documented |
| Fine-grained access | Row filters | **MISSING** | no | UC OSS grants do not inject row predicates into every query engine. | documented |
| Fine-grained access | Column masks | **MISSING** | no | UC OSS grants do not rewrite protected columns in every query engine. | documented |
| Fine-grained access | Dynamic views for security | **ALTERNATIVE** | no | Engine views with carefully controlled base-table and storage access. | documented |
| Isolation | Workspace bindings | **MISSING** | no | The OSS server has no Databricks workspace boundary. | documented |
| Observability | Automatic lineage | **ALTERNATIVE** | no | OpenLineage with a compatible backend. | planned:challenge-8 |
| Observability | Audit and system tables | **WORKAROUND** | no | Logs must be collected and normalized separately. | planned:challenge-8 |
| Discovery | Catalog search and discovery UI | **WORKAROUND** | no | UC OSS UI is less complete than the managed governance experience. | documented |
| Federation | Lakehouse federation | **MISSING** | no | Cross-system query federation is not supplied by UC OSS. | documented |

</details>

### Declarative data pipelines

`Lakeflow Spark Declarative Pipelines` → `Apache Spark Declarative Pipelines 4.1`

```
Outcome coverage  ████████████████░░░░   79%   (11/14)
Native parity     █████████░░░░░░░░░░░   43%   (6/14)
```

Native **6** · alternatives **2** · workarounds **3** · missing **3** · not assessed **0** · workload-required coverage **0/0**

<details markdown="1"><summary>Every capability and gap</summary>

| Area | Capability | Status | Required here | Gap or alternative | Evidence |
|---|---|---|---|---|---|
| Authoring | Declarative table and view definitions | **NATIVE** | no | — | planned:challenge-3 |
| Authoring | Python authoring | **NATIVE** | no | — | documented |
| Authoring | SQL authoring | **NATIVE** | no | — | documented |
| Planning | Dependency graph construction | **NATIVE** | no | — | documented |
| Processing | Batch and streaming flows | **NATIVE** | no | — | documented |
| Processing | Materialized views and streaming tables | **NATIVE** | no | — | documented |
| Quality | Data-quality expectations | **WORKAROUND** | no | Exact Lakeflow expectation metrics and operational behavior require comparison tests. | planned:challenge-3 |
| CDC | Managed CDC / AUTO CDC flows | **WORKAROUND** | no | Equivalent semantics and supported options require executable validation. | planned:challenge-3 |
| Observability | Pipeline event log | **WORKAROUND** | no | OSS events do not provide the complete managed event-log experience. | planned:challenge-3 |
| Operations | Managed scheduling and triggers | **ALTERNATIVE** | no | Airflow schedules pipeline execution. | documented |
| Operations | Managed retries and recovery | **ALTERNATIVE** | no | Spark checkpointing plus Airflow retry policy. | documented |
| Operations | Pipeline autoscaling | **MISSING** | no | The tested standalone Spark deployment is fixed-size. | documented |
| Operations | Serverless pipeline compute | **MISSING** | no | Compute is self-managed. | documented |
| Operations | Integrated pipeline UI and graph | **MISSING** | no | No equivalent managed pipeline UI is included. | documented |

</details>

### Workflow orchestration

`Lakeflow Jobs` → `Apache Airflow 3.1.6`

```
Outcome coverage  █████████████████░░░   83%   (10/12)
Native parity     ████████░░░░░░░░░░░░   42%   (5/12)
```

Native **5** · alternatives **4** · workarounds **1** · missing **2** · not assessed **0** · workload-required coverage **4/4**

<details markdown="1"><summary>Every capability and gap</summary>

| Area | Capability | Status | Required here | Gap or alternative | Evidence |
|---|---|---|---|---|---|
| Core | Directed acyclic task graphs | **NATIVE** | yes | — | measured:orchestration |
| Triggers | Schedules and event triggers | **NATIVE** | no | — | documented |
| Core | Task dependencies and conditions | **NATIVE** | yes | — | measured:orchestration |
| Operations | Retries timeouts and notifications | **NATIVE** | no | — | documented |
| Core | Parameters and task values | **ALTERNATIVE** | yes | Airflow params XCom and generated task configuration. | measured:orchestration |
| Operations | Backfills and repair runs | **ALTERNATIVE** | no | Airflow backfill and task clearing semantics. | documented |
| Tasks | Python and notebook tasks | **ALTERNATIVE** | yes | Python tasks and Spark Connect replace workspace notebook tasks. | measured:orchestration |
| Tasks | SQL and pipeline tasks | **ALTERNATIVE** | no | Airflow operators invoke query and pipeline services. | documented |
| Observability | Run history and logs | **NATIVE** | no | — | documented |
| Compute | Managed compute attachment | **WORKAROUND** | no | Compute lifecycle needs operators or infrastructure automation. | documented |
| Compute | Serverless job execution | **MISSING** | no | Airflow schedules work but does not provide serverless Spark compute. | documented |
| Experience | Databricks-native task types and UI | **MISSING** | no | Airflow has its own operators and UI rather than Databricks task parity. | documented |

</details>

### Deployment and configuration

`Databricks Asset Bundles` → `Python packaging and Docker Compose`

```
Outcome coverage  ██████████████████░░   89%   (8/9)
Native parity     ████░░░░░░░░░░░░░░░░   22%   (2/9)
```

Native **2** · alternatives **4** · workarounds **2** · missing **1** · not assessed **0** · workload-required coverage **4/4**

<details markdown="1"><summary>Every capability and gap</summary>

| Area | Capability | Status | Required here | Gap or alternative | Evidence |
|---|---|---|---|---|---|
| Definition | Version-controlled deployment definition | **NATIVE** | yes | — | measured:orchestration |
| Definition | Environment variables and targets | **ALTERNATIVE** | yes | Environment files and platform configuration. | documented |
| Artifacts | Python wheel packaging | **NATIVE** | yes | — | measured:spark_executable |
| Deployment | Resource deployment | **ALTERNATIVE** | yes | Compose and platform scripts provision the open services. | documented |
| Deployment | Deployment validation | **ALTERNATIVE** | no | Configuration tests and Freedom Check. | documented |
| Definition | Development and production target overrides | **ALTERNATIVE** | no | Separate environment configuration and infrastructure variables. | documented |
| Security | Identity-aware run-as configuration | **WORKAROUND** | no | Requires identity integration across Airflow Spark and UC OSS. | documented |
| Deployment | Unified resource state and deployment lifecycle | **WORKAROUND** | no | Multiple open components have separate lifecycle and state. | documented |
| Deployment | Databricks workspace resource model | **MISSING** | no | Workspace-specific resources intentionally have no direct open equivalent. | documented |

</details>

### ML lifecycle

`Databricks managed MLflow` → `MLflow OSS 3.14`

```
Outcome coverage  ████████████░░░░░░░░   60%   (6/10)
Native parity     ██████████░░░░░░░░░░   50%   (5/10)
```

Native **5** · alternatives **0** · workarounds **1** · missing **4** · not assessed **0** · workload-required coverage **0/0**

<details markdown="1"><summary>Every capability and gap</summary>

| Area | Capability | Status | Required here | Gap or alternative | Evidence |
|---|---|---|---|---|---|
| Tracking | Experiment and run tracking | **NATIVE** | no | — | planned:challenge-5 |
| Tracking | Artifact storage | **NATIVE** | no | — | documented |
| Models | Model packaging and flavors | **NATIVE** | no | — | documented |
| Registry | Model registry | **NATIVE** | no | — | documented |
| AI | Tracing and evaluation APIs | **NATIVE** | no | — | documented |
| Governance | Registry integration with catalog permissions | **WORKAROUND** | no | Identity and UC OSS integration require explicit configuration. | documented |
| Operations | Managed tracking service operations | **MISSING** | no | The service database artifacts backups and upgrades are operator responsibilities. | documented |
| Serving | Managed model serving | **MISSING** | no | A serving platform must be deployed separately. | documented |
| Serving | Serverless GPU inference | **MISSING** | no | No managed inference compute is included. | documented |
| Features | Integrated feature engineering service | **MISSING** | no | No managed feature store equivalent is included. | documented |

</details>

### Business intelligence

`Databricks SQL AI/BI` → `Open BI tools over Spark SQL or DuckDB`

```
Outcome coverage  ███████████████░░░░░   75%   (6/8)
Native parity     ░░░░░░░░░░░░░░░░░░░░    0%   (0/8)
```

Native **0** · alternatives **5** · workarounds **1** · missing **2** · not assessed **0** · workload-required coverage **0/0**

<details markdown="1"><summary>Every capability and gap</summary>

| Area | Capability | Status | Required here | Gap or alternative | Evidence |
|---|---|---|---|---|---|
| Authoring | SQL editor and saved queries | **ALTERNATIVE** | no | Use an external SQL client or BI authoring tool. | planned:challenge-6 |
| Visualization | Interactive dashboards | **ALTERNATIVE** | no | Connect an open BI tool to the query endpoint. | planned:challenge-6 |
| Distribution | Dashboard sharing and embedding | **ALTERNATIVE** | no | Use the selected BI tool's sharing and embedding model. | planned:challenge-6 |
| Automation | Scheduled dashboard refresh | **ALTERNATIVE** | no | BI scheduling or Airflow. | planned:challenge-6 |
| Automation | SQL alerts | **ALTERNATIVE** | no | Scheduled queries plus an alert integration. | planned:challenge-6 |
| Governance | Catalog-aware permissions | **WORKAROUND** | no | End-to-end identity propagation must be integrated across BI query service and UC OSS. | planned:challenge-6 |
| AI | AI-assisted dashboard authoring | **MISSING** | no | No equivalent assistant is included in the open stack. | documented |
| Semantics | Managed semantic metric layer | **MISSING** | no | A semantic-layer component and model must be selected separately. | documented |

</details>

### AI, vector search and agents

`Databricks Mosaic AI capabilities` → `Open models and separately operated AI services`

```
Outcome coverage  ██████████████░░░░░░   70%   (7/10)
Native parity     ████░░░░░░░░░░░░░░░░   20%   (2/10)
```

Native **2** · alternatives **3** · workarounds **2** · missing **3** · not assessed **0** · workload-required coverage **0/0**

<details markdown="1"><summary>Every capability and gap</summary>

| Area | Capability | Status | Required here | Gap or alternative | Evidence |
|---|---|---|---|---|---|
| Models | Foundation model inference API | **ALTERNATIVE** | no | Use an open model server or external model API. | planned:challenge-7 |
| Observability | Model and prompt tracing | **NATIVE** | no | — | documented |
| Evaluation | Evaluation datasets and metrics | **NATIVE** | no | — | documented |
| Retrieval | Vector indexing and similarity search | **ALTERNATIVE** | no | Deploy an open vector database or search engine. | planned:challenge-7 |
| Retrieval | Automatic vector index synchronization | **WORKAROUND** | no | Data-change capture embedding and index updates require a custom pipeline. | planned:challenge-7 |
| Agents | Agent authoring framework | **ALTERNATIVE** | no | Use an open agent framework with MLflow tracing. | planned:challenge-7 |
| Agents | Managed agent deployment | **MISSING** | no | Agent serving scaling and lifecycle must be supplied separately. | documented |
| Governance | AI gateway and endpoint governance | **MISSING** | no | No unified AI gateway is included in this stack. | documented |
| Governance | Catalog-governed AI assets | **WORKAROUND** | no | UC OSS and MLflow permissions require explicit identity integration. | planned:challenge-7 |
| Serving | Serverless GPU model serving | **MISSING** | no | GPU serving infrastructure is operator-owned. | documented |

</details>

### Governance observability

`Databricks system tables and Unity Catalog lineage` → `Spark event logs and OpenLineage`

```
Outcome coverage  ████████████░░░░░░░░   60%   (6/10)
Native parity     ████░░░░░░░░░░░░░░░░   20%   (2/10)
```

Native **2** · alternatives **2** · workarounds **2** · missing **4** · not assessed **0** · workload-required coverage **0/0**

<details markdown="1"><summary>Every capability and gap</summary>

| Area | Capability | Status | Required here | Gap or alternative | Evidence |
|---|---|---|---|---|---|
| Runtime | Spark execution metrics | **NATIVE** | no | — | documented |
| Runtime | Query plans and job event logs | **NATIVE** | no | — | documented |
| Lineage | Cross-job dataset lineage | **ALTERNATIVE** | no | OpenLineage events and a compatible backend. | planned:challenge-8 |
| Lineage | Column-level lineage | **WORKAROUND** | no | Coverage depends on engine integration and SQL-plan extraction. | planned:challenge-8 |
| Audit | Account audit log | **WORKAROUND** | no | Service logs must be collected correlated and retained separately. | planned:challenge-8 |
| Audit | Query history system tables | **ALTERNATIVE** | no | Spark event-log processing and engine-specific history. | documented |
| Cost | Billing and usage system tables | **MISSING** | no | Infrastructure and service cost data require a separate FinOps pipeline. | documented |
| Governance | Access and governance system tables | **MISSING** | no | No unified open governance event schema is implemented. | documented |
| Operations | Managed retention and query service | **MISSING** | no | Storage retention indexing and query infrastructure are operator-owned. | documented |
| Experience | Unified governance UI | **MISSING** | no | Separate open tools are required for logs metrics lineage and catalog metadata. | documented |

</details>

Definitions and maintenance rules: `docs/platform-capability-coverage.md`.

## 10. Known limitations

- The Databricks side was not executed for this report. SQL portability is measured against the official TPC-H answers (SF ≤ 1) or the OpenLakehouse Spark run, not against Databricks output.
- Performance numbers compare unlike compute and must not be read as a platform performance ranking.
- UC OSS runs with authorization disabled (OpenLakehouse default); grants, row filters and masks are not migrated.
- The DuckDB `unity_catalog` extension cannot read from SeaweedFS through UC OSS credential vending (vended credentials carry no S3 endpoint); DuckDB resolves locations through UC and reads with a configured S3 secret.
- The Airflow DAG is generated from the shared graph and consistency-checked, but v1 runs the OpenLakehouse pipeline from the command line rather than from Airflow.
- SQL portability is measured on TPC-H only. TPC-H uses a conservative SQL subset; real workloads using Databricks SQL extensions will score lower (use `freedom assess` to find them).
- Lines-of-code ratios measure how much code is shared, not how hard the platform-specific part is to write.

## 11. Freedom Score

```
LAKEHOUSE FREEDOM REPORT
────────────────────────────────────────────
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
███████████████░░░░░   75%
```

| Component | Formula | Included in Freedom Score |
|---|---|---|
| TPC-H SQL portability (Spark) | TPC-H queries running unchanged with correct results on spark / 22 | yes |
| TPC-H SQL portability (DuckDB) | TPC-H queries running unchanged with correct results on duckdb / 22 | no (additional engine) |
| Transformation portability | shared transformation LOC / (shared + OpenLakehouse-specific transformation LOC) | yes |
| Catalog portability | Unity Catalog capabilities recreated in UC OSS / capabilities used | yes |
| Orchestration portability | shared orchestration LOC / (shared + OpenLakehouse-specific orchestration LOC) | yes |

Freedom Score = unweighted mean of the included, measured components. Definitions: `freedom/reporting/score.py`.

## 12. Conclusions

**SQL.** 22 of 22 TPC-H queries ran unchanged on open-source Spark with correct results, and 22 of 22 on DuckDB. TPC-H is a conservative SQL subset, so treat this as an upper bound for real workloads.

**Code.** 91% of the code that runs the workload on OpenLakehouse is identical to the code that runs it on Databricks (1385 of 1524 LOC). The platform-specific remainder is session setup, configuration and orchestration.

**Catalog.** 6 of 10 Unity Catalog capabilities used by the workload were recreated in UC OSS. Gaps: Column metadata for tables created from Spark; Custom table properties set from Spark SQL; ALTER TABLE for comments and properties; Grants (GRANT USE SCHEMA ... TO principal). This is where a migration needs the most deliberate work, and where the managed catalog clearly adds value (F6).

**Orchestration.** Sharing the task graph keeps both schedulers aligned, but the scheduler definitions themselves are platform code (51% shared).

**Next step.** Run the Databricks bundle to replace the stand-in references with measured Databricks output and complete the two-implementation comparison.

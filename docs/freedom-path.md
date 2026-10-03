# Freedom Path

The route from a Databricks workload to the same workload on OpenLakehouse. Steps 1 to 5 can be rehearsed at any time without touching production, and running them regularly keeps the option real.

```
 assess ──► own the data ──► reach the storage ──► rebuild the catalog ──► run ──► validate ──► switch scheduling
   0             1                   2                      3                4         5               6
```

## 0. Assess

```bash
make freedom-assess REPO_PATH=/path/to/your/databricks/project
```

The scanner lists Databricks-specific constructs with a classification and the open alternative, for example Auto Loader (`REWRITE`), `dbutils` (`ADAPTABLE`), AI functions (`PLATFORM-SPECIFIC`). Read the result as a map of where the effort will go. A file with no findings can still depend on platform behaviour, and step 5 is where that shows up.

## 1. Own the data

Write business tables as **external** Delta tables in a storage account you control (Principle F1). In the bundle this is the `table_root` variable.

Things to check on existing Databricks tables before Freedom Day:

| Property | Why it matters | How to see it |
|---|---|---|
| Managed or external | Managed tables live under catalog-owned storage; newer catalog-managed tables also route commits through the catalog. Reading them without Unity Catalog is not guaranteed. | `DESCRIBE TABLE EXTENDED` → `Type` |
| Delta table features | The open readers must support every reader feature in use (deletion vectors, column mapping, v2 checkpoints, type widening, variant, ...). | `DESCRIBE DETAIL` → `minReaderVersion`, `tableFeatures` |
| Storage location | Must be reachable by the open stack. | `DESCRIBE DETAIL` → `location` |

Freedom Day prints the protocol versions and table features it found and fails if a table cannot be read, so unsupported features are reported rather than assumed.

## 2. Reach the storage

Freedom Day needs the Delta folders on storage that OpenLakehouse can read. There are two options.

**Read in place.** Point OpenLakehouse at the original bucket or container. For S3 this is configuration only (`spark.hadoop.fs.s3a.*`, a DuckDB S3 secret). For ADLS Gen2 (Azure Databricks), Spark needs `hadoop-azure` on the classpath and an OAuth or key configuration. OpenLakehouse does not ship that JAR, so this is an addition to the stack.

**Byte-for-byte copy.** Sync the external location into the OpenLakehouse bucket with a tool that copies objects unchanged, for example `azcopy sync` or `rclone sync` from ADLS to SeaweedFS or MinIO. A Delta table is a folder of Parquet files plus a JSON/Parquet log. Copying the folder copies the table, history included, with no conversion. This is not "regenerating the data": the Parquet files and commit log are the same bytes.

Then:

```bash
make freedom-day SCALE=1 SOURCE=s3://lakehouse/<prefix-holding-<schema>/<table>-folders>
```

## 3. Rebuild the catalog

Freedom Day creates an empty Unity Catalog OSS catalog (`freedom_day`) and registers each table through the UC REST API, using the schema read from the table's own `_delta_log`. Registering through the API, instead of `CREATE TABLE` from Spark, keeps column metadata in the catalog (see the catalog probe in the Freedom Report).

What does not come back on its own: grants, row filters, column masks, tags, lineage, and anything else stored only in the managed catalog. Export what you need while the managed catalog is still available. The catalog probe in `freedom/validation/catalog_portability.py` shows what UC OSS 0.5.0 can hold.

## 4. Run

Run the shared code with the OpenLakehouse entry point:

```bash
make pipeline SCALE=1                    # or: freedom pipeline --task silver --scale 1
```

The only code that changes is the code already isolated in `platforms/` (session, configuration, orchestration).

## 5. Validate

```bash
make freedom-check SCALE=1
make freedom-report SCALE=1
```

The check compares results with the official TPC-H answers, with the Databricks run when its results are present, and with two independent oracles (DuckDB SQL and plain Python).

## 6. Switch scheduling

Deploy `platforms/openlakehouse/airflow/dags/lakehouse_freedom.py` to Airflow (OpenLakehouse ships Airflow 3.1.6, `./lakehouse start airflow` in the submodule). The DAG is generated from the same task graph as the Databricks job. v1 checks this for consistency but does not execute it; see the limitations in the report.

## Freedom Day as a drill

Freedom Day works best as a recurring rehearsal, not a one-off event. Running `make freedom-day` against a fresh sync on a schedule shows whether a table has picked up a Delta feature the open readers cannot handle, or a dependency on catalog-only metadata, before anyone needs the exit.

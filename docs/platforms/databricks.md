# Databricks (managed implementation)

The same pipeline as OpenLakehouse, deployed as a Databricks Asset Bundle with one serverless job. The job runs the shared `lakehouse_freedom` wheel; `platforms/databricks/entrypoint.py` is the only Databricks-specific Python.

## Prerequisites

* Databricks CLI with bundle support, authenticated (`databricks auth login -p <profile>`).
* `uv` locally (the bundle builds the wheel with `uv build --wheel`).
* A Unity Catalog catalog named `freedom` (or set `--var catalog=...`):
  ```sql
  CREATE CATALOG IF NOT EXISTS freedom;
  ```
* An **external location** for the Delta tables, with `CREATE EXTERNAL TABLE` granted to the deploying principal. This keeps table layout equivalent across both reference implementations.

## Run

From the repository root:

```bash
make databricks-validate DATABRICKS_PROFILE=<profile>
make databricks-run      DATABRICKS_PROFILE=<profile> SCALE=1 \
     TABLE_ROOT=abfss://<container>@<account>.dfs.core.windows.net/freedom
make databricks-fetch-results DATABRICKS_PROFILE=<profile>
make freedom-check SCALE=1 && make freedom-report SCALE=1
```

`databricks-run` deploys the bundle and runs the job: generate (DuckDB dbgen on the driver into the `landing.raw` volume) → bronze → silver → gold → quality → TPC-H queries, plus the incremental SCD2 scenario. Results are written to the `landing.results` volume. `databricks-fetch-results` copies them to `benchmarks/results/databricks/`, where the Freedom Check and Report pick them up.

Running the job uses Databricks compute and is billed to the workspace.

## What gets created

| Object | Name |
|---|---|
| Schema (bundle) | `freedom.landing`, granted `USE_SCHEMA`, `READ_VOLUME` to `reader_group` |
| Volumes (bundle) | `freedom.landing.raw`, `freedom.landing.results` |
| Schemas (job) | `freedom.tpch_sf<N>_bronze`, `freedom.tpch_sf<N>`, `freedom.tpch_sf<N>_gold`, `freedom.incremental` |
| Tables (job) | external Delta tables under `${table_root}/<schema>/<table>` |
| Job | `lakehouse-freedom-sf<N>` |

## Status in v1

The bundle passes the configuration checks of `databricks bundle validate` (Databricks CLI 1.18); the final step of validation, resolving the workspace, needs an authenticated profile. The results committed in this repository come from OpenLakehouse only; the Databricks columns in `reports/freedom-report.md` show *not run* until this job has been executed and its results fetched.

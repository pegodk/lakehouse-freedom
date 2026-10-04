# Databricks (managed implementation)

The same pipeline as OpenLakehouse, deployed as a Databricks Asset Bundle with one serverless job. The job runs the shared `portable_lakehouse` wheel; `platforms/databricks/entrypoint.py` is the only Databricks-specific Python.

## Prerequisites

* Databricks CLI with bundle support, authenticated (`databricks auth login -p <profile>`).
* `uv` locally (the bundle builds the wheel with `uv build --wheel`).
* A Unity Catalog catalog named `portable_lakehouse` (or set `--var catalog=...`):
  ```sql
  CREATE CATALOG IF NOT EXISTS portable_lakehouse;
  ```
* An **external location** for the Delta tables, with `CREATE EXTERNAL TABLE` granted to the deploying principal. This keeps table layout equivalent across both reference implementations.

## Run

From the repository root:

```bash
make databricks-validate DATABRICKS_PROFILE=<profile>
make databricks-run      DATABRICKS_PROFILE=<profile> SCALE=1 \
     TABLE_ROOT=abfss://<container>@<account>.dfs.core.windows.net/portable-lakehouse
make databricks-fetch-results DATABRICKS_PROFILE=<profile>
make portability-check SCALE=1 && make portability-report SCALE=1
```

`databricks-run` deploys the bundle and runs the job: generate (DuckDB dbgen on the driver into the `landing.raw` volume) → bronze → silver → gold → quality → TPC-H queries, plus the incremental SCD2 scenario. Results are written to the `landing.results` volume. `databricks-fetch-results` copies them to `benchmarks/results/databricks/`, where the Portability Check and Report pick them up.

Running the job uses Databricks compute and is billed to the workspace.

## What gets created

| Object | Name |
|---|---|
| Schema (bundle) | `portable_lakehouse.landing`, granted `USE_SCHEMA`, `READ_VOLUME` to `reader_group` |
| Volumes (bundle) | `portable_lakehouse.landing.raw`, `portable_lakehouse.landing.results` |
| Schemas (job) | `portable_lakehouse.tpch_sf<N>_bronze`, `portable_lakehouse.tpch_sf<N>`, `portable_lakehouse.tpch_sf<N>_gold`, `portable_lakehouse.incremental` |
| Tables (job) | external Delta tables under `${table_root}/<schema>/<table>` |
| Job | `portable-lakehouse-sf<N>` |

## Status in v1

The bundle passes `databricks bundle validate` with Databricks CLI 1.18. The committed SF1 and SF10 results were produced on Databricks serverless jobs compute and include all 22 TPC-H queries, table-quality and fingerprint evidence, and the incremental SCD2 scenario. The report compares execution characteristics across unlike compute only; it is not a platform performance comparison.

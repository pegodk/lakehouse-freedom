# Commands

All `make` targets accept `SCALE` (TPC-H scale factor, default `1`). Each one wraps a `freedom` CLI command from the project's virtual environment.

## OpenLakehouse stack

| Make target | What it does |
|---|---|
| `make setup` | submodule, `.venv`, OpenLakehouse configuration, Spark JARs |
| `make openlakehouse-configure` | rewrite the stack's runtime config from its examples plus the Lakehouse Freedom overlay |
| `make openlakehouse-up` | start SeaweedFS, PostgreSQL, Unity Catalog OSS, Spark 4.1 + Connect |
| `make openlakehouse-status` | container status |
| `make openlakehouse-down` | stop, keep data |
| `make openlakehouse-destroy` | stop and delete all data volumes |

## Workload and measurements

| Make target | CLI | What it does |
|---|---|---|
| `make generate-data` | `freedom generate --scale N` | TPC-H Raw Parquet into `s3://lakehouse/freedom/raw/sf<N>` |
| `make pipeline` | `freedom pipeline --scale N [--task KEY]` | all tasks, or one task, on OpenLakehouse |
| `make freedom-benchmark` | `freedom benchmark --scale N --repeats R` | 22 queries on Spark and DuckDB (`REPEATS`, default 3); adds Databricks when `DATABRICKS_PROFILE` is set |
| `make freedom-check` | `freedom check --scale N [--no-probe]` | 14 checks; exit code 1 on any FAIL |
| `make freedom-report` | `freedom report --scale N` | `reports/freedom-report.md` and `reports/freedom-report-sf<N>.md` |
| `make freedom-assess` | `freedom assess PATH [--json]` | scan a repository for Databricks-specific constructs (`REPO_PATH=`) |
| `make demo` | | pipeline → benchmark → check → report |

Pipeline task keys: `generate`, `bronze`, `silver`, `gold`, `quality`, `incremental`, `tpch_queries`.

## Databricks

| Make target | What it does |
|---|---|
| `make databricks-validate` | `databricks bundle validate` |
| `make databricks-deploy` | deploy the bundle (`TABLE_ROOT=`, `SCALE=`, `REPEATS=`) |
| `make databricks-run` | deploy and run the job (uses billed compute) |
| `make databricks-fetch-results` | copy results from the `freedom.landing.results` volume into `benchmarks/results/databricks/` |

All of them take `DATABRICKS_PROFILE=<profile>`.

## Development

| Make target | What it does |
|---|---|
| `make test` | unit and portability tests, no stack required |
| `make test-stack` | end to end at SF0.01 against the running stack |
| `make lint` | ruff |
| `make docs-serve` | preview this site on http://localhost:8000 |
| `make docs-build` | build the site into `./site` |

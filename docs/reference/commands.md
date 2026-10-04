# Commands

All `make` targets accept `SCALE` (TPC-H scale factor, default `1`). Each one wraps a `portable-lakehouse` CLI command from the project's virtual environment.

## OpenLakehouse stack

| Make target | What it does |
|---|---|
| `make setup` | submodule, `.venv`, OpenLakehouse configuration, Spark JARs |
| `make openlakehouse-configure` | rewrite the stack's runtime config from its examples plus the Portable Lakehouse overlay |
| `make openlakehouse-up` | start SeaweedFS, PostgreSQL, Unity Catalog OSS, Spark 4.1 + Connect |
| `make openlakehouse-status` | container status |
| `make openlakehouse-down` | stop, keep data |
| `make openlakehouse-destroy` | stop and delete all data volumes |

## Workload and measurements

| Make target | CLI | What it does |
|---|---|---|
| `make generate-data` | `portable-lakehouse generate --scale N` | TPC-H Raw Parquet into `s3://lakehouse/portable-lakehouse/raw/sf<N>` |
| `make pipeline` | `portable-lakehouse pipeline --scale N [--task KEY]` | all tasks, or one task, on OpenLakehouse |
| `make portability-benchmark` | `portable-lakehouse benchmark --scale N --repeats R` | 22 queries on Spark, DuckDB and DataFusion (`REPEATS`, default 3); adds Databricks when `DATABRICKS_PROFILE` is set |
| `make portability-check` | `portable-lakehouse check --scale N [--no-probe]` | portability checks, including MLflow evidence; exit code 1 on any FAIL |
| `make portability-report` | `portable-lakehouse report --scale N` | `reports/portability-report.md` and `reports/portability-report-sf<N>.md` |
| `make portability-assess` | `portable-lakehouse assess PATH [--json]` | identify Databricks-specific constructs and possible alternatives (`REPO_PATH=`) |
| `make mlflow-smoke` | `portable-lakehouse mlflow [--tracking-uri URI]` | log and read back a portable MLflow run; writes `reports/mlflow-tracking.json` |
| `make demo` | | pipeline → benchmark → check → report |

Pipeline task keys: `generate`, `bronze`, `silver`, `gold`, `quality`, `incremental`, `tpch_queries`.

## Databricks

| Make target | What it does |
|---|---|
| `make databricks-validate` | `databricks bundle validate` |
| `make databricks-deploy` | deploy the bundle (`TABLE_ROOT=`, `SCALE=`, `REPEATS=`) |
| `make databricks-run` | deploy and run the job (uses billed compute) |
| `make databricks-fetch-results` | copy results from the `portable_lakehouse.landing.results` volume into `benchmarks/results/databricks/` |

All of them take `DATABRICKS_PROFILE=<profile>`.

## Development

| Make target | What it does |
|---|---|
| `make test` | unit and portability tests, no stack required |
| `make test-stack` | end to end at SF0.01 against the running stack |
| `make lint` | ruff |
| `make docs-serve` | preview this site on http://localhost:8000 |
| `make docs-build` | build the site into `./site` |

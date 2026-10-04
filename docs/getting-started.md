# Get started

The OpenLakehouse side runs on a laptop. The Databricks side is optional, and is covered on the [Databricks](platforms/databricks.md) page.

## Requirements

| | |
|---|---|
| Docker | Compose v2, about 10 GB of memory available to containers |
| [uv](https://docs.astral.sh/uv/) | creates the Python 3.12 environment |
| git, make, curl | standard tools |
| Disk | about 5 GB for SF1, 20 GB for SF10 (Docker volumes) |
| Network | first run downloads about 1 GB of Spark JARs and the container images |

Ports used: 5432 (PostgreSQL), 8333 (SeaweedFS S3), 8081 (Unity Catalog OSS), 7078/8082/8083 (Spark master and worker), 15002 (Spark Connect).

## Three commands

```bash
git clone --recurse-submodules https://github.com/pegodk/lakehouse-freedom.git
cd lakehouse-freedom

make setup              # (1)!
make openlakehouse-up   # (2)!
make demo SCALE=1       # (3)!
```

1. Initialises the OpenLakehouse submodule, creates `.venv`, writes the OpenLakehouse runtime configuration and downloads its Spark JARs.
2. Starts SeaweedFS, PostgreSQL, Unity Catalog OSS and Spark 4.1 (master, worker, Connect server) using OpenLakehouse's own compose files.
3. Pipeline, Freedom Benchmark, Freedom Check and Freedom Report, at TPC-H scale factor 1.

When it finishes, open `reports/freedom-report.md`.

!!! tip "Pick a scale factor"

    `SCALE=0.01` is a one-minute smoke run. `SCALE=1` takes roughly 15 minutes on an 8-core laptop. `SCALE=10` is the larger reference size; budget an hour or more and 20 GB of disk.

## Step by step

```bash
make generate-data     SCALE=1   # TPC-H Raw Parquet into s3://lakehouse/freedom/raw/sf1
make pipeline          SCALE=1   # generate → bronze → silver → gold → quality → TPC-H, plus SCD2
make freedom-benchmark SCALE=1   # 22 queries on Spark, DuckDB and DataFusion (REPEATS=3)
make freedom-check     SCALE=1   # exit code 1 if any check fails
make freedom-report    SCALE=1   # reports/freedom-report.md
```

Each step reads what the previous one wrote, so they can be re-run individually.

## Stopping

```bash
make openlakehouse-down      # stop containers, keep data
make openlakehouse-destroy   # stop containers and delete all data volumes
```

## Tests

```bash
make test         # unit and portability tests, no stack needed (~5 s)
make test-stack   # end to end at SF0.01 against the running stack
```

## Smaller machines

The default Spark sizing assumes 8 cores and 16 GB. For a smaller machine:

```bash
FREEDOM_SPARK_EXECUTOR_CORES=3 FREEDOM_SPARK_EXECUTOR_MEMORY=4g make openlakehouse-configure
platforms/openlakehouse/scripts/stack.sh restart-spark
```

## Troubleshooting

| Symptom | Cause and fix |
|---|---|
| `Spark Connect ... timed out` during `openlakehouse-up` | The Connect server is still starting or failed. `docker logs spark-connect-41`, then `platforms/openlakehouse/scripts/stack.sh restart-spark`. |
| `DELTA_CREATE_TABLE_WITH_NON_EMPTY_LOCATION` | A table folder exists in storage but the table is not registered in UC OSS, for example after recreating the UC container. Run `make openlakehouse-destroy` for a clean slate, or register the existing table location in UC OSS. |
| Port already in use | Another local service holds one of the ports above. Stop it, or change the published port in the OpenLakehouse compose file. |
| `No pipeline output for SF...` | Run `make pipeline SCALE=...` before the benchmark. |

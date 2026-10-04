# OpenLakehouse (freedom implementation)

[OpenLakehouse](https://openlakehouse.io) is the reference open-source platform. Its implementation, [`open-lakehouse/open-lakehouse`](https://github.com/open-lakehouse/open-lakehouse), is included as a git submodule in `platforms/openlakehouse/stack/`, pinned to a commit. Lakehouse Freedom uses its compose files, images, JAR set, configuration examples and storage bootstrap unchanged.

## Components used

Versions are read from the pinned submodule at run time (`adapter.discover_versions()`) and recorded in every benchmark result. At the pinned commit:

| Component | Version | Used for |
|---|---|---|
| Apache Spark | 4.1.0 (`apache/spark:4.1.0-scala2.13-java21-python3-r-ubuntu`) | all pipeline tasks, via Spark Connect on `:15002` |
| Delta Lake | 4.3.1 (`delta-spark_2.13`) | table format |
| Unity Catalog OSS | server v0.5.0, Spark connector 0.4.1 | catalog `freedom` on `:8081` |
| SeaweedFS | 3.80 | S3-compatible storage on `:8333`, bucket `lakehouse` |
| PostgreSQL | 16 | started by the storage compose file (OpenLakehouse metastore) |
| DuckDB | 1.5.6 (pinned in `pyproject.toml`) | generator, second query engine, validation oracle |
| Apache DataFusion | 50–54 (bounded in `pyproject.toml`) | third query engine; reference governance enforcement point |
| Airflow | 3.1.6 (OpenLakehouse, optional) | DAG in `airflow/dags/`, not executed in v1 |

OpenLakehouse also provides Kafka, MLflow, Iceberg, Jupyter and a dashboard. The stack's MLflow service is optional: the portable tracking smoke test defaults to local SQLite and can target that service by URI.

## Files

All paths are relative to `platforms/openlakehouse/`.

| File | Purpose |
|---|---|
| `stack/` | the OpenLakehouse submodule (do not edit; runtime config is gitignored there) |
| `config/freedom.env` | becomes `stack/.env` |
| `config/spark-defaults.freedom.conf` | appended to the stack's Spark example: `freedom` UC catalog, laptop sizing |
| `scripts/configure.sh` | writes `stack/.env`, `stack/config/spark/spark-defaults.conf`, `stack/config/unity-catalog/server.properties` |
| `scripts/stack.sh` | `up` / `down` / `destroy` / `status` / `restart-spark` for the services above |
| `adapter.py` | endpoints, credentials, storage roots, version discovery |
| `catalog.py` | UC OSS catalog bootstrap and location lookup |
| `entrypoint.py` | runs pipeline tasks over Spark Connect |
| `airflow/dags/lakehouse_freedom.py` | Airflow DAG generated from the shared task graph |

## Why `stack.sh` instead of `./lakehouse`

The OpenLakehouse CLI checks ports with `nc`, which is missing on many machines. `stack.sh` runs the same compose files with the project name `openlakehouse`, the same storage bootstrap (`scripts/tools/init-storage.sh`), and waits for Spark Connect by running a query (Docker publishes port 15002 before the server is ready). If you have `nc`, `cd stack && ./lakehouse start storage && ./lakehouse start spark && ./lakehouse start unity-catalog` brings up an equivalent stack, but under a different compose project name, so use one method consistently.

## Sizing

Defaults assume an 8-core, 16 GB machine: one executor with 6 cores and 7 GB, a 2 GB driver, 24 shuffle partitions. Override before `make openlakehouse-configure`:

```bash
FREEDOM_SPARK_EXECUTOR_CORES=4 FREEDOM_SPARK_EXECUTOR_MEMORY=5g make openlakehouse-configure
platforms/openlakehouse/scripts/stack.sh restart-spark
```

SF10 needs roughly 15 GB of free disk for raw, Bronze and Silver data in the SeaweedFS volume.

## Running inside the Docker network (Airflow)

`adapter.py` reads `FREEDOM_SPARK_REMOTE`, `FREEDOM_UC_URL` and `FREEDOM_S3_ENDPOINT`, so the same entry point works from a container on the OpenLakehouse network (`sc://spark-connect-41:15002`, `http://unity-catalog:8080`, `seaweedfs:8333`).

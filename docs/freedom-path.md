# Freedom Path

The route from a Databricks workload to the same workload on OpenLakehouse. The two reference implementations make each step concrete and comparable.

```
 assess ──► own the data ──► configure the target ──► run ──► validate ──► switch scheduling
   0             1                    2                 3         4               5
```

## 0. Assess

```bash
make freedom-assess REPO_PATH=/path/to/your/databricks/project
```

The scanner lists Databricks-specific constructs with a classification and the open alternative, for example Auto Loader (`REWRITE`), `dbutils` (`ADAPTABLE`), AI functions (`PLATFORM-SPECIFIC`). Read the result as a map of where the effort will go. A file with no findings can still depend on platform behaviour, and step 5 is where that shows up.

## 1. Own the data

Write business tables as **external** Delta tables in a storage account you control (Principle F1). In the bundle this is the `table_root` variable.

Things to compare for existing Databricks tables:

| Property | Why it matters | How to see it |
|---|---|---|
| Managed or external | Managed tables live under catalog-owned storage; newer catalog-managed tables also route commits through the catalog. Reading them without Unity Catalog is not guaranteed. | `DESCRIBE TABLE EXTENDED` → `Type` |
| Delta table features | The open readers must support every reader feature in use (deletion vectors, column mapping, v2 checkpoints, type widening, variant, ...). | `DESCRIBE DETAIL` → `minReaderVersion`, `tableFeatures` |
| Storage location | Must be reachable by the open stack. | `DESCRIBE DETAIL` → `location` |

The [capability mapping](capability-mapping.md) and generated report record which table features and catalog behaviours are supported by each implementation.

## 2. Configure the target

Configure the OpenLakehouse implementation with its own object storage and Unity Catalog OSS catalog. Both implementations use the same logical catalog, schema and table names, while platform adapters own the storage URLs, credentials and session setup.

## 3. Run

Run the shared code with the OpenLakehouse entry point:

```bash
make pipeline SCALE=1                    # or: freedom pipeline --task silver --scale 1
```

The only code that changes is the code already isolated in `platforms/` (session, configuration, orchestration).

## 4. Validate

```bash
make freedom-check SCALE=1
make freedom-report SCALE=1
```

The check compares results with the official TPC-H answers, with the Databricks run when its results are present, and with two independent oracles (DuckDB SQL and plain Python).

## 5. Switch scheduling

Deploy `platforms/openlakehouse/airflow/dags/lakehouse_freedom.py` to Airflow (OpenLakehouse ships Airflow 3.1.6, `./lakehouse start airflow` in the submodule). The DAG is generated from the same task graph as the Databricks job. v1 checks this for consistency but does not execute it; see the limitations in the report.

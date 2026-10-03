# Freedom Check

```bash
make freedom-check SCALE=1
```

The Freedom Check validates that the workload keeps working without Databricks. Every check returns **PASS**, **FAIL** or **SKIP** together with the evidence. A failing check is reported as failing, and the command exits with code 1. No check switches to a platform-specific workaround to get a pass.

Results are written to `reports/freedom-check-sf<N>.json` and shown in section 4 of the [Freedom Report](report.md).

## The checks

| # | Check | What is verified | Evidence |
|---|---|---|---|
| 1 | Delta tables readable | Every Bronze, Silver, Gold and incremental table can be read by OSS Spark through UC OSS | live Spark read |
| 2 | Schemas compatible | Silver matches the canonical TPC-H schema, and the Databricks schema when it is available | `quality.json` |
| 3 | Expected row counts and keys | dbgen row counts, primary-key uniqueness and non-null, 7 foreign keys without orphans | `quality.json` |
| 4 | Transformation outputs equivalent | Silver equals DuckDB's independent conform of the Raw Parquet; Gold equals a DuckDB SQL re-implementation; Databricks fingerprints match when available | live DuckDB oracle |
| 5 | TPC-H results equivalent | All 22 queries correct on OSS Spark and DuckDB (and Databricks when available) | official answers or reference run |
| 6 | Spark transformations executable | Every pipeline task completed on OpenLakehouse Spark | run artefacts |
| 7 | Unity Catalog metadata accessible/recreated | UC OSS lists the tables with format and location; the [catalog probe](capability-mapping.md) recreates the Unity Catalog capabilities the workload uses | live UC OSS probe |
| 8 | DuckDB can access selected tables | DuckDB reads `lineitem` through a UC OSS-resolved location with the expected row count | live DuckDB read |
| 9 | Incremental pipeline works | Three batches applied incrementally; a duplicate batch is refused; replaying the last batch changes nothing | `scd2.json` |
| 10 | SCD2 behaviour equivalent | The SCD2 dimension equals a pure-Python oracle on every platform that ran | `scd2.json` vs oracle |
| 11 | Shared code has no Databricks-specific APIs | 21 scanner rules find nothing in shared code | static scan |
| 12 | Orchestration matches the shared task graph | Databricks job and Airflow DAG implement `src/common/pipeline.py` exactly | static check |
| 13 | Databricks reference run available | Databricks results present and all queries succeeded | SKIP until run |
| 14 | Freedom Day | Freedom Day passed for this scale factor | `freedom-day-sf<N>.json` |

## Independent oracles

A check that reuses the code under test proves little, so two oracles share no code with the Spark pipeline.

**DuckDB.** For every Silver table, a column profile (row count; per column: sum for numbers, total trimmed length for strings, sum of epoch days for dates) is computed by DuckDB twice: once from the Raw Parquet applying the conform rules in DuckDB SQL, and once from the Delta table Spark wrote. The Gold aggregate is recomputed in DuckDB SQL and compared row by row.

**Python.** `freedom/validation/scd2_reference.py` replays the change feed in plain Python. Its output is committed as `tests/data/scd2_expected.json`, and the SCD2 table from each platform must equal it.

## Comparing query results

Query results are compared value by value: numbers within an absolute tolerance of 0.01 (or 1e-9 relative), strings after trimming, dates as ISO strings. Rows are compared in order first and, if that fails, after sorting, so ties under `ORDER BY` with different physical order do not count as differences. The reference is, in order of preference:

1. the official TPC-H answers shipped with DuckDB's `tpch` extension (SF 0.01, 0.1 and 1),
2. the Databricks results, when fetched,
3. the OpenLakehouse Spark results.

The report states which reference each comparison used.

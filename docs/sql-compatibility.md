# SQL compatibility

The same 22 canonical TPC-H queries are executed against Delta tables through Databricks Spark, OpenLakehouse Spark, DuckDB, and optionally DataFusion.

## Current evidence

| Recorded SF10 run | Canonical queries passed | Adapted queries | Failed queries |
|---|---:|---:|---:|
| Databricks Spark | 22 | 0 | 0 |
| OpenLakehouse Spark | 22 | 0 | 0 |
| OpenLakehouse DuckDB | 22 | 0 | 0 |
| OpenLakehouse DataFusion | Not run | Not run | Not run |

The runner attempts canonical SQL first and compares results with reference answers. An engine-specific variant is counted as adapted, so dialect differences remain visible.

## Scope

TPC-H exercises joins, aggregates, subqueries, common table expressions, and date arithmetic. It is still a conservative analytical SQL workload. Passing it demonstrates compatibility for these queries and versions, not complete dialect parity across every Databricks SQL feature.

Query durations remain in the raw execution artifacts for diagnostics. They are not part of the platform comparison or documentation conclusions.

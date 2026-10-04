# Performance and compatibility

The benchmark runs the same 22 TPC-H queries against Delta tables through Databricks Spark, OpenLakehouse Spark, DuckDB, and optionally DataFusion.

## Current result

All 22 queries completed with correct results in the committed Databricks Spark, OpenLakehouse Spark, and DuckDB SF10 runs. No engine-specific SQL variants were needed for those recorded results.

| Recorded SF10 run | Total query time |
|---|---:|
| OpenLakehouse Spark, local Docker | 402.1 s |
| OpenLakehouse DuckDB, local process | 37.9 s |
| Databricks serverless Spark | 45.8 s |
| OpenLakehouse DataFusion | Not run |

## What the timings do and do not say

The local machine and Databricks serverless compute differ in hardware, runtime, caching, and repetitions. The totals therefore show execution characteristics, not which platform is faster.

A defensible platform comparison would require equivalent resources, controlled data placement and cache state, identical repetition and warm-up rules, cost reporting, and multiple runs. Until then, the benchmark supports compatibility claims only.

## Method

- TPC-H SF1 and SF10 data is generated with DuckDB's embedded `dbgen`.
- Canonical SQL is attempted first on every engine.
- Results are compared with reference answers.
- Timings include planning, execution, and result collection.
- Every result records versions and environment details.

See the [latest report](report.md#4-benchmark-results) for per-query timings and environments.

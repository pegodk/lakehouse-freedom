# Repository layout

```
portable-lakehouse/
├── src/                      shared workload code            → package portable_lakehouse
│   ├── common/               config, task graph, TPC-H schema, portable Delta IO
│   ├── ingestion/            Raw → Bronze, synthetic change feed
│   ├── transformations/      Silver, Gold (DataFrame API), SCD2 MERGE
│   ├── quality/              row counts, keys, FK integrity, fingerprints
│   └── run.py                task dispatcher: run_task(spark, cfg, key)
├── tpch/                                                     → portable_lakehouse.tpch
│   ├── generator/            DuckDB tpch extension (embedded dbgen), chunked
│   ├── queries/              q01–q22 canonical SQL; adapted/<engine>/ when needed
│   └── expected/             official answers for SF 0.01, 0.1 and 1
├── benchmarks/
│   ├── runner/               query runner: Spark, DuckDB, DataFusion → portable_lakehouse.benchmarks
│   └── results/              one JSON per query / platform / engine / scale
├── platforms/                                                → portable_lakehouse_platforms
│   ├── databricks/           Asset Bundle, job, entrypoint.py
│   └── openlakehouse/        stack/ (submodule), adapter, catalog, entrypoint, Airflow DAG, scripts, config
├── portability/                  tooling                         → package portability
│   ├── assessment/           inventory, scanner, capability mapping
│   ├── validation/           Portability Check, comparisons, catalog probe, SCD2 oracle
│   ├── reporting/            Portability Score and Portability Report
│   ├── benchmark.py  day.py  uc.py  cli.py
├── tests/                    data/, transformations/, portability/
├── docs/                     this site (Zensical)
├── reports/                  generated reports
├── zensical.toml
├── pyproject.toml
└── Makefile
```

The folders follow the original Portable Lakehouse specification. `pyproject.toml` maps them onto importable packages (right-hand column), so a single wheel built from the repository runs on Databricks and locally.

## What runs where

| Path | Databricks | OpenLakehouse | Classification in the inventory |
|---|---|---|---|
| `src/`, `tpch/`, `benchmarks/runner/` | yes | yes | shared |
| `platforms/databricks/` | yes | | databricks |
| `platforms/openlakehouse/` | | yes | openlakehouse |
| `portability/` | | developer machine | tooling, not scored |

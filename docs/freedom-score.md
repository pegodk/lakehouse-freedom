# Freedom Score

Every component of the Freedom Score is a ratio of measured counts, and the inputs are committed alongside the report. There are no subjective percentages. A component that could not be measured is shown as *not measured* and left out of the overall score. It is never counted as 0% or 100%.

```
LAKEHOUSE FREEDOM REPORT
────────────────────────────────
Data portability
████████████████████ 100%
TPC-H SQL portability (Spark)
████████████████████ 100%
Transformation portability
██████████████████░░  91%
Catalog portability
████████████░░░░░░░░  60%
Orchestration portability
██████████░░░░░░░░░░  51%
```

*(Shape of the output; current values are in the [latest report](report.md).)*

## Formulas

### Data portability

```
Delta tables read by OSS Spark and DuckDB with identical row counts after re-registration from storage
──────────────────────────────────────────────────────────────────────────────────────────────────────
Delta tables
```

Source: `reports/freedom-day-sf<N>.json`. Covers Bronze, Silver, Gold and the incremental tables (19 at present).

### TPC-H SQL portability

```
queries PORTABLE on the target engine
─────────────────────────────────────
22
```

PORTABLE means the canonical text ran unchanged **and** returned the reference result. Reported separately for OSS Spark (the migration target, included in the score) and DuckDB (an additional engine, shown but not included).

### Transformation portability

```
shared transformation LOC
─────────────────────────────────────────────────────────────────────
shared transformation LOC + OpenLakehouse-specific transformation LOC
```

The share of the code that runs the workload on OpenLakehouse that is identical to the code running it on Databricks. LOC are logical lines: blank lines, comments and docstrings are not counted. Classification of files: [`freedom/assessment/inventory.yaml`](https://github.com/pegodk/lakehouse-freedom/blob/main/freedom/assessment/inventory.yaml).

### Catalog portability

```
Unity Catalog capabilities recreated in UC OSS and read back
────────────────────────────────────────────────────────────
Unity Catalog capabilities used by the workload
```

Measured live by the catalog probe (catalogs, schemas, external tables, Spark-created column metadata, comments, properties, `ALTER TABLE`, REST registration, volumes, grants).

### Orchestration portability

```
shared orchestration LOC
───────────────────────────────────────────────────────────────────
shared orchestration LOC + OpenLakehouse-specific orchestration LOC
```

Shared: the task graph in `src/common/pipeline.py`. Platform-specific: the Airflow DAG (OpenLakehouse) and the job YAML (Databricks).

### Freedom Score

```
Freedom Score = mean(data, SQL (Spark), transformation, catalog, orchestration)
```

An unweighted mean of the measured components. The weighting is deliberately naive. Read the components; the single number only summarises them.

## What the score does not measure

- **Effort.** Lines-of-code ratios show how much is shared. They don't show how hard the non-shared part is to write.
- **Workloads other than this one.** TPC-H is a conservative SQL subset. Run `make freedom-assess REPO_PATH=...` on your own code for a first impression.
- **Operations.** Running a Spark cluster yourself costs effort that a managed platform absorbs. That is Principle F6, and it is outside the score.

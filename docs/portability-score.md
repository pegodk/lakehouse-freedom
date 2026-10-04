# Portability Score

The Portability Score is the first summary of the measured comparison between the two reference architectures. Every component is a ratio of measured counts, and the inputs are committed alongside the report. There are no subjective percentages. A component that could not be measured is shown as *not measured* and left out of the overall score. It is never counted as 0% or 100%.

```
PORTABLE LAKEHOUSE REPORT
────────────────────────────────
Transformation portability
██████████████████░░  91%
Catalog portability
████████████░░░░░░░░  60%
Orchestration portability
██████████░░░░░░░░░░  51%
Governance portability
██████████░░░░░░░░░░  50%
```

*(Shape of the output; current values are in the [latest report](report.md).)*

## Formulas

### Transformation portability

```
shared transformation LOC
─────────────────────────────────────────────────────────────────────
shared transformation LOC + OpenLakehouse-specific transformation LOC
```

The share of workload code used by the OpenLakehouse implementation that is also used by the Databricks implementation. LOC are logical lines: blank lines, comments and docstrings are not counted. Classification of files: [`portability/assessment/inventory.yaml`](https://github.com/pegodk/portable-lakehouse/blob/main/portability/assessment/inventory.yaml).

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

### Governance portability

```
reviewed obligations enforced by the DataFusion adapter
───────────────────────────────────────────────────────────
reviewed obligations in governance/obligations.yaml
```

The current registry contains tenant row isolation and email masking. The DataFusion adapter enforces email masking and fails closed for tenant isolation, so governance portability is 1/2 (50%). This metric measures the implemented obligation boundary; it does not represent production identity integration, gateway hardening, or every governance capability.

### Portability Score

```
Portability Score = mean(transformation, catalog, orchestration, governance)
```

An unweighted mean of the measured components. The weighting is deliberately naive. Read the components; the single number only summarises them.

## What the score does not measure

- **Effort.** Lines-of-code ratios show how much is shared. They don't show how hard the non-shared part is to write.
- **Workloads other than this one.** TPC-H is a conservative SQL subset. Run `make portability-assess REPO_PATH=...` on your own code for a first impression.
- **Operations.** Running a Spark cluster yourself costs effort that a managed platform absorbs. That is Principle F6, and it is outside the score.

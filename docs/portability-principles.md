# Portability principles

These guidelines apply whether a team chooses Databricks, an open stack, or both.

## 1. Own the data

Keep business data in an open table format on object storage you control where practical. Catalogs should point to the data, not become the only route to it.

**Evidence here:** external Delta tables were read through Spark and DuckDB without conversion.

## 2. Separate business logic from platform logic

Keep transformations independent from session creation, paths, credentials, compute sizing, and scheduling.

**Evidence here:** 89% of measured transformation code is shared; platform adapters contain the environment-specific code.

## 3. Prefer open interfaces

Use stable interfaces such as Spark SQL, the PySpark DataFrame API, Delta SQL, MLflow APIs, catalog APIs, and object-storage APIs when they meet the need.

Open interfaces reduce dependency. They do not guarantee identical behaviour, so test the combinations you rely on.

## 4. Isolate managed capabilities

Managed features are valid architectural choices. Put their use behind clear boundaries so the benefit, dependency, and replacement cost remain visible.

## 5. Test portability

A component being open source does not prove the system is portable. Execute important workloads in a second environment and compare results, metadata, and operational assumptions.

## 6. Do not confuse portability with equivalence

Preserving data and core logic is valuable even when governance or user experience differs. Judge each capability separately.

## 7. Allow managed services to be better

Databricks may be the better choice for serverless compute, governance, observability, and integrated operations. Portability means choosing those advantages deliberately while protecting the data and logic that should outlive the platform.

## A practical review

For every important lakehouse capability, ask:

1. Who owns the data and metadata?
2. Which interface does business logic depend on?
3. What is platform-specific, and where is it isolated?
4. Has the workload run elsewhere with equivalent results?
5. Which managed benefit would be lost, and is that trade-off acceptable?

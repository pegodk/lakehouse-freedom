# ML lifecycle

Databricks managed MLflow and MLflow OSS share public tracking APIs. The same workload successfully logged and read back parameters, metrics, tags, and an artifact by changing only the tracking URI.

That demonstrates **tracking portability**, not ML-platform equivalence.

| Capability | Finding |
|---|---|
| Experiment and run tracking | Native OSS counterpart; measured here |
| Artifact storage | Native OSS counterpart; measured here |
| Model packaging, registry, tracing | Available in MLflow OSS; not exercised here |
| Catalog-aware registry governance | Requires explicit integration |
| Managed service operations | Operator responsibility in OSS |
| Feature engineering and model serving | Separate services; not reproduced here |

The lesson is broader than MLflow: an open API can preserve workload code while leaving identity, governance, availability, and operations platform-specific.

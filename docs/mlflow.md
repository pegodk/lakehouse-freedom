# Portable MLflow tracking

Freedom Challenge #5 now has an executable tracking foundation. The shared
workload logs parameters, metrics, tags and an artifact, then reads the run
back to produce `reports/mlflow-tracking.json` as measured evidence.

Install the ML dependency and run a local smoke test:

```bash
uv pip install --python .venv/bin/python -e '.[ml]'
make mlflow-smoke
```

The default `sqlite:///mlflow.db` URI needs no service. Point the same workload at an
MLflow OSS server or another MLflow-compatible backend with:

```bash
make mlflow-smoke MLFLOW_TRACKING_URI=http://localhost:5000
```

For Databricks, use a configured Databricks MLflow tracking URI and credentials.
The workload contains no platform branch: backend selection is configuration.

This foundation measures experiment and artifact tracking. Model registry,
feature engineering and model serving remain separate Challenge #5 gaps.

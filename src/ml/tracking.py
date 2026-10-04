"""A small, platform-neutral MLflow experiment-tracking workload.

The workload deliberately uses only public MLflow APIs.  The tracking URI is
configuration: it can point at MLflow OSS, Databricks managed MLflow, or a
local file store for a quick smoke test.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def run_tracking_workload(
    tracking_uri: str,
    experiment_name: str = "portable-lakehouse",
    output: Path | None = None,
) -> dict[str, Any]:
    """Log and read back one MLflow run, returning portable evidence."""
    try:
        import mlflow
    except ImportError as exc:  # pragma: no cover - exercised by the CLI installation
        raise RuntimeError("MLflow is not installed; install the 'ml' extra") from exc

    mlflow.set_tracking_uri(tracking_uri)
    mlflow.set_experiment(experiment_name)
    with mlflow.start_run(run_name="portable-tracking-smoke") as active:
        mlflow.log_params({"workload": "tracking-smoke", "api": "mlflow"})
        mlflow.log_metrics({"records": 3.0, "portability_score": 1.0})
        mlflow.set_tags({
            "portable_lakehouse.capability": "experiment-tracking",
            "portable_lakehouse.portable": "true",
        })
        mlflow.log_text("portable MLflow artifact\n", "evidence/readme.txt")
        run_id = active.info.run_id
        experiment_id = active.info.experiment_id

    client = mlflow.MlflowClient(tracking_uri=tracking_uri)
    saved = client.get_run(run_id)
    artifacts = client.list_artifacts(run_id, "evidence")
    evidence = {
        "tracking_uri": tracking_uri,
        "experiment": experiment_name,
        "experiment_id": experiment_id,
        "run_id": run_id,
        "status": saved.info.status,
        "params": dict(saved.data.params),
        "metrics": dict(saved.data.metrics),
        "tags": {k: v for k, v in saved.data.tags.items() if k.startswith("portable_lakehouse.")},
        "artifacts": sorted(item.path for item in artifacts),
    }
    if output is not None:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(evidence, indent=2) + "\n")
    return evidence

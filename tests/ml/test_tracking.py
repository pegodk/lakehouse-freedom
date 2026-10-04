from pathlib import Path
from types import SimpleNamespace

from lakehouse_freedom.ml.tracking import run_tracking_workload


class FakeMlflow:
    def __init__(self):
        self.data = SimpleNamespace(params={}, metrics={}, tags={})
        self.info = SimpleNamespace(run_id="run-1", experiment_id="exp-1", status="FINISHED")

    def set_tracking_uri(self, uri):
        self.uri = uri

    def set_experiment(self, name):
        self.experiment = name

    def start_run(self, run_name):
        info = self.info

        class RunContext:
            def __enter__(self):
                return SimpleNamespace(info=info)

            def __exit__(self, *_):
                return None

        return RunContext()

    def log_params(self, values):
        self.data.params.update(values)

    def log_metrics(self, values):
        self.data.metrics.update(values)

    def set_tags(self, values):
        self.data.tags.update(values)

    def log_text(self, text, path):
        self.artifact = SimpleNamespace(path=path)

    def MlflowClient(self, tracking_uri):
        return SimpleNamespace(
            get_run=lambda _: SimpleNamespace(info=self.info, data=self.data),
            list_artifacts=lambda *_: [self.artifact],
        )


def test_tracking_workload_logs_and_reads_back(monkeypatch, tmp_path: Path):
    fake = FakeMlflow()
    monkeypatch.setitem(__import__("sys").modules, "mlflow", fake)
    output = tmp_path / "evidence.json"

    evidence = run_tracking_workload("sqlite:///test.db", output=output)

    assert evidence["status"] == "FINISHED"
    assert evidence["metrics"]["portability_score"] == 1.0
    assert evidence["artifacts"] == ["evidence/readme.txt"]
    assert output.exists()

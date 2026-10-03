from pathlib import Path

import yaml

from lakehouse_freedom.common.pipeline import TASKS, topological_order

REPO = Path(__file__).resolve().parents[2]


def test_graph_is_acyclic_and_complete():
    order = topological_order()
    assert sorted(order) == sorted(t.key for t in TASKS)
    assert order.index("bronze") < order.index("silver") < order.index("gold")


def test_databricks_job_matches_shared_graph():
    job = yaml.safe_load((REPO / "platforms/databricks/resources/lakehouse_freedom.job.yml").read_text())
    tasks = job["resources"]["jobs"]["lakehouse_freedom"]["tasks"]
    graph = {t["task_key"]: tuple(d["task_key"] for d in t.get("depends_on", [])) for t in tasks}
    assert graph == {t.key: t.depends_on for t in TASKS}
    for t in tasks:
        assert t["spark_python_task"]["parameters"][0] == t["task_key"]


def test_airflow_dag_is_generated_from_shared_graph():
    src = (REPO / "platforms/openlakehouse/airflow/dags/lakehouse_freedom.py").read_text()
    assert "from lakehouse_freedom.common.pipeline import TASKS" in src

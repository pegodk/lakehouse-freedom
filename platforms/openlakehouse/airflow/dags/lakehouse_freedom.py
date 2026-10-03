"""Airflow 3 DAG for the shared pipeline graph on OpenLakehouse.

Built from lakehouse_freedom.common.pipeline.TASKS, so it cannot drift from the
Databricks job. Each task runs the OpenLakehouse entry point, which talks to
Spark Connect. Inside the OpenLakehouse Docker network set:

    FREEDOM_SPARK_REMOTE=sc://spark-connect-41:15002
    FREEDOM_UC_URL=http://unity-catalog:8080
    FREEDOM_S3_ENDPOINT=seaweedfs:8333

and install this repository into the Airflow image (pip install /opt/lakehouse-freedom).
"""

from __future__ import annotations

import pendulum
from airflow.providers.standard.operators.bash import BashOperator
from airflow.sdk import DAG, Param

from lakehouse_freedom.common.pipeline import TASKS

with DAG(
    dag_id="lakehouse_freedom",
    description="Lakehouse Freedom TPC-H pipeline on OpenLakehouse",
    schedule=None,
    start_date=pendulum.datetime(2026, 1, 1, tz="UTC"),
    catchup=False,
    params={"scale": Param(1, type="number")},
    tags=["lakehouse-freedom"],
) as dag:
    operators = {
        t.key: BashOperator(
            task_id=t.key,
            doc=t.description,
            bash_command=(
                "python -m freedom_platforms.openlakehouse.entrypoint "
                f"{t.key} --scale {{{{ params.scale }}}}"
            ),
        )
        for t in TASKS
    }
    for t in TASKS:
        for upstream in t.depends_on:
            operators[upstream] >> operators[t.key]

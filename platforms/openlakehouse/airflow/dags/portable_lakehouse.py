"""Airflow 3 DAG for the shared pipeline graph on OpenLakehouse.

Built from portable_lakehouse.common.pipeline.TASKS, so it cannot drift from the
Databricks job. Each task runs the OpenLakehouse entry point, which talks to
Spark Connect. Inside the OpenLakehouse Docker network set:

    PORTABLE_LAKEHOUSE_SPARK_REMOTE=sc://spark-connect-41:15002
    PORTABLE_LAKEHOUSE_UC_URL=http://unity-catalog:8080
    PORTABLE_LAKEHOUSE_S3_ENDPOINT=seaweedfs:8333

and install this repository into the Airflow image (pip install /opt/portable-lakehouse).
"""

from __future__ import annotations

import pendulum
from airflow.providers.standard.operators.bash import BashOperator
from airflow.sdk import DAG, Param

from portable_lakehouse.common.pipeline import TASKS

with DAG(
    dag_id="portable_lakehouse",
    description="Portable Lakehouse TPC-H pipeline on OpenLakehouse",
    schedule=None,
    start_date=pendulum.datetime(2026, 1, 1, tz="UTC"),
    catchup=False,
    params={"scale": Param(1, type="number")},
    tags=["portable-lakehouse"],
) as dag:
    operators = {
        t.key: BashOperator(
            task_id=t.key,
            doc=t.description,
            bash_command=(
                "python -m portable_lakehouse_platforms.openlakehouse.entrypoint "
                f"{t.key} --scale {{{{ params.scale }}}}"
            ),
        )
        for t in TASKS
    }
    for t in TASKS:
        for upstream in t.depends_on:
            operators[upstream] >> operators[t.key]

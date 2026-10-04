"""OpenLakehouse platform adapter.

Everything Portable Lakehouse needs to know about the local OpenLakehouse stack
lives here: endpoints, credentials, storage roots, and how to discover the
versions of the running components. Versions are read from the pinned
submodule's own files rather than hard-coded.
"""

from __future__ import annotations

import os
import platform as host_platform
import re
import subprocess
from pathlib import Path

STACK = Path(__file__).resolve().parent / "stack"
REPO = Path(__file__).resolve().parents[2]

SPARK_REMOTE = os.environ.get("PORTABLE_LAKEHOUSE_SPARK_REMOTE", "sc://localhost:15002")
UC_URL = os.environ.get("PORTABLE_LAKEHOUSE_UC_URL", "http://localhost:8081")
S3_ENDPOINT_HOST = os.environ.get("PORTABLE_LAKEHOUSE_S3_ENDPOINT", "localhost:8333")
S3_ACCESS_KEY = os.environ.get("S3_ACCESS_KEY", "lakehouse_s3")
S3_SECRET_KEY = os.environ.get("S3_SECRET_KEY", "lakehouse_s3_secret")

RAW_ROOT = "s3://lakehouse/portable-lakehouse/raw"
TABLE_ROOT = "s3://lakehouse/portable-lakehouse/tables"
RESULTS_ROOT = str(REPO / "benchmarks" / "results")
CATALOG = "portable_lakehouse"


def spark_session():
    from pyspark.sql import SparkSession

    return SparkSession.builder.remote(SPARK_REMOTE).getOrCreate()


def duckdb_s3_setup(con) -> None:
    """Point DuckDB's httpfs/delta readers at SeaweedFS."""
    con.execute("INSTALL httpfs; LOAD httpfs;")
    con.execute(
        f"""CREATE OR REPLACE SECRET portable_lakehouse_s3 (
            TYPE s3, KEY_ID '{S3_ACCESS_KEY}', SECRET '{S3_SECRET_KEY}',
            ENDPOINT '{S3_ENDPOINT_HOST}', URL_STYLE 'path', USE_SSL false, REGION 'us-east-1')"""
    )


def delta_rs_s3_options() -> dict[str, str]:
    """Object-store options used by delta-rs and its DataFusion Arrow dataset."""
    return {
        "AWS_ACCESS_KEY_ID": S3_ACCESS_KEY,
        "AWS_SECRET_ACCESS_KEY": S3_SECRET_KEY,
        "AWS_ENDPOINT_URL": f"http://{S3_ENDPOINT_HOST}",
        "AWS_REGION": "us-east-1",
        "AWS_ALLOW_HTTP": "true",
        "AWS_S3_ADDRESSING_STYLE": "path",
    }


def boto3_client():
    import boto3

    return boto3.client(
        "s3",
        endpoint_url=f"http://{S3_ENDPOINT_HOST}",
        aws_access_key_id=S3_ACCESS_KEY,
        aws_secret_access_key=S3_SECRET_KEY,
        region_name="us-east-1",
    )


def _read(path: Path) -> str:
    return path.read_text() if path.exists() else ""


def discover_versions() -> dict:
    """Component versions as pinned by the OpenLakehouse checkout."""
    defaults = _read(STACK / "config/spark/spark-defaults.conf") or _read(
        STACK / "config/spark/spark-defaults.conf.example"
    )

    def jar(pattern: str) -> str | None:
        m = re.search(pattern, defaults)
        return m.group(1) if m else None

    def image(file: str, name: str) -> str | None:
        m = re.search(rf"image:\s*{re.escape(name)}:(\S+)", _read(STACK / file))
        return m.group(1) if m else None

    try:
        commit = subprocess.run(
            ["git", "-C", str(STACK), "rev-parse", "HEAD"], capture_output=True, text=True, check=True
        ).stdout.strip()
    except Exception:
        commit = None

    return {
        "openlakehouse_repo": "https://github.com/open-lakehouse/open-lakehouse",
        "openlakehouse_commit": commit,
        "spark_image": image("docker-compose-spark41.yml", "apache/spark"),
        "delta_version": jar(r"delta-spark_2\.13-([\d.]+)\.jar"),
        "unitycatalog_spark_connector": jar(r"unitycatalog-spark_2\.13-([\d.]+)\.jar"),
        "unitycatalog_server": image("docker-compose-unity-catalog.yml", "unitycatalog/unitycatalog"),
        "seaweedfs": image("docker-compose-storage.yml", "chrislusf/seaweedfs"),
        "postgres": image("docker-compose-storage.yml", "postgres"),
    }


def spark_resources() -> dict:
    conf = _read(STACK / "config/spark/spark-defaults.conf")
    keys = ["spark.executor.cores", "spark.executor.memory", "spark.driver.memory",
            "spark.sql.shuffle.partitions"]
    found = {}
    for key in keys:
        matches = re.findall(rf"^{re.escape(key)}\s+(\S+)", conf, flags=re.M)
        if matches:
            found[key] = matches[-1]  # last definition wins, as in Spark
    return found


def host_resources() -> dict:
    mem_gb = None
    try:
        with open("/proc/meminfo") as fh:
            kb = int(next(line for line in fh if line.startswith("MemTotal")).split()[1])
            mem_gb = round(kb / 1024 / 1024, 1)
    except Exception:
        pass
    return {"host_cpus": os.cpu_count(), "host_memory_gb": mem_gb,
            "host_os": f"{host_platform.system()} {host_platform.release()}"}


def environment() -> dict:
    return {
        "platform_label": "OpenLakehouse (local Docker)",
        "compute": "Spark standalone: 1 master, 1 worker, Spark Connect server, all on one host",
        **discover_versions(),
        "spark_conf": spark_resources(),
        **host_resources(),
    }


def config(scale_factor: float):
    from portable_lakehouse.common.config import LakehouseConfig

    return LakehouseConfig(
        platform="openlakehouse",
        scale_factor=scale_factor,
        raw_root=RAW_ROOT,
        table_root=TABLE_ROOT,
        results_root=RESULTS_ROOT,
        catalog=CATALOG,
        engine_info=environment(),
    )

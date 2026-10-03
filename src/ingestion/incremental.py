"""A small synthetic change feed for the incremental / SCD2 scenario.

TPC-H is a static snapshot, so it cannot exercise incremental loads or slowly
changing dimensions. These three deterministic batches cover inserts, updates,
no-op repeats, deletes and re-inserts. They are defined in code so every
platform ingests byte-identical input.
"""

from __future__ import annotations

from pyspark.sql import SparkSession
from pyspark.sql import functions as F

from lakehouse_freedom.common.config import FreedomConfig
from lakehouse_freedom.common.delta_io import create_table_if_missing, ensure_schema

# (batch_id, effective_date, [(op, customer_id, name, segment, city), ...])
# op: U = upsert (insert or change), D = delete
BATCHES: list[tuple[int, str, list[tuple[str, int, str, str, str]]]] = [
    (1, "2024-01-01", [
        ("U", 1, "Ada", "BUILDING", "Copenhagen"),
        ("U", 2, "Grace", "MACHINERY", "Aarhus"),
        ("U", 3, "Linus", "AUTOMOBILE", "Odense"),
        ("U", 4, "Margaret", "HOUSEHOLD", "Aalborg"),
        ("U", 5, "Edsger", "FURNITURE", "Esbjerg"),
        ("U", 6, "Barbara", "BUILDING", "Vejle"),
    ]),
    (2, "2024-02-01", [
        ("U", 2, "Grace", "MACHINERY", "Copenhagen"),   # moved
        ("U", 3, "Linus", "AUTOMOBILE", "Odense"),      # unchanged repeat: no new version
        ("U", 5, "Edsger", "FURNITURE", "Roskilde"),    # moved
        ("D", 6, "Barbara", "BUILDING", "Vejle"),       # closed
        ("U", 7, "Ken", "MACHINERY", "Horsens"),        # new
    ]),
    (3, "2024-03-01", [
        ("U", 2, "Grace", "AUTOMOBILE", "Copenhagen"),  # segment change
        ("U", 6, "Barbara", "BUILDING", "Kolding"),     # re-activated after delete
        ("U", 7, "Kenneth", "MACHINERY", "Horsens"),    # renamed
    ]),
]

CHANGES_COLUMNS = (
    "batch_id INT, effective_date DATE, op STRING, customer_id BIGINT, "
    "name STRING, segment STRING, city STRING"
)


def batch_frame(spark: SparkSession, batch_id: int):
    _, effective, rows = next(b for b in BATCHES if b[0] == batch_id)
    data = [(batch_id, effective, *r) for r in rows]
    return spark.createDataFrame(
        data, "batch_id INT, effective_date STRING, op STRING, customer_id BIGINT, "
        "name STRING, segment STRING, city STRING",
    ).withColumn("effective_date", F.to_date("effective_date"))


def ingest_batch(spark: SparkSession, cfg: FreedomConfig, batch_id: int) -> bool:
    """Append one batch to the bronze change log. Returns False if already loaded."""
    ensure_schema(spark, cfg.catalog, cfg.incremental_schema)
    name = cfg.table_name(cfg.incremental_schema, "customer_changes")
    create_table_if_missing(
        spark,
        name,
        CHANGES_COLUMNS,
        cfg.table_location(cfg.incremental_schema, "customer_changes"),
        comment="Bronze change feed for the SCD2 scenario",
        properties={"freedom.layer": "bronze"},
    )
    already = spark.table(name).where(F.col("batch_id") == batch_id).limit(1).count() > 0
    if already:
        return False
    batch_frame(spark, batch_id).writeTo(name).append()
    return True

"""Slowly changing dimension type 2 with a single portable MERGE.

Validity dates come from the data (effective_date), never from the clock, so
the resulting table is deterministic and can be compared across platforms and
against tests/data/scd2_expected.json.
"""

from __future__ import annotations

from pyspark.sql import SparkSession

from lakehouse_freedom.common.config import FreedomConfig
from lakehouse_freedom.common.delta_io import create_table_if_missing

SCD2_COLUMNS = (
    "customer_id BIGINT, name STRING, segment STRING, city STRING, "
    "valid_from DATE, valid_to DATE, is_current BOOLEAN, record_hash STRING"
)


def merge_sql(target: str, changes: str, batch_id: int) -> str:
    staged = f"""
        SELECT customer_id, name, segment, city, effective_date, op,
               sha2(concat_ws('||', name, segment, city), 256) AS record_hash
        FROM {changes} WHERE batch_id = {batch_id}
    """
    # Each change appears twice: once keyed (to close the current version) and,
    # for upserts that differ from the current version, once unkeyed (to insert
    # the new version). Classic Delta SCD2 pattern; ANSI MERGE only.
    return f"""
    MERGE INTO {target} AS t
    USING (
        SELECT s.customer_id AS merge_key, s.* FROM ({staged}) s
        UNION ALL
        SELECT CAST(NULL AS BIGINT) AS merge_key, s.*
        FROM ({staged}) s
        JOIN {target} c
          ON s.customer_id = c.customer_id AND c.is_current
        WHERE s.op = 'U' AND s.record_hash <> c.record_hash
    ) AS u
    ON t.customer_id = u.merge_key AND t.is_current
    WHEN MATCHED AND (u.op = 'D' OR t.record_hash <> u.record_hash) THEN
      UPDATE SET is_current = false, valid_to = u.effective_date
    WHEN NOT MATCHED AND u.op = 'U' THEN
      INSERT (customer_id, name, segment, city, valid_from, valid_to, is_current, record_hash)
      VALUES (u.customer_id, u.name, u.segment, u.city, u.effective_date, NULL, true, u.record_hash)
    """


def apply_batch(spark: SparkSession, cfg: FreedomConfig, batch_id: int) -> None:
    target = cfg.table_name(cfg.incremental_schema, "customer_scd2")
    create_table_if_missing(
        spark,
        target,
        SCD2_COLUMNS,
        cfg.table_location(cfg.incremental_schema, "customer_scd2"),
        comment="Customer dimension, SCD type 2",
        properties={"freedom.layer": "silver"},
    )
    changes = cfg.table_name(cfg.incremental_schema, "customer_changes")
    spark.sql(merge_sql(target, changes, batch_id))


def snapshot(spark: SparkSession, cfg: FreedomConfig) -> list[dict]:
    rows = spark.sql(
        f"SELECT customer_id, name, segment, city, CAST(valid_from AS STRING) AS valid_from, "
        f"CAST(valid_to AS STRING) AS valid_to, is_current "
        f"FROM {cfg.table_name(cfg.incremental_schema, 'customer_scd2')} "
        f"ORDER BY customer_id, valid_from"
    ).collect()
    return [r.asDict() for r in rows]

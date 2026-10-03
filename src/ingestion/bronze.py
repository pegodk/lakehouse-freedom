"""Raw Parquet -> Bronze Delta.

Bronze keeps the generated columns untouched and adds lineage columns. Columns
prefixed with an underscore are operational metadata and are excluded from
cross-platform equivalence checks (they legitimately differ per run).
"""

from __future__ import annotations

from pyspark.sql import DataFrame, SparkSession
from pyspark.sql import functions as F

from lakehouse_freedom.common.config import FreedomConfig
from lakehouse_freedom.common.delta_io import ensure_schema, write_table
from lakehouse_freedom.common.tpch_schema import TABLES


def add_lineage(df: DataFrame, batch_id: str) -> DataFrame:
    return df.select(
        "*",
        F.col("_metadata.file_path").alias("_source_file"),
        F.lit(batch_id).alias("_batch_id"),
        F.current_timestamp().alias("_ingested_at"),
    )


def build_bronze(spark: SparkSession, cfg: FreedomConfig, batch_id: str) -> dict[str, int]:
    ensure_schema(spark, cfg.catalog, cfg.bronze_schema)
    counts = {}
    for table in TABLES:
        raw = spark.read.parquet(cfg.raw_path(table))
        write_table(
            spark,
            add_lineage(raw, batch_id),
            cfg.table_name(cfg.bronze_schema, table),
            cfg.table_location(cfg.bronze_schema, table),
            comment=f"TPC-H {table}, raw generator output with lineage columns",
            properties={"freedom.layer": "bronze", "freedom.source": "tpch-dbgen"},
        )
        counts[table] = spark.table(cfg.table_name(cfg.bronze_schema, table)).count()
    return counts

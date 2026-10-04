"""Bronze -> Silver: conform every TPC-H table to the canonical schema.

Pure DataFrame transformations (F2): they take and return DataFrames and know
nothing about catalogs, storage, clusters or orchestration.
"""

from __future__ import annotations

from pyspark.sql import DataFrame, SparkSession
from pyspark.sql import functions as F

from portable_lakehouse.common.config import LakehouseConfig
from portable_lakehouse.common.delta_io import ensure_schema, write_table
from portable_lakehouse.common.tpch_schema import TABLES, TPCH_SCHEMA


def conform(df: DataFrame, table: str) -> DataFrame:
    """Project to the canonical TPC-H columns and types, dropping lineage columns."""
    columns = []
    for name, sql_type in TPCH_SCHEMA[table]:
        col = F.col(name).cast(sql_type)
        if sql_type == "STRING":
            col = F.trim(col)
        columns.append(col.alias(name))
    return df.select(*columns)


def build_silver(spark: SparkSession, cfg: LakehouseConfig) -> dict[str, int]:
    ensure_schema(spark, cfg.catalog, cfg.silver_schema)
    counts = {}
    for table in TABLES:
        bronze = spark.table(cfg.table_name(cfg.bronze_schema, table))
        name = cfg.table_name(cfg.silver_schema, table)
        write_table(
            spark,
            conform(bronze, table),
            name,
            cfg.table_location(cfg.silver_schema, table),
            comment=f"TPC-H {table}, conformed to the TPC-H v3 schema",
            properties={"portable_lakehouse.layer": "silver"},
        )
        counts[table] = spark.table(name).count()
    return counts

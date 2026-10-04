"""Portable Delta table IO.

These helpers use only statements that behave the same on Databricks (Unity
Catalog) and on open-source Spark + Delta + Unity Catalog OSS. Several more
convenient statements are deliberately avoided; see docs/capability-mapping.md:

* CREATE OR REPLACE TABLE ... LOCATION   rejected by the UC OSS 0.5 connector
* ALTER TABLE ... (comments, properties) rejected by the UC OSS 0.5 connector
* ANALYZE TABLE                          not supported for UC OSS (v2) tables

Instead: create once (with comment and properties at creation time), then
INSERT OVERWRITE for full refreshes and MERGE for incremental changes.
"""

from __future__ import annotations

from pyspark.sql import DataFrame, SparkSession


def quote_props(properties: dict[str, str] | None) -> str:
    if not properties:
        return ""
    body = ", ".join(f"'{k}' = '{v}'" for k, v in sorted(properties.items()))
    return f" TBLPROPERTIES ({body})"


def ensure_schema(spark: SparkSession, catalog: str, schema: str) -> None:
    spark.sql(f"CREATE SCHEMA IF NOT EXISTS {catalog}.{schema}")


def table_exists(spark: SparkSession, name: str) -> bool:
    return spark.catalog.tableExists(name)


def write_table(
    spark: SparkSession,
    df: DataFrame,
    name: str,
    location: str | None,
    comment: str | None = None,
    properties: dict[str, str] | None = None,
) -> None:
    """Full refresh of a Delta table: create on first write, INSERT OVERWRITE after."""
    view = "_portable_lakehouse_" + name.replace(".", "_")
    df.createOrReplaceTempView(view)
    try:
        if table_exists(spark, name):
            spark.sql(f"INSERT OVERWRITE {name} SELECT * FROM {view}")
            return
        loc = f" LOCATION '{location}'" if location else ""
        cmt = f" COMMENT '{comment}'" if comment else ""
        spark.sql(
            f"CREATE TABLE {name} USING DELTA{loc}{cmt}{quote_props(properties)} "
            f"AS SELECT * FROM {view}"
        )
    finally:
        spark.catalog.dropTempView(view)


def create_table_if_missing(
    spark: SparkSession,
    name: str,
    columns_ddl: str,
    location: str | None,
    comment: str | None = None,
    properties: dict[str, str] | None = None,
) -> None:
    loc = f" LOCATION '{location}'" if location else ""
    cmt = f" COMMENT '{comment}'" if comment else ""
    spark.sql(
        f"CREATE TABLE IF NOT EXISTS {name} ({columns_ddl}) USING DELTA{loc}{cmt}"
        f"{quote_props(properties)}"
    )

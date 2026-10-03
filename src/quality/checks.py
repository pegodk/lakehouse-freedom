"""Data quality and equivalence fingerprints for the Silver layer.

Fingerprints are computed with plain Spark SQL aggregates (count, sum, a hash
sum over every column), so the same function produces comparable numbers on
Databricks and on open-source Spark. Two platforms holding the same data
produce identical fingerprints.
"""

from __future__ import annotations

from functools import reduce
from operator import or_

from pyspark.sql import DataFrame, SparkSession
from pyspark.sql import functions as F

from lakehouse_freedom.common.config import FreedomConfig
from lakehouse_freedom.common.tpch_schema import (
    FOREIGN_KEYS,
    PRIMARY_KEYS,
    TABLES,
    TPCH_SCHEMA,
    expected_row_count,
)


def fingerprint(df: DataFrame) -> dict:
    """Order-independent content fingerprint of a DataFrame.

    hash_sum adds xxhash64 over all non-metadata columns as DECIMAL(38,0), so it
    does not overflow under ANSI mode and is identical for identical row sets.
    """
    cols = sorted(c for c in df.columns if not c.startswith("_"))
    row = df.select(
        F.count(F.lit(1)).alias("rows"),
        F.sum(F.xxhash64(*[F.col(c) for c in cols]).cast("decimal(38,0)")).alias("hash_sum"),
    ).collect()[0]
    return {"rows": int(row["rows"]), "hash_sum": str(row["hash_sum"]), "columns": cols}


def schema_of(df: DataFrame) -> list[tuple[str, str]]:
    return [(f.name, f.dataType.simpleString()) for f in df.schema.fields]


def run_quality(spark: SparkSession, cfg: FreedomConfig) -> dict:
    """Row counts, keys, referential integrity and schema conformance for Silver."""
    results: dict = {"tables": {}, "foreign_keys": []}
    for table in TABLES:
        df = spark.table(cfg.table_name(cfg.silver_schema, table))
        pk = PRIMARY_KEYS[table]
        stats = df.agg(
            F.count(F.lit(1)).alias("rows"),
            F.count_distinct(*[F.col(c) for c in pk]).alias("distinct_pk"),
            F.sum(F.when(reduce(or_, [F.col(c).isNull() for c in pk]), 1).otherwise(0)).alias(
                "null_pk"
            ),
        ).collect()[0]
        expected_schema = TPCH_SCHEMA[table]
        actual_schema = schema_of(df)
        results["tables"][table] = {
            "rows": int(stats["rows"]),
            "expected_rows": expected_row_count(table, cfg.scale_factor),
            "pk_unique": int(stats["distinct_pk"]) == int(stats["rows"]),
            "pk_not_null": int(stats["null_pk"] or 0) == 0,
            "schema": actual_schema,
            "schema_matches": _normalise(actual_schema) == _normalise(expected_schema),
            "fingerprint": fingerprint(df),
        }
    for child, child_col, parent, parent_col in FOREIGN_KEYS:
        c = spark.table(cfg.table_name(cfg.silver_schema, child))
        p = spark.table(cfg.table_name(cfg.silver_schema, parent))
        orphans = c.join(p, c[child_col] == p[parent_col], "left_anti").count()
        results["foreign_keys"].append(
            {"child": f"{child}.{child_col}", "parent": f"{parent}.{parent_col}", "orphans": orphans}
        )
    return results


def _normalise(schema: list[tuple[str, str]]) -> list[tuple[str, str]]:
    aliases = {"integer": "int", "long": "bigint", "string": "string"}
    return [(c, aliases.get(t.lower(), t.lower())) for c, t in schema]

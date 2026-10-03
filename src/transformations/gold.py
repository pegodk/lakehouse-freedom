"""Silver -> Gold: a business aggregate written with the DataFrame API.

The TPC-H queries exercise SQL. This module exercises the other common style,
PySpark DataFrame code, so that both are covered by the portability checks.
"""

from __future__ import annotations

from pyspark.sql import DataFrame, SparkSession
from pyspark.sql import functions as F

from lakehouse_freedom.common.config import FreedomConfig
from lakehouse_freedom.common.delta_io import ensure_schema, write_table


def revenue_by_nation_year(
    orders: DataFrame, lineitem: DataFrame, customer: DataFrame, nation: DataFrame
) -> DataFrame:
    revenue = lineitem.select(
        "l_orderkey",
        (F.col("l_extendedprice") * (F.lit(1) - F.col("l_discount"))).alias("net"),
        F.col("l_quantity"),
    )
    return (
        orders.join(revenue, orders.o_orderkey == revenue.l_orderkey)
        .join(customer, orders.o_custkey == customer.c_custkey)
        .join(nation, customer.c_nationkey == nation.n_nationkey)
        .groupBy(F.col("n_name").alias("nation"), F.year("o_orderdate").alias("order_year"))
        .agg(
            F.countDistinct("o_orderkey").alias("orders"),
            F.sum("l_quantity").alias("quantity"),
            F.sum("net").cast("decimal(38,4)").alias("net_revenue"),
        )
    )


def build_gold(spark: SparkSession, cfg: FreedomConfig) -> int:
    def silver(table: str) -> DataFrame:
        return spark.table(cfg.table_name(cfg.silver_schema, table))

    ensure_schema(spark, cfg.catalog, cfg.gold_schema)
    name = cfg.table_name(cfg.gold_schema, "revenue_by_nation_year")
    write_table(
        spark,
        revenue_by_nation_year(silver("orders"), silver("lineitem"), silver("customer"), silver("nation")),
        name,
        cfg.table_location(cfg.gold_schema, "revenue_by_nation_year"),
        comment="Net revenue per customer nation and order year",
        properties={"freedom.layer": "gold"},
    )
    return spark.table(name).count()

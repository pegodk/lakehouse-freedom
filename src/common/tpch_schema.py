"""Canonical TPC-H schema (TPC-H specification v3, clause 1.4) as Spark SQL types.

Used to type the Silver layer, to validate schemas on every platform, and to
compute expected row counts.
"""

from __future__ import annotations

# table -> list of (column, spark_sql_type)
TPCH_SCHEMA: dict[str, list[tuple[str, str]]] = {
    "region": [
        ("r_regionkey", "INT"),
        ("r_name", "STRING"),
        ("r_comment", "STRING"),
    ],
    "nation": [
        ("n_nationkey", "INT"),
        ("n_name", "STRING"),
        ("n_regionkey", "INT"),
        ("n_comment", "STRING"),
    ],
    "supplier": [
        ("s_suppkey", "BIGINT"),
        ("s_name", "STRING"),
        ("s_address", "STRING"),
        ("s_nationkey", "INT"),
        ("s_phone", "STRING"),
        ("s_acctbal", "DECIMAL(15,2)"),
        ("s_comment", "STRING"),
    ],
    "customer": [
        ("c_custkey", "BIGINT"),
        ("c_name", "STRING"),
        ("c_address", "STRING"),
        ("c_nationkey", "INT"),
        ("c_phone", "STRING"),
        ("c_acctbal", "DECIMAL(15,2)"),
        ("c_mktsegment", "STRING"),
        ("c_comment", "STRING"),
    ],
    "part": [
        ("p_partkey", "BIGINT"),
        ("p_name", "STRING"),
        ("p_mfgr", "STRING"),
        ("p_brand", "STRING"),
        ("p_type", "STRING"),
        ("p_size", "INT"),
        ("p_container", "STRING"),
        ("p_retailprice", "DECIMAL(15,2)"),
        ("p_comment", "STRING"),
    ],
    "partsupp": [
        ("ps_partkey", "BIGINT"),
        ("ps_suppkey", "BIGINT"),
        ("ps_availqty", "BIGINT"),
        ("ps_supplycost", "DECIMAL(15,2)"),
        ("ps_comment", "STRING"),
    ],
    "orders": [
        ("o_orderkey", "BIGINT"),
        ("o_custkey", "BIGINT"),
        ("o_orderstatus", "STRING"),
        ("o_totalprice", "DECIMAL(15,2)"),
        ("o_orderdate", "DATE"),
        ("o_orderpriority", "STRING"),
        ("o_clerk", "STRING"),
        ("o_shippriority", "INT"),
        ("o_comment", "STRING"),
    ],
    "lineitem": [
        ("l_orderkey", "BIGINT"),
        ("l_partkey", "BIGINT"),
        ("l_suppkey", "BIGINT"),
        ("l_linenumber", "BIGINT"),
        ("l_quantity", "DECIMAL(15,2)"),
        ("l_extendedprice", "DECIMAL(15,2)"),
        ("l_discount", "DECIMAL(15,2)"),
        ("l_tax", "DECIMAL(15,2)"),
        ("l_returnflag", "STRING"),
        ("l_linestatus", "STRING"),
        ("l_shipdate", "DATE"),
        ("l_commitdate", "DATE"),
        ("l_receiptdate", "DATE"),
        ("l_shipinstruct", "STRING"),
        ("l_shipmode", "STRING"),
        ("l_comment", "STRING"),
    ],
}

PRIMARY_KEYS: dict[str, list[str]] = {
    "region": ["r_regionkey"],
    "nation": ["n_nationkey"],
    "supplier": ["s_suppkey"],
    "customer": ["c_custkey"],
    "part": ["p_partkey"],
    "partsupp": ["ps_partkey", "ps_suppkey"],
    "orders": ["o_orderkey"],
    "lineitem": ["l_orderkey", "l_linenumber"],
}

# (child_table, child_column, parent_table, parent_column)
FOREIGN_KEYS: list[tuple[str, str, str, str]] = [
    ("nation", "n_regionkey", "region", "r_regionkey"),
    ("supplier", "s_nationkey", "nation", "n_nationkey"),
    ("customer", "c_nationkey", "nation", "n_nationkey"),
    ("partsupp", "ps_partkey", "part", "p_partkey"),
    ("partsupp", "ps_suppkey", "supplier", "s_suppkey"),
    ("orders", "o_custkey", "customer", "c_custkey"),
    ("lineitem", "l_orderkey", "orders", "o_orderkey"),
]

TABLES: list[str] = list(TPCH_SCHEMA)

# Row counts fixed by the specification (clause 4.2.5), multiplied by SF.
_FIXED = {"region": 5, "nation": 25}
_PER_SF = {
    "supplier": 10_000,
    "customer": 150_000,
    "part": 200_000,
    "partsupp": 800_000,
    "orders": 1_500_000,
}
# lineitem is not an exact multiple of SF; these are the dbgen counts.
_LINEITEM = {0.01: 60_175, 0.1: 600_572, 1: 6_001_215, 10: 59_986_052, 100: 600_037_902}


def expected_row_count(table: str, scale_factor: float) -> int | None:
    """Exact dbgen row count, or None when it is not known in advance."""
    if table in _FIXED:
        return _FIXED[table]
    if table in _PER_SF:
        return int(_PER_SF[table] * scale_factor)
    if table == "lineitem":
        return _LINEITEM.get(scale_factor if scale_factor < 1 else int(scale_factor))
    raise KeyError(table)

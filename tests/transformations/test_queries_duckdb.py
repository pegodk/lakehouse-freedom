"""The canonical TPC-H SQL runs on DuckDB and matches the official answers (SF0.01).

This needs no Spark and no stack; it is the quickest SQL portability signal.
"""

import duckdb
import pytest

from freedom.validation.compare import rows_equal
from lakehouse_freedom.tpch import sql as tpch_sql
from lakehouse_freedom.tpch.generator.dbgen import answers


@pytest.fixture(scope="module")
def con():
    c = duckdb.connect()
    c.execute("INSTALL tpch; LOAD tpch; CALL dbgen(sf=0.01)")
    return c


@pytest.fixture(scope="module")
def expected():
    out = {}
    for q, text in answers(0.01).items():
        lines = text.strip().split("\n")
        out[q] = [line.split("|") for line in lines[1:]]
    return out


@pytest.mark.parametrize("q", tpch_sql.QUERY_IDS)
def test_canonical_query_on_duckdb(con, expected, q):
    text = tpch_sql.adapted("duckdb", q) or tpch_sql.canonical(q)
    rows = [list(r) for r in con.execute(text).fetchall()]
    ok, why = rows_equal(rows, expected[q])
    assert ok, why

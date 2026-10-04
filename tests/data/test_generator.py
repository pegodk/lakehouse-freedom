import json

import duckdb

from portable_lakehouse.common.tpch_schema import TABLES, expected_row_count
from portable_lakehouse.tpch.generator.dbgen import generate


def test_generate_sf001_local(tmp_path):
    manifest = generate(0.01, str(tmp_path), chunks=2)
    assert manifest["chunks"] == 2
    for table in TABLES:
        files = sorted((tmp_path / "sf0_01" / table).glob("part-*.parquet"))
        assert len(files) == 2
        n = duckdb.sql(f"SELECT count(*) FROM read_parquet('{tmp_path}/sf0_01/{table}/*.parquet')").fetchone()[0]
        assert n == manifest["rows"][table] == expected_row_count(table, 0.01)
    json.dumps(manifest)

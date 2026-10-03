from lakehouse_freedom.common.tpch_schema import (
    FOREIGN_KEYS,
    PRIMARY_KEYS,
    TABLES,
    TPCH_SCHEMA,
    expected_row_count,
)


def test_eight_tables():
    assert sorted(TABLES) == sorted(
        ["region", "nation", "supplier", "customer", "part", "partsupp", "orders", "lineitem"])


def test_keys_reference_existing_columns():
    for table, cols in PRIMARY_KEYS.items():
        names = {c for c, _ in TPCH_SCHEMA[table]}
        assert set(cols) <= names
    for child, ccol, parent, pcol in FOREIGN_KEYS:
        assert ccol in {c for c, _ in TPCH_SCHEMA[child]}
        assert pcol in {c for c, _ in TPCH_SCHEMA[parent]}


def test_expected_row_counts():
    assert expected_row_count("region", 10) == 5
    assert expected_row_count("orders", 1) == 1_500_000
    assert expected_row_count("lineitem", 1) == 6_001_215
    assert expected_row_count("lineitem", 10) == 59_986_052
    assert expected_row_count("lineitem", 3) is None

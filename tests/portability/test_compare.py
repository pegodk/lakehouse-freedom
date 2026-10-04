from portability.reporting.score import bar
from portability.validation.compare import diff_ratio, rows_equal, values_equal


def test_numeric_tolerance():
    assert values_equal("25.522005853257337", "25.522006")
    assert values_equal(55909065222.827692, "55909065222.83")
    assert not values_equal("1.00", "1.02")
    assert values_equal(" ABC ", "ABC")
    assert values_equal(None, "NULL")


def test_rows_equal_order_insensitive_for_ties():
    a = [["x", "1.00"], ["y", "1.00"]]
    b = [["y", "1"], ["x", "1"]]
    assert rows_equal(a, b)[0]
    assert not rows_equal(a, [["x", "1"]])[0]


def test_single_null_row_matches_empty_answer():
    assert rows_equal([[None]], [])[0]


def test_diff_ratio():
    assert diff_ratio("a\nb\nc\nd\ne", "a\nb\nc\nd\ne") == 0
    assert 0 < diff_ratio("a\nb\nc\nd\ne", "a\nB\nc\nd\ne") <= 0.2


def test_bar():
    assert bar(None).endswith("not measured")
    assert bar(0.5).startswith("█" * 10 + "░" * 10)

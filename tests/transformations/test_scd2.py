import json
from pathlib import Path

from freedom.assessment.scanner import RULES
from freedom.validation.scd2_reference import expected_scd2
from lakehouse_freedom.ingestion.incremental import BATCHES
from lakehouse_freedom.transformations.scd2 import merge_sql

EXPECTED = Path(__file__).resolve().parents[1] / "data" / "scd2_expected.json"


def test_reference_matches_committed_expectation():
    assert expected_scd2() == json.loads(EXPECTED.read_text())


def test_reference_semantics():
    rows = expected_scd2()
    current = {r["customer_id"]: r for r in rows if r["is_current"]}
    assert set(current) == {1, 2, 3, 4, 5, 6, 7}
    # unchanged repeat of customer 3 in batch 2 does not create a version
    assert len([r for r in rows if r["customer_id"] == 3]) == 1
    # customer 6: closed by a delete, re-activated later, gap in validity
    six = [r for r in rows if r["customer_id"] == 6]
    assert [(r["valid_from"], r["valid_to"]) for r in six] == [
        ("2024-01-01", "2024-02-01"), ("2024-03-01", None)]
    assert len(BATCHES) == 3


def test_merge_is_plain_sql():
    import re

    text = merge_sql("c.s.target", "c.s.changes", 2)
    assert "MERGE INTO c.s.target" in text
    assert not [r.key for r in RULES if re.search(r.pattern, text)]

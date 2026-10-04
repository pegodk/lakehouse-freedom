from pathlib import Path

from portability.assessment.inventory import count_loc, measure

REPO = Path(__file__).resolve().parents[2]
WORKLOAD_DIRS = ["src", "tpch/generator", "tpch/queries", "benchmarks/runner", "platforms/databricks",
                 "platforms/openlakehouse/airflow"]


def test_every_workload_file_is_classified_once():
    classified = [f["path"] for f in measure()["files"]]
    assert len(classified) == len(set(classified))
    for d in WORKLOAD_DIRS:
        for p in (REPO / d).rglob("*"):
            if p.is_file() and p.suffix in {".py", ".sql", ".yml"} and p.name != "__init__.py" \
                    and "__pycache__" not in p.parts:
                assert str(p.relative_to(REPO)) in classified, p


def test_loc_ignores_comments_and_docstrings(tmp_path):
    f = tmp_path / "x.py"
    f.write_text('"""doc\nstring"""\n\n# comment\nx = 1  # trailing\n\ndef f():\n    """doc"""\n    return x\n')
    assert count_loc(f) == 3


def test_scores_are_ratios():
    m = measure()
    for kind in ("transformation", "orchestration"):
        for platform in ("openlakehouse", "databricks"):
            s = m[kind][platform]
            assert 0 < s["score"] <= 1
            assert s["score"] == s["shared_loc"] / (s["shared_loc"] + s["platform_loc"])

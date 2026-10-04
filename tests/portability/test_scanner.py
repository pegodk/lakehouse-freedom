from pathlib import Path

from portability.assessment.inventory import measure
from portability.assessment.scanner import scan, scan_file

REPO = Path(__file__).resolve().parents[2]


def test_shared_code_has_no_databricks_specific_constructs():
    shared = [REPO / f["path"] for f in measure()["files"] if f["group"] == "shared"]
    assert scan(shared, REPO) == []


def test_scanner_finds_known_constructs(tmp_path):
    f = tmp_path / "nb.py"
    f.write_text(
        "df = spark.readStream.format('cloudFiles').load('/Volumes/x/y/z')\n"
        "dbutils.fs.ls('dbfs:/tmp')\n"
        "display(df)\n"
        "# dbutils in a comment is not a finding\n"
    )
    rules = {h["rule"] for h in scan_file(f)}
    assert {"auto_loader", "volumes_path", "dbutils", "dbfs", "display"} <= rules
    assert all(h["line"] != 4 for h in scan_file(f))


def test_scanner_sql(tmp_path):
    f = tmp_path / "q.sql"
    f.write_text("CREATE OR REFRESH STREAMING TABLE t AS SELECT * FROM read_files('/x');\n"
                 "-- CLUSTER BY AUTO in a comment\n")
    rules = {h["rule"] for h in scan_file(f)}
    assert rules == {"streaming_table", "read_files"}

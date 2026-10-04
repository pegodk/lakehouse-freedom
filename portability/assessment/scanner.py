"""Static scan for Databricks-specific constructs.

Used two ways:
  * Portability Check: shared code (inventory group `shared`) must contain none.
  * `portable-lakehouse assess <path>`: inventory any Databricks project and identify
    where platform-specific capabilities and alternatives differ.

Every rule names the capability, the classification used in Portability Reports
(PORTABLE / ADAPTABLE / REIMPLEMENT / PLATFORM-SPECIFIC) and a possible open alternative.
The rules are deliberately conservative pattern matches: a hit means "look
here", not a verdict.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

ADAPTABLE = "ADAPTABLE"
REIMPLEMENT = "REIMPLEMENT"
PLATFORM_SPECIFIC = "PLATFORM-SPECIFIC"


@dataclass(frozen=True)
class Rule:
    key: str
    pattern: str
    capability: str
    classification: str
    alternative: str


RULES: list[Rule] = [
    Rule("dbutils", r"\bdbutils\.", "Databricks Utilities (fs, secrets, widgets, notebook)",
         ADAPTABLE, "pass values as parameters; object-store SDK; secret manager"),
    Rule("display", r"(?<![\w.])display\(", "Notebook display()", ADAPTABLE, "df.show() / plotting library"),
    Rule("databricks_connect", r"\bDatabricksSession\b|from databricks\.connect", "Databricks Connect session",
         ADAPTABLE, "SparkSession.builder.remote('sc://...') (Spark Connect)"),
    Rule("databricks_sdk", r"from databricks\.sdk|import databricks\.sdk", "Databricks SDK / REST APIs",
         PLATFORM_SPECIFIC, "keep in platform adapters; UC REST for catalog metadata"),
    Rule("spark_databricks_conf", r"spark\.databricks\.", "Databricks-only Spark configuration",
         PLATFORM_SPECIFIC, "remove, or move to platform configuration"),
    Rule("dbfs", r"dbfs:/|/dbfs/", "DBFS paths", ADAPTABLE, "object-store URI from configuration"),
    Rule("volumes_path", r"/Volumes/", "Hard-coded Unity Catalog Volume path", ADAPTABLE,
         "path from configuration (LakehouseConfig.raw_root)"),
    Rule("auto_loader", r"cloudFiles", "Auto Loader", REIMPLEMENT,
         "Structured Streaming file source + checkpoint; see Portability Challenge #2"),
    Rule("dlt", r"^\s*import dlt\b|@dlt\.", "Lakeflow Declarative Pipelines (dlt module)", ADAPTABLE,
         "Spark Declarative Pipelines (pyspark.pipelines, Spark 4.1)"),
    Rule("streaming_table", r"(?i)\bCREATE\s+(OR\s+REFRESH\s+)?STREAMING\s+TABLE\b",
         "Lakeflow streaming tables (SQL)", ADAPTABLE, "Spark Declarative Pipelines SQL"),
    Rule("materialized_view", r"(?i)\bCREATE\s+(OR\s+REPLACE\s+)?MATERIALIZED\s+VIEW\b",
         "Materialized views", ADAPTABLE, "Spark Declarative Pipelines materialized views"),
    Rule("read_files", r"(?i)\bread_files\s*\(", "read_files() table-valued function", ADAPTABLE,
         "spark.read.format(...).load(...)"),
    Rule("ai_functions", r"(?i)\bai_(query|classify|extract|gen|similarity|summarize|translate|forecast)\s*\(",
         "Databricks AI Functions", PLATFORM_SPECIFIC, "call a model endpoint from a UDF or pipeline step"),
    Rule("vector_search", r"databricks\.vector_search|vector_search\(", "Mosaic AI Vector Search",
         PLATFORM_SPECIFIC, "open-source vector store; see Portability Challenge #7"),
    Rule("secret_fn", r"(?i)\bsecret\s*\(\s*'", "SQL secret() function", ADAPTABLE, "parameters / env"),
    Rule("cluster_by_auto", r"(?i)\bCLUSTER\s+BY\s+AUTO\b", "Automatic liquid clustering", ADAPTABLE,
         "CLUSTER BY (explicit columns), supported by OSS Delta"),
    Rule("row_filter_mask", r"(?i)\b(ROW\s+FILTER|MASK)\b\s+\w", "Row filters / column masks",
         PLATFORM_SPECIFIC, "engine-side policies; see Portability Challenge #4"),
    Rule("system_tables", r"\bsystem\.(billing|access|lakeflow|compute|query|information_schema)\.",
         "Databricks system tables", PLATFORM_SPECIFIC, "observability stack; see Portability Challenge #8"),
    Rule("create_or_replace_location", r"(?i)CREATE\s+OR\s+REPLACE\s+TABLE[^;]*\bLOCATION\b",
         "CREATE OR REPLACE TABLE ... LOCATION", ADAPTABLE,
         "create once, then INSERT OVERWRITE (UC OSS 0.5 rejects the replace)"),
    Rule("alter_table_meta", r"(?i)\bALTER\s+TABLE\b[^;]*\b(SET\s+TBLPROPERTIES|ALTER\s+COLUMN[^;]*COMMENT)\b",
         "ALTER TABLE metadata changes", ADAPTABLE,
         "set comments/properties at creation (UC OSS 0.5 connector rejects ALTER TABLE)"),
    Rule("notebook_magic", r"^\s*#\s*MAGIC\s+%|^%(sql|python|run|pip)\b", "Notebook magics", ADAPTABLE,
         "plain .py / .sql modules"),
]

SCANNED_SUFFIXES = {".py", ".sql", ".scala", ".yml", ".yaml", ".ipynb"}


def _non_code_lines(path: Path, text: str) -> set[int]:
    """Comment and docstring lines: mentioning a construct is not using it."""
    if path.suffix == ".py":
        from portability.assessment.inventory import _docstring_lines

        skip = _docstring_lines(text)
        skip.update(i for i, line in enumerate(text.splitlines(), 1) if line.strip().startswith("#")
                    and "MAGIC" not in line)
        return skip
    marker = "--" if path.suffix == ".sql" else "#" if path.suffix in (".yml", ".yaml") else None
    if not marker:
        return set()
    return {i for i, line in enumerate(text.splitlines(), 1) if line.strip().startswith(marker)}


def scan_file(path: Path) -> list[dict]:
    hits = []
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return hits
    skip = _non_code_lines(path, text)
    for i, line in enumerate(text.splitlines(), 1):
        if i in skip:
            continue
        for rule in RULES:
            if re.search(rule.pattern, line):
                hits.append({"file": str(path), "line": i, "rule": rule.key, "capability": rule.capability,
                             "classification": rule.classification, "alternative": rule.alternative,
                             "text": line.strip()[:160]})
    return hits


def scan(paths: list[Path], root: Path | None = None) -> list[dict]:
    hits = []
    for base in paths:
        files = [base] if base.is_file() else [
            p for p in base.rglob("*") if p.suffix in SCANNED_SUFFIXES and ".venv" not in p.parts
            and "stack" not in p.parts]
        for f in sorted(files):
            for h in scan_file(f):
                if root:
                    h["file"] = str(Path(h["file"]).resolve().relative_to(root.resolve()))
                hits.append(h)
    return hits

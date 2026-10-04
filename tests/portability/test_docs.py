import re
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[2]


def test_capability_mapping_doc_lists_every_capability():
    doc = (REPO / "docs" / "capability-mapping.md").read_text()
    for cap in yaml.safe_load((REPO / "portability/assessment/capabilities.yaml").read_text()):
        assert f"| {cap['capability']} |" in doc
        assert cap["classification"] in {"PORTABLE", "ADAPTABLE", "REIMPLEMENT", "PLATFORM-SPECIFIC"}


def test_legacy_project_name_is_not_reintroduced():
    legacy_name = re.compile(r"lakehouse[ _-]*" + "freedom", re.IGNORECASE)
    roots = ("src", "tpch", "benchmarks", "portability", "platforms", "governance", "docs", "reports")
    text_suffixes = {".cedar", ".conf", ".env", ".json", ".md", ".py", ".sql", ".toml", ".yaml", ".yml"}
    files = [
        REPO / "LICENSE",
        REPO / "Makefile",
        REPO / "README.md",
        REPO / "pyproject.toml",
        REPO / "zensical.toml",
        *(
            path
            for root in roots
            for path in (REPO / root).rglob("*")
            if path.is_file() and path.suffix in text_suffixes and "stack" not in path.parts
        ),
    ]
    offenders = []
    for path in files:
        if legacy_name.search(path.read_text(errors="replace")):
            offenders.append(str(path.relative_to(REPO)))
    assert offenders == []

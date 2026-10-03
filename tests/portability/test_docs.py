from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[2]


def test_capability_mapping_doc_lists_every_capability():
    doc = (REPO / "docs" / "capability-mapping.md").read_text()
    for cap in yaml.safe_load((REPO / "freedom/assessment/capabilities.yaml").read_text()):
        assert f"| {cap['capability']} |" in doc
        assert cap["classification"] in {"PORTABLE", "ADAPTABLE", "REWRITE", "PLATFORM-SPECIFIC"}

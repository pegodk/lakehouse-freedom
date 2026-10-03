"""Load and summarize the curated managed-to-open capability matrix."""

from __future__ import annotations

from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[2]
MATRIX = REPO / "freedom" / "assessment" / "feature_matrix.yaml"
STATUSES = {"NATIVE", "ALTERNATIVE", "WORKAROUND", "MISSING", "NOT_ASSESSED"}
COVERED = {"NATIVE", "ALTERNATIVE", "WORKAROUND"}


def load() -> dict:
    matrix = yaml.safe_load(MATRIX.read_text())
    validate(matrix)
    return matrix


def validate(matrix: dict) -> None:
    if not matrix.get("as_of") or not matrix.get("profiles"):
        raise ValueError("feature matrix requires as_of and profiles")
    profile_keys: set[str] = set()
    for profile in matrix["profiles"]:
        required = {"key", "component", "source", "target", "features"}
        missing = required - profile.keys()
        if missing:
            raise ValueError(f"profile is missing {sorted(missing)}")
        if profile["key"] in profile_keys:
            raise ValueError(f"duplicate profile key: {profile['key']}")
        profile_keys.add(profile["key"])
        capabilities: set[str] = set()
        for feature in profile["features"]:
            missing = {"capability", "area", "status", "workload", "evidence"} - feature.keys()
            if missing:
                raise ValueError(f"{profile['key']} feature is missing {sorted(missing)}")
            if feature["status"] not in STATUSES:
                raise ValueError(f"invalid status {feature['status']} in {profile['key']}")
            if feature["workload"] not in {"required", "not_used"}:
                raise ValueError(f"invalid workload relevance in {profile['key']}")
            if feature["capability"] in capabilities:
                raise ValueError(f"duplicate capability in {profile['key']}: {feature['capability']}")
            capabilities.add(feature["capability"])


def summarize(profile: dict) -> dict:
    assessed = [f for f in profile["features"] if f["status"] != "NOT_ASSESSED"]
    counts = {status: sum(f["status"] == status for f in profile["features"]) for status in STATUSES}
    covered = sum(f["status"] in COVERED for f in assessed)
    native = counts["NATIVE"]
    total = len(assessed)
    required = [f for f in assessed if f["workload"] == "required"]
    required_covered = sum(f["status"] in COVERED for f in required)
    return {
        "counts": counts,
        "total": total,
        "covered": covered,
        "native": native,
        "outcome_coverage": covered / total if total else None,
        "native_parity": native / total if total else None,
        "required_covered": required_covered,
        "required_total": len(required),
    }

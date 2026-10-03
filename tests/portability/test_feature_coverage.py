from freedom.assessment.feature_coverage import COVERED, STATUSES, load, summarize


def test_feature_matrix_is_valid_and_has_visible_gaps():
    matrix = load()
    assert len(matrix["profiles"]) >= 8
    for profile in matrix["profiles"]:
        summary = summarize(profile)
        assert summary["total"] > 0
        assert summary["counts"]["MISSING"] > 0
        for feature in profile["features"]:
            assert feature["status"] in STATUSES
            if feature["status"] == "MISSING":
                assert feature.get("gap")
            if feature["status"] == "ALTERNATIVE":
                assert feature.get("alternative")


def test_coverage_ratios_are_derived_from_assessed_rows():
    for profile in load()["profiles"]:
        summary = summarize(profile)
        assessed = [f for f in profile["features"] if f["status"] != "NOT_ASSESSED"]
        assert summary["covered"] == sum(f["status"] in COVERED for f in assessed)
        assert summary["native"] == sum(f["status"] == "NATIVE" for f in assessed)
        assert summary["outcome_coverage"] == summary["covered"] / len(assessed)

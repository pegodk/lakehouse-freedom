import pytest

from lakehouse_freedom.governance import (
    AccessDenied,
    AccessRequest,
    Decision,
    GovernancePlanner,
    Obligation,
    PolicyPlan,
    Principal,
    Resource,
    UnsupportedObligation,
    enforce_datafusion_obligations,
    mask_email_value,
)


def plan(*obligations):
    request = AccessRequest(Principal("User", "alice"), "select", Resource("Table", "customers"))
    return PolicyPlan(request, ("pii-reader",), obligations)


@pytest.mark.parametrize(
    "source,masked",
    [
        (None, None),
        ("alice@example.com", "a***@example.com"),
        ("a@example.com", "a***@example.com"),
        ("not-an-email", "***"),
        ("@example.com", "***"),
    ],
)
def test_mask_email_value(source, masked):
    assert mask_email_value(source) == masked


def test_datafusion_masks_configured_column_and_preserves_others():
    from datafusion import SessionContext

    dataframe = SessionContext().from_pydict({
        "id": [1, 2, 3],
        "email": ["alice@example.com", None, "invalid"],
    })
    obligation = Obligation("column_mask", "mask_email", {"columns": ["email"]})

    result = enforce_datafusion_obligations(dataframe, plan(obligation)).to_pydict()

    assert result == {
        "id": [1, 2, 3],
        "email": ["a***@example.com", None, "***"],
    }


def test_cedar_decision_to_datafusion_mask_end_to_end():
    from datafusion import SessionContext

    class PiiAuthorizer:
        def authorize(self, request):
            return Decision(True, ("pii-reader",))

    obligation = Obligation("column_mask", "mask_email", {"columns": ["email"]})
    policy_plan = GovernancePlanner(PiiAuthorizer(), {"pii-reader": (obligation,)}).plan(
        AccessRequest(Principal("User", "alice"), "select", Resource("Column", "customers.email"))
    )
    dataframe = SessionContext().from_pydict({"email": ["alice@example.com"]})

    assert enforce_datafusion_obligations(dataframe, policy_plan).to_pydict() == {
        "email": ["a***@example.com"]
    }


def test_datafusion_returns_clear_values_without_mask_obligation():
    from datafusion import SessionContext

    dataframe = SessionContext().from_pydict({"email": ["alice@example.com"]})

    assert enforce_datafusion_obligations(dataframe, plan()).to_pydict()["email"] == ["alice@example.com"]


def test_datafusion_fails_closed_for_missing_column():
    from datafusion import SessionContext

    dataframe = SessionContext().from_pydict({"email": ["alice@example.com"]})
    obligation = Obligation("column_mask", "mask_email", {"columns": ["phone"]})

    with pytest.raises(AccessDenied, match="mask column not found"):
        enforce_datafusion_obligations(dataframe, plan(obligation))


def test_datafusion_fails_closed_for_unimplemented_obligation():
    from datafusion import SessionContext

    dataframe = SessionContext().from_pydict({"email": ["alice@example.com"]})
    obligation = Obligation("row_filter", "tenant_isolation", {})

    with pytest.raises(AccessDenied, match="cannot enforce"):
        enforce_datafusion_obligations(dataframe, plan(obligation))


def test_datafusion_rejects_invalid_mask_configuration():
    from datafusion import SessionContext

    dataframe = SessionContext().from_pydict({"email": ["alice@example.com"]})
    obligation = Obligation("column_mask", "mask_email", {"columns": []})

    with pytest.raises(UnsupportedObligation, match="non-empty"):
        enforce_datafusion_obligations(dataframe, plan(obligation))

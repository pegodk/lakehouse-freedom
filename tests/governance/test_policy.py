import pytest

from portable_lakehouse.governance import (
    AccessDenied,
    AccessRequest,
    CedarJsonAuthorizer,
    Decision,
    GovernancePlanner,
    Obligation,
    Principal,
    Resource,
)


class StubAuthorizer:
    def __init__(self, decision):
        self.decision = decision

    def authorize(self, request):
        return self.decision


def request():
    return AccessRequest(
        Principal("User", "alice", {"tenant": "acme"}),
        "select",
        Resource("Table", "portable_lakehouse.silver.orders", {"classification": "internal"}),
    )


def test_resolves_cedar_policy_ids_to_typed_obligations():
    tenant = Obligation("row_filter", "tenant_isolation", {"attribute": "tenant"})
    mask = Obligation("column_mask", "mask_email", {"columns": ("email",)})
    planner = GovernancePlanner(
        StubAuthorizer(Decision(True, ("tenant-reader", "pii-mask"))),
        {"tenant-reader": (tenant,), "pii-mask": (mask,)},
    )

    plan = planner.plan(request())

    assert plan.obligations == (tenant, mask)


def test_cedar_json_adapter_preserves_request_attributes_and_diagnostics():
    captured = {}

    def evaluate(payload):
        captured.update(payload)
        return {"decision": "Allow", "diagnostics": {"reason": ["tenant-reader"]}}

    decision = CedarJsonAuthorizer(evaluate).authorize(request())

    assert decision == Decision(True, ("tenant-reader",))
    assert captured["request"]["principal"] == {"type": "User", "id": "alice"}
    assert captured["entities"][0]["attrs"] == {"tenant": "acme"}


@pytest.mark.parametrize(
    "decision,mappings,error",
    [
        (Decision(False), {}, "may not select"),
        (Decision(True, errors=("Cedar evaluation failed",)), {}, "Cedar evaluation failed"),
        (Decision(True, ("unknown-policy",)), {}, "unmapped policy"),
    ],
)
def test_fails_closed(decision, mappings, error):
    with pytest.raises(AccessDenied, match=error):
        GovernancePlanner(StubAuthorizer(decision), mappings).plan(request())

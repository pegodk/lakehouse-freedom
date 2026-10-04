"""Engine-neutral contract between Cedar and query enforcement points.

Cedar decides whether an action is permitted and reports the policy IDs that
determined the decision. Query engines must not interpret Cedar source as SQL.
Instead, this module maps reviewed policy IDs to typed, portable obligations
that an engine adapter can compile to its own expression tree.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any, Literal, Protocol


@dataclass(frozen=True)
class Principal:
    type: str
    id: str
    attributes: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class Resource:
    type: str
    id: str
    attributes: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class AccessRequest:
    principal: Principal
    action: str
    resource: Resource
    context: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class Decision:
    allowed: bool
    determining_policies: tuple[str, ...] = ()
    errors: tuple[str, ...] = ()


class Authorizer(Protocol):
    """Port implemented by a Cedar library, sidecar, or policy service."""

    def authorize(self, request: AccessRequest) -> Decision: ...


class CedarJsonAuthorizer:
    """Adapt a Cedar-compatible JSON evaluator to the portable contract.

    ``evaluate`` can call an in-process Cedar binding or a sidecar. It receives
    a request plus the two request entities and must return Cedar's JSON result
    shape: ``decision`` and optional ``diagnostics.reason/errors``.
    """

    def __init__(self, evaluate):
        self.evaluate = evaluate

    @staticmethod
    def _uid(entity: Principal | Resource) -> dict[str, str]:
        return {"type": entity.type, "id": entity.id}

    def authorize(self, request: AccessRequest) -> Decision:
        principal = self._uid(request.principal)
        resource = self._uid(request.resource)
        result = self.evaluate({
            "request": {
                "principal": principal,
                "action": {"type": "Action", "id": request.action},
                "resource": resource,
                "context": dict(request.context),
            },
            "entities": [
                {"uid": principal, "attrs": dict(request.principal.attributes), "parents": []},
                {"uid": resource, "attrs": dict(request.resource.attributes), "parents": []},
            ],
        })
        diagnostics = result.get("diagnostics") or {}
        reasons = tuple(str(value) for value in diagnostics.get("reason", ()))
        errors = tuple(str(value) for value in diagnostics.get("errors", ()))
        return Decision(str(result.get("decision", "Deny")).lower() == "allow", reasons, errors)


ObligationKind = Literal["row_filter", "column_allow", "column_mask"]


@dataclass(frozen=True)
class Obligation:
    """A reviewed enforcement operation, never arbitrary SQL from a policy."""

    kind: ObligationKind
    name: str
    parameters: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class PolicyPlan:
    request: AccessRequest
    determining_policies: tuple[str, ...]
    obligations: tuple[Obligation, ...]


class AccessDenied(PermissionError):
    def __init__(self, request: AccessRequest, errors: tuple[str, ...] = ()):
        message = (
            f"{request.principal.type}::{request.principal.id} may not "
            f"{request.action} {request.resource.type}::{request.resource.id}"
        )
        if errors:
            message += f" ({'; '.join(errors)})"
        super().__init__(message)
        self.request = request
        self.errors = errors


class GovernancePlanner:
    """Fail-closed Cedar decision and obligation resolution."""

    def __init__(self, authorizer: Authorizer, obligations: Mapping[str, tuple[Obligation, ...]]):
        self.authorizer = authorizer
        self.obligations = MappingProxyType(dict(obligations))

    def plan(self, request: AccessRequest) -> PolicyPlan:
        decision = self.authorizer.authorize(request)
        if not decision.allowed or decision.errors:
            raise AccessDenied(request, decision.errors)

        resolved: list[Obligation] = []
        for policy_id in decision.determining_policies:
            if policy_id not in self.obligations:
                # An allowing policy without a known enforcement mapping could
                # otherwise silently drop a row or column restriction.
                raise AccessDenied(request, (f"unmapped policy: {policy_id}",))
            for obligation in self.obligations[policy_id]:
                if obligation not in resolved:
                    resolved.append(obligation)
        return PolicyPlan(request, decision.determining_policies, tuple(resolved))

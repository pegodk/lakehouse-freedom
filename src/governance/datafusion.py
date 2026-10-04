"""DataFusion enforcement for reviewed governance obligations."""

from __future__ import annotations

from typing import Any

from .policy import AccessDenied, Obligation, PolicyPlan


def mask_email_value(value: str | None) -> str | None:
    """Mask an email while retaining one character and its routing domain.

    Malformed values are fully masked so unexpected input cannot disclose more
    data than a valid address. Null remains null.
    """
    if value is None:
        return None
    local, separator, domain = value.partition("@")
    if not separator or not local or not domain:
        return "***"
    return f"{local[0]}***@{domain}"


def datafusion_mask_email_udf():
    """Build the Arrow-native scalar UDF used in DataFusion logical plans."""
    import pyarrow as pa
    from datafusion import udf

    def mask_email(values):
        return pa.array((mask_email_value(value.as_py()) for value in values), type=pa.string())

    return udf(mask_email, [pa.string()], pa.string(), "immutable", "mask_email")


class UnsupportedObligation(ValueError):
    pass


def enforce_datafusion_obligations(dataframe: Any, plan: PolicyPlan):
    """Compile every obligation in ``plan`` into a DataFusion projection.

    This initial adapter deliberately supports only ``column_mask/mask_email``.
    Any other operation fails closed instead of returning unprotected data.
    """
    from datafusion.functions import col

    columns = list(dataframe.schema().names)
    masks: dict[str, Obligation] = {}

    for obligation in plan.obligations:
        if obligation.kind != "column_mask" or obligation.name != "mask_email":
            raise AccessDenied(
                plan.request,
                (f"DataFusion cannot enforce {obligation.kind}/{obligation.name}",),
            )
        targets = obligation.parameters.get("columns")
        if not isinstance(targets, (list, tuple)) or not targets or not all(isinstance(c, str) for c in targets):
            raise UnsupportedObligation("mask_email requires a non-empty list of column names")
        for column in targets:
            if column not in columns:
                raise AccessDenied(plan.request, (f"mask column not found: {column}",))
            if column in masks and masks[column] != obligation:
                raise AccessDenied(plan.request, (f"conflicting masks for column: {column}",))
            masks[column] = obligation

    if not masks:
        return dataframe

    mask_email = datafusion_mask_email_udf()
    projections = [mask_email(col(column)).alias(column) if column in masks else col(column) for column in columns]
    return dataframe.select(*projections)

// Store this policy with the stable policy ID `pii-reader`, which maps to the
// mask_email obligation. The mask is enforced by the DataFusion adapter.

permit (
    principal is LakehouseFreedom::User,
    action == LakehouseFreedom::Action::"select",
    resource is LakehouseFreedom::Column
)
when { resource.classification == "pii" };

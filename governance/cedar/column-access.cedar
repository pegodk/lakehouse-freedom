// Store this policy with the stable policy ID `pii-reader`, which maps to the
// mask_email obligation. The mask is enforced by the DataFusion adapter.

permit (
    principal is PortableLakehouse::User,
    action == PortableLakehouse::Action::"select",
    resource is PortableLakehouse::Column
)
when { resource.classification == "pii" };

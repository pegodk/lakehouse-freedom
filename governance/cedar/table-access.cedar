// Policy-store IDs are stable external identifiers. The obligation registry
// maps `public-reader` and `tenant-reader` to engine enforcement operations.

permit (
    principal is LakehouseFreedom::User,
    action == LakehouseFreedom::Action::"select",
    resource is LakehouseFreedom::Table
)
when { resource.classification == "public" };

permit (
    principal is LakehouseFreedom::User,
    action == LakehouseFreedom::Action::"select",
    resource is LakehouseFreedom::Table
)
when { resource has tenantColumn && principal has tenant };

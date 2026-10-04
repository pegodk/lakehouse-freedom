// Policy-store IDs are stable external identifiers. The obligation registry
// maps `public-reader` and `tenant-reader` to engine enforcement operations.

permit (
    principal is PortableLakehouse::User,
    action == PortableLakehouse::Action::"select",
    resource is PortableLakehouse::Table
)
when { resource.classification == "public" };

permit (
    principal is PortableLakehouse::User,
    action == PortableLakehouse::Action::"select",
    resource is PortableLakehouse::Table
)
when { resource has tenantColumn && principal has tenant };

namespace LakehouseFreedom {
    entity Group;
    entity User in [Group] {
        tenant: String,
        regions: Set<String>,
        clearance: Long
    };

    entity Catalog;
    entity Schema in [Catalog];
    entity Table in [Schema] {
        classification: String,
        tenantColumn?: String
    };
    entity Column in [Table] {
        classification: String
    };

    action select appliesTo {
        principal: [User],
        resource: [Table, Column],
        context: { purpose?: String }
    };
}

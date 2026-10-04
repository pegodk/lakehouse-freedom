# Governance

Governance is the largest gap between an open table/catalog foundation and an integrated managed platform.

Databricks combines identity, catalog permissions, row filters, column masks, lineage, auditing, and enforcement across its services. Unity Catalog OSS provides useful metadata and permissions foundations, but the tested OpenLakehouse configuration does not reproduce that end-to-end control plane.

## Prototype assessed here

The repository explores a portable policy boundary:

| | Role | Open component |
|---|---|---|
| <img class="tech-icon tech-icon-wide" src="assets/icons/unity-catalog.png" alt="Unity Catalog"> | Resource metadata | Unity Catalog OSS |
| <img class="tech-icon" src="assets/icons/cedar.png" alt="Cedar"> | Authorization decision | Cedar |
| <img class="tech-icon" src="assets/icons/datafusion.svg" alt="Apache DataFusion"> | Query enforcement | DataFusion prototype |
| <img class="tech-icon" src="assets/icons/delta-lake.svg" alt="Delta Lake"> | Data | Delta tables on object storage |

Two obligations were reviewed. Email masking is implemented; tenant row isolation fails closed because it is not implemented. This produces the measured 1/2 governance score.

That score is deliberately narrow. It does not establish production identity integration, secure credential isolation, a hardened SQL gateway, comprehensive policy coverage, lineage, or audit parity.

## Practical conclusion

Portable policy definitions can reduce coupling, but enforcement must exist in every path to the data. Direct object-storage credentials or an unrestricted query engine can bypass catalog policy. Teams choosing an open architecture must design identity, enforcement, audit, and storage boundaries as one system rather than treating the catalog as sufficient governance.

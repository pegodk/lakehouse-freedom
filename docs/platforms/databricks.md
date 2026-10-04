# Databricks reference

<img class="page-mark" src="../assets/icons/databricks.svg" alt="Databricks">

Databricks is the managed side of the comparison. One serverless Lakeflow Job runs the shared Python wheel and task graph against external Delta tables registered in Unity Catalog.

## What the implementation demonstrates

- shared PySpark transformations and canonical SQL run on Databricks;
- an Asset Bundle describes the job and landing volumes;
- results and environment metadata can be compared with the open implementation;
- platform-specific Python remains limited to the entry point and environment discovery.

The committed SF1 and SF10 results include all 22 TPC-H queries, table-quality evidence, fingerprints, and the SCD2 scenario.

## Interpretation

Databricks contributes more than a Spark runtime: it manages compute provisioning, service integration, identity, governance, upgrades, and the user experience. Those benefits are central to the comparison and are not treated as portability failures.

To reproduce this side, use an authenticated Databricks CLI profile, a Unity Catalog catalog, an external storage location, and billed compute. The exact commands remain in the [command reference](../reference/commands.md#databricks).

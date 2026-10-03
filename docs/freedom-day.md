# Freedom Day

> The day Databricks is switched off. The data stays where it is.

```bash
make freedom-day SCALE=1                                   # rehearsal on OpenLakehouse-written tables
make freedom-day SCALE=1 SOURCE=s3://lakehouse/<prefix>    # tables synced from a Databricks external location
```

## Before, during, after

```
Before                     Freedom Day                After

  Databricks                 Databricks                 OpenLakehouse.io
      │                          X                             │
 Unity Catalog                                        Unity Catalog OSS
      │                                                ┌───────┴───────┐
    Delta                                            Spark           DuckDB
      │                                                └───────┬───────┘
Object Storage  ─────────────── unchanged ──────────►  EXISTING DELTA DATA
```

## The critical constraint

**The business data is not regenerated, converted or copied because Databricks has gone.** Freedom Day starts from the Delta folders in object storage and nothing else. It fails if any stored object is added or changed during the run.

## What happens

| Step | Action | Fails when |
|---|---|---|
| 1. Inventory | List every object under the table root: key, size, ETag | |
| 2. Empty catalog | Create Unity Catalog OSS catalog `freedom_day` from scratch. The original catalog is never consulted. | |
| 3. Discover and register | Find tables by their `_delta_log/` folders. For each: `DESCRIBE DETAIL` and `DESCRIBE HISTORY` on the path, read the schema from the log, register through the UC REST API with full column metadata. | a table cannot be read by path |
| 4. Read every table | `count(*)` on every table with Spark (through `freedom_day`) and DuckDB (`delta_scan` on the UC-resolved location) | counts differ or a read fails |
| 5. Query | TPC-H 1–22 on Spark and on DuckDB against `freedom_day` | a query fails |
| 6. Compare | Results against the official answers / Databricks / earlier OpenLakehouse run | any result differs |
| 7. Inventory again | Same listing as step 1 | any object added or changed |

Output: `reports/freedom-day-sf<N>.json` with per-table protocol versions, table features, number of commits, the writer of each commit (`engineInfo`), and both row counts.

## Rehearsal or the real thing

The Delta history records which engine wrote each commit. Freedom Day reads it and reports:

- **Rehearsal**: every writer is open-source Spark (`Apache-Spark/4.1.0 Delta-Lake/4.3.1`). This is the default when you run it right after `make pipeline`.
- **Databricks data**: at least one writer is Databricks Runtime. This is the real scenario, after syncing the Databricks external location (see the [Freedom Path](freedom-path.md#2-reach-the-storage)).

The committed results are a rehearsal, because the Databricks job has not been executed for this release. The mechanics are the same either way. What a rehearsal cannot show is whether tables written by Databricks use Delta table features the open readers don't support. Freedom Day reports the features it actually finds and fails if a table can't be read, so you learn this from the run itself and don't have to assume it.

## Why it can work

Three choices from the [Freedom Architecture](freedom-architecture.md) make it possible:

1. **External tables** (F1). Table folders sit under a `table_root` you control and remain addressable by path.
2. **A self-describing format.** A Delta table's schema, history and file list are in its `_delta_log`, so the catalog can be rebuilt from storage.
3. **Open readers.** Delta Lake 4.3.1 for Spark and `delta-kernel-rs` (DuckDB's `delta` extension) both read the log directly.

What does **not** come back on its own: grants, tags, row filters, column masks, lineage and anything else held only by the managed catalog. See the [capability mapping](capability-mapping.md).

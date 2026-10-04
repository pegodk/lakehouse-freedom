# Reproducing the evidence

<img class="page-mark" src="assets/icons/docker.svg" alt="Docker">

The committed [report](report.md) contains the results and limitations. The steps below reproduce the open side of the comparison.

To reproduce the open side, use Docker Compose v2, `uv`, Git, Make, about 10 GB of container memory, and about 5 GB of disk for SF1:

```bash
git clone --recurse-submodules https://github.com/pegodk/portable-lakehouse.git
cd portable-lakehouse
make setup
make openlakehouse-up
make demo SCALE=1
```

The last command runs the workload, SQL compatibility checks, capability checks, and report generation. Use `SCALE=0.01` for a smoke test or `SCALE=10` for the reference scale. Results are written to `reports/portability-report.md`.

Databricks execution requires an authenticated CLI profile, a Unity Catalog catalog, an external storage location, and billed compute. See [Databricks reference](platforms/databricks.md).

For individual commands and troubleshooting, see [command reference](reference/commands.md).

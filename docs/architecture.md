# Architectures compared

Both architectures run the same workload and produce external Delta tables with matching names.

<div class="architecture-diagram" role="img" aria-label="Side-by-side architecture comparison of Databricks and OpenLakehouse">
  <div class="architecture-heading architecture-databricks">
    <img src="assets/icons/databricks.svg" alt="">
    <strong>Databricks</strong>
    <small>Integrated managed platform</small>
  </div>
  <div class="architecture-heading architecture-openlakehouse">
    <img class="rounded" src="assets/icons/openlakehouse.jpg" alt="">
    <strong>OpenLakehouse</strong>
    <small>Assembled open-source services</small>
  </div>

  <div class="architecture-card">
    <img src="assets/icons/databricks.svg" alt="">
    <span><strong>Lakeflow Jobs</strong><small>Managed workflow and task execution</small></span>
  </div>
  <div class="architecture-link"><span>orchestration</span><b>↔</b></div>
  <div class="architecture-card">
    <img src="assets/icons/apache-airflow.svg" alt="">
    <span><strong>Apache Airflow</strong><small>DAG generated from the shared task graph</small></span>
  </div>

  <div class="architecture-down">↓</div><div></div><div class="architecture-down">↓</div>

  <div class="architecture-card">
    <img src="assets/icons/databricks.svg" alt="">
    <span><strong>Databricks Runtime</strong><small>Serverless Apache Spark compute</small></span>
  </div>
  <div class="architecture-link"><span>compute</span><b>↔</b></div>
  <div class="architecture-card">
    <img src="assets/icons/apache-spark.svg" alt="">
    <span><strong>Apache Spark</strong><small>Standalone cluster through Spark Connect</small></span>
  </div>

  <div class="architecture-down">↓</div><div></div><div class="architecture-down">↓</div>

  <div class="architecture-card">
    <img src="assets/icons/unity-catalog.png" alt="">
    <span><strong>Managed Unity Catalog</strong><small>Metadata, identity and governance</small></span>
  </div>
  <div class="architecture-link"><span>catalog</span><b>↔</b></div>
  <div class="architecture-card">
    <img src="assets/icons/unity-catalog.png" alt="">
    <span><strong>Unity Catalog OSS</strong><small>Metadata and catalog REST API</small></span>
  </div>

  <div class="architecture-down">↓</div><div></div><div class="architecture-down">↓</div>

  <div class="architecture-card">
    <img src="assets/icons/databricks.svg" alt="">
    <span><strong>Databricks SQL / Spark</strong><small>Canonical TPC-H SQL</small></span>
  </div>
  <div class="architecture-link"><span>SQL engines</span><b>↔</b></div>
  <div class="architecture-card architecture-multi-icon">
    <span class="architecture-icons"><img src="assets/icons/apache-spark.svg" alt=""><img src="assets/icons/duckdb.svg" alt=""><img src="assets/icons/datafusion.svg" alt=""></span>
    <span><strong>Spark, DuckDB, DataFusion</strong><small>Multiple engines over the same tables</small></span>
  </div>

  <div class="architecture-down">↓</div><div></div><div class="architecture-down">↓</div>

  <div class="architecture-card">
    <img src="assets/icons/delta-lake.svg" alt="">
    <span><strong>External Delta tables</strong><small>Cloud object storage</small></span>
  </div>
  <div class="architecture-link"><span>data</span><b>↔</b></div>
  <div class="architecture-card architecture-multi-icon">
    <span class="architecture-icons"><img src="assets/icons/delta-lake.svg" alt=""><img src="assets/icons/seaweedfs.svg" alt=""></span>
    <span><strong>External Delta tables</strong><small>SeaweedFS S3 in the local reference</small></span>
  </div>

  <div class="architecture-support">
    <img src="assets/icons/mlflow.svg" alt=""><span><strong>Managed MLflow</strong><small>Experiment tracking</small></span>
  </div>
  <div class="architecture-link"><span>ML lifecycle</span><b>↔</b></div>
  <div class="architecture-support">
    <img src="assets/icons/mlflow.svg" alt=""><span><strong>MLflow OSS</strong><small>Experiment tracking</small></span>
  </div>

  <div class="architecture-support">
    <img src="assets/icons/unity-catalog.png" alt=""><span><strong>Integrated governance</strong><small>Policies enforced across the platform</small></span>
  </div>
  <div class="architecture-link"><span>governance</span><b>↔</b></div>
  <div class="architecture-support architecture-multi-icon">
    <span class="architecture-icons"><img src="assets/icons/cedar.png" alt=""><img src="assets/icons/datafusion.svg" alt=""></span>
    <span><strong>Cedar + DataFusion</strong><small>Partial enforcement prototype</small></span>
  </div>
</div>

## Tool mapping

| Capability | Databricks | OpenLakehouse | Comparison |
|---|---|---|---|
| Workflow orchestration | Lakeflow Jobs | Apache Airflow | Same task graph; different scheduler definitions and operational model |
| Batch compute | Databricks Runtime on serverless Spark | Apache Spark through Spark Connect | Shared PySpark logic; provisioning and lifecycle differ |
| Catalog | Managed Unity Catalog | Unity Catalog OSS | Core namespaces and external tables work; metadata and governance gaps remain |
| SQL analytics | Databricks SQL / Spark SQL | Spark SQL, DuckDB, DataFusion | All recorded Spark and DuckDB runs pass the 22 canonical queries |
| Table format | Delta Lake | Delta Lake OSS | Closest feature match in the tested workload |
| Object storage | Customer cloud storage | SeaweedFS S3 in the local reference | Same external-table design; SeaweedFS is a test-environment choice |
| ML tracking | Managed MLflow | MLflow OSS | Same public tracking API; service operations differ |
| Governance | Integrated Unity Catalog controls | UC OSS, Cedar and DataFusion prototype | Open enforcement is partial and not production-equivalent |

## Why this structure matters

Business transformations receive a Spark session and configuration; they do not select a platform. Storage paths, credentials, session creation, and scheduling stay in platform adapters. This boundary makes shared logic measurable and exposes the parts that really depend on a platform.

The comparison also uses independent checks. DuckDB recomputes table and Gold results, while a plain-Python implementation validates the SCD2 scenario. Agreement is therefore stronger evidence than running the same implementation twice.

## Important differences

Matching the task graph does not make the architectures equivalent. Databricks supplies an integrated control plane, managed compute, identity, governance, and operations. The open architecture assembles separate services, and its operator owns their integration, security, scaling, upgrades, and recovery.

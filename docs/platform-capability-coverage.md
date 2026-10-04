# Capability coverage

The broad comparison asks whether an important Databricks outcome is available natively, through an open alternative, through a workaround, or not at all.

| Status | Meaning |
|---|---|
| **Native** | Substantially equivalent capability in the open target |
| **Alternative** | Similar outcome through a different component or approach |
| **Workaround** | Possible with material limitations or manual work |
| **Missing** | No implemented equivalent in this repository's open stack |

## Pattern across the platform

| Area | Assessment |
|---|---|
| Delta tables and transactions | Strongest native overlap; 7 of 10 assessed capabilities are native |
| Batch compute | Core Spark is native; serverless, Photon, and managed lifecycle are not |
| SQL analytics | Queries are portable; warehouse operations, acceleration, and integrated BI differ |
| Streaming | Spark and Kafka foundations exist; Auto Loader operations need workarounds |
| Catalog and governance | Metadata basics work; fine-grained controls and integrated governance have major gaps |
| Declarative pipelines | Spark foundations overlap; managed operations and UI do not |
| Orchestration | Airflow covers common workflow outcomes through a different experience |
| Deployment | Open tools can deploy the system, but there is no unified workspace lifecycle |
| ML lifecycle | MLflow APIs travel well; managed serving and feature engineering do not |
| BI, AI, and observability | Mostly separate alternatives, workarounds, or gaps |

“Outcome coverage” in the generated report counts native features, alternatives, and workarounds. It should not be read as parity. “Native parity” is the stricter measure.

The [latest report](report.md#7-platform-capability-coverage) lists every assessed capability, gap, evidence level, target version, and as-of date. The underlying matrix is curated rather than exhaustive; rows marked planned have not been tested.

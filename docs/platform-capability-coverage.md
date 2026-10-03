# Platform capability coverage

The Freedom Score measures whether the workload can leave Databricks. Platform capability coverage answers a
different question: how much of each managed component's curated capability surface exists in the open target?
It is deliberately reported separately and is not averaged into the Freedom Score.

The source of truth is
[`freedom/assessment/feature_matrix.yaml`](../freedom/assessment/feature_matrix.yaml). The generated Freedom Report
shows two progress bars and an expandable capability table for every component pair:

- **Outcome coverage** counts `NATIVE`, `ALTERNATIVE`, and `WORKAROUND`: the outcome can be achieved, even if the
  implementation or operational experience differs.
- **Native parity** counts only `NATIVE`: the open target provides substantially equivalent semantics.
- **Required coverage** considers only capabilities exercised by the current workload.

## Status definitions

| Status | Meaning | Outcome covered | Native parity |
|---|---|---:|---:|
| `NATIVE` | Substantially equivalent capability in the open target | yes | yes |
| `ALTERNATIVE` | Same outcome through a different open component or approach | yes | no |
| `WORKAROUND` | Possible with material limitations or manual work | yes | no |
| `MISSING` | No implemented equivalent in this repository's open stack | no | no |
| `NOT_ASSESSED` | Evidence is insufficient | excluded | excluded |

This is a curated comparison, not a claim to enumerate every feature of either product. Every matrix records an
`as_of` date and explicit target versions. A documented claim can describe a known product difference; a measured
claim is backed by a repository check or artefact. Planned evidence identifies a future Freedom Challenge and does
not imply that the capability has already been tested.

## Updating the comparison

Add or change capabilities in the YAML matrix, retaining a precise gap or alternative for every non-native row.
Run `pytest tests/portability/test_feature_coverage.py` and regenerate the report with `make freedom-report`.

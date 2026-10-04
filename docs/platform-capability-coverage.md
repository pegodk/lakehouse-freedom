# Platform capability coverage

The Freedom Score summarises measured sharing between the two reference architectures. Platform capability
coverage answers a broader question: which outcomes are supported by each architecture, and whether support is
native, provided by an alternative, requires a workaround, or is missing. It is reported separately because a
curated capability comparison is different from a score calculated from workload measurements.

The source of truth is
[`freedom/assessment/feature_matrix.yaml`](../freedom/assessment/feature_matrix.yaml). The generated Freedom Report
shows two progress bars and an expandable capability table for every component pair:

- **Outcome coverage** counts `NATIVE`, `ALTERNATIVE`, and `WORKAROUND`: the outcome can be achieved, even if the
  implementation or operational experience differs.
- **Native parity** counts only `NATIVE`: the open target provides substantially equivalent semantics.
- **Required coverage** considers only capabilities exercised by the current workload.

## Status definitions

| Status | Meaning |
|---|---|
| `NATIVE` | Substantially equivalent capability in the open target |
| `ALTERNATIVE` | Same outcome through a different open component or approach |
| `WORKAROUND` | Possible with material limitations or manual work |
| `MISSING` | No implemented equivalent in this repository's open stack |
| `NOT_ASSESSED` | Evidence is insufficient |

This is a curated comparison, not a claim to enumerate every feature of either product. Every matrix records an
`as_of` date and explicit target versions. A documented claim can describe a known product difference; a measured
claim is backed by a repository check or artefact. Planned evidence identifies a future Freedom Challenge and does
not imply that the capability has already been tested.

## Updating the comparison

Add or change capabilities in the YAML matrix, retaining a precise gap or alternative for every non-native row.
Run `pytest tests/portability/test_feature_coverage.py` and regenerate the report with `make freedom-report`.

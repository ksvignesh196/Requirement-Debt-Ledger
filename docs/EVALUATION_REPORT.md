# Requirement Debt Ledger (RDL) — Reproducible Evaluation Notes

## Purpose

This document records the results produced by the project's current synthetic evaluation harness (`python evaluation.py`). It is an implementation-level evaluation note, not evidence from a production deployment or a study with human participants.

## Setup

The harness creates a synthetic project containing 15 requirement-debt records and three dependency patterns: a diamond-shaped dependency cluster, a linear cascade, and independent items. It compares three ranking policies under effort budgets of 15, 25, and 35 story points:

- **FIFO:** oldest deferred item first.
- **Static severity:** highest base risk first.
- **RDL:** the project's weighted risk / downstream-impact / business-impact / urgency score divided by an effort factor.

The harness also measures in-memory graph traversal on generated directed acyclic graphs. These timing values are local microbenchmarks, not end-to-end API response times.

## Results from the verified run

The run performed during project verification produced the following output. Risk values are points in the synthetic model.

| Effort budget | Policy | Items selected | Risk removed | Newly unblocked |
|---:|---|---:|---:|---:|
| 15 | FIFO | 3 | 184.2 | 3 |
| 15 | Static severity | 3 | 168.8 | 2 |
| 15 | RDL | 3 | 184.2 | 3 |
| 25 | FIFO | 4 | 267.6 | 3 |
| 25 | Static severity | 4 | 274.0 | 4 |
| 25 | RDL | 5 | 268.1 | 2 |
| 35 | FIFO | 6 | 333.0 | 2 |
| 35 | Static severity | 6 | 336.4 | 4 |
| 35 | RDL | 6 | 333.0 | 2 |

The synthetic portfolio contained 15 items with an initial aggregate dynamic risk of 508.3 points.

### Interpretation

The results do **not** show that RDL wins on every metric or every budget. At 15 points, RDL matched FIFO on the reported item count, risk removed, and newly unblocked count. At 25 points, RDL selected one additional item, but the static-severity policy removed slightly more risk and unblocked more downstream items. At 35 points, the static baseline again removed slightly more risk and unblocked more items. These results indicate that the proposed ranking balances multiple factors and changes the selected work; they do not establish universal superiority.

The `newly unblocked` metric counts a dependent requirement only when all of its prerequisite requirements are satisfied after the simulated selection. Each dependent requirement is counted once. This prevents double-counting in diamond-shaped dependency graphs.

## Graph timing run

The same verification run produced these in-memory timings:

| Nodes | Generated edges | Reachability check (ms) | Downstream traversal (ms) |
|---:|---:|---:|---:|
| 50 | 100 | 0.0021 | 0.0022 |
| 200 | 400 | 0.0189 | 0.0180 |
| 500 | 1,000 | 0.0483 | 0.0585 |
| 1,000 | 2,000 | 0.1135 | 0.1044 |

These measurements depend on the execution environment and are not a guarantee of production performance. They measure the in-memory graph operations in the evaluation script, not database queries, network transport, or full application response time.

## Limitations

1. The benchmark data is synthetic and intentionally small; it does not represent an industry dataset.
2. The RDL ranking weights and the daily risk-interest rate are proposed model assumptions. They have not been calibrated against historical project outcomes.
3. The ranking policies are simplified baselines. Different tie-breaking or capacity-allocation rules can change the comparison.
4. Graph timings are microbenchmarks and should be rerun on the machine used for any formal performance claim.
5. No claim is made about improved project success, reduced real-world defects, or superiority over commercial requirements-management platforms.

## Reproduction

From the project root, run:

```bash
python evaluation.py
```

The command prints the current synthetic benchmark results and fresh local timing measurements. Use the newly printed values when discussing a later run; do not assume timing values will be identical across machines.

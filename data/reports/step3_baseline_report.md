# Step 3 Baseline Results

This report records the output of `python src/run_baseline.py` run against the Step 2 cleaned scenario file.

## Overall results

- Scenarios evaluated: 10,000
- Input course records: 50,000
- Requested sessions: 125,109
- Scheduled sessions: 84,845
- Unplaced sessions: 40,264
- Hard clash violations: 0
- Soft preference penalties: 76,364
- Fully feasible scenarios: 2,593 of 10,000

## Results by scenario category

| Case type | Scenarios | Requested sessions | Scheduled sessions | Unplaced sessions | Fully feasible | Feasibility rate | Mean coverage | Mean unplaced | Hard violations |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| normal | 7,000 | 70,118 | 58,451 | 11,667 | 2,583 | 36.90% | 84.78% | 1.67 | 0 |
| boundary | 2,000 | 34,991 | 20,494 | 14,497 | 10 | 0.50% | 58.76% | 7.25 | 0 |
| stress | 1,000 | 20,000 | 5,900 | 14,100 | 0 | 0.00% | 29.50% | 14.10 | 0 |

## Interpretation

The baseline avoids hard room, faculty, and cohort clashes in the schedule it assigns. If a session cannot be placed, it is marked `unplaced`; it is not forced into an invalid room/slot. Normal, boundary and stress results are reported separately so feasibility limitations are visible.

This is a deterministic first-fit baseline, not the Genetic Algorithm. The GA should later be tested on the same scenarios and constraints for a fair comparison.

The scenario data and room inventory are simulated learning assumptions, not real university records. The baseline uses three simplified rooms (two classrooms and one lab) and a single ten-slot timeline.

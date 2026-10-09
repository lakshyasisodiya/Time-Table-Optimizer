# Step 3 — First-Fit Baseline Scheduler

## Goal

Implement the simple, non-Soft-Computing baseline described in the Time-Table Optimizer Step 1 project contract. This creates a comparison point for the later Genetic Algorithm (GA).

## Why this is not an ANN

The supplied Step 3 ANN PDF uses SC11 Water Quality Potability as its worked example and says students should adapt the model and measures to their own project. The assigned Time-Table Optimizer is a Genetic Algorithm scheduling project, not a water-quality classifier. Therefore this stage uses the project-specific baseline plan already documented in Step 1/Step 2: first-fit room/slot placement. No classifier loss curve or confusion matrix is claimed because the baseline does not classify labels.

## Input

`data/processed/cleaned_scenarios.csv`, created by the Step 2 pipeline. The script refuses to use the raw or invalid-test files.

Each scenario contains five course records (C01–C05), plus cohort, faculty, weekly demand, duration, required room type, candidate room-capacity/type facts, and a slot value.

## Simplified room and slot assumptions

The Step 1 fixture specifies three rooms and ten slots. For this baseline these are represented as R1 classroom/60 seats, R2 classroom/60 seats, and R3 lab/30 seats. Slots S1–S10 are the available periods. A two-slot session occupies its start slot and the following slot. These are teaching-project assumptions, not a real university room inventory.

In the baseline only, the existing `slot_id` is treated as a soft preferred start slot for reporting preference penalties. The algorithm itself scans S1 onward, as described in the Step 1 first-fit plan. An assignment outside that preferred start adds one soft penalty; it is not a hard violation.

## Baseline algorithm

1. Read each scenario and process its courses in course-code order.
2. Expand each course into its requested `weekly_sessions` individual meetings.
3. For each meeting, scan possible start slots from S1 to S10 (respecting duration).
4. For each candidate start slot, try compatible rooms in R1/R2/R3 order.
5. Accept the first placement that does not overlap the room, faculty, or cohort in any occupied slot.
6. If no placement is possible, mark the meeting unplaced rather than inventing a placement.
7. Count unplaced meetings and soft preference penalties, and audit the saved schedule for hard clashes.

## How to run

From the repository root, with the project environment active:

```powershell
python -m pip install matplotlib
python src/run_baseline.py
python -m unittest discover -s tests -v
```

Open `notebooks/02_baseline_scheduler.ipynb` and run its cells from top to bottom to retain visible evidence.

## Outputs

Under `results/step3_baseline/`:

- `baseline_schedule.csv` — each requested meeting, its room/slot assignment or unplaced status.
- `sample_scenario_schedule.csv` — readable schedule for one scenario.
- `baseline_metrics.csv` — one metrics row per scenario.
- `baseline_metrics_by_case.csv` — normal/boundary/stress summary.
- `scenario_feasibility_by_case.png` — percent of scenarios fully scheduled by category.
- `mean_unplaced_sessions_by_case.png` — mean unplaced sessions per scenario.
- `baseline_metadata.json` — method, room inventory, constraints, and assumptions.

## Measures

- **Scheduled sessions:** meetings that received a valid room and slot.
- **Unplaced sessions:** requested meetings for which no valid placement remained.
- **Hard violations:** overlapping room, faculty, or cohort assignments; the saved result must have zero.
- **Preference penalties:** assigned meetings whose start slot differs from the row's preferred slot.
- **Feasibility rate:** percentage of scenarios with all requested sessions placed.
- **Room-slot utilization:** occupied room-slot units divided by the 30 units available in this simplified room inventory.

## Limitations

This is a basic deterministic first-fit method, not the Genetic Algorithm. It uses only three simplified rooms and one S1–S10 timeline, so it is a learning baseline, not a deployable university scheduler. Infeasible scenarios may have unplaced meetings; that result must be reported honestly. The GA can later be compared against this baseline using the same scenarios and constraints.

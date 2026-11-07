# Step 5 — Product V1

> Complete this report with your team's real observations, screenshots, branch and member contributions. Do not claim a manual app test passed until you have run it on your computer.

## Team and project

- Project: Time-Table Optimizer
- Team: [enter your registered team and members]
- Branch and commit: [enter the actual Step 5 branch and commit]

## User task

A timetable coordinator enters the requirements for five courses and requests a timetable. Product V1 validates the input, calls the Step 4 Genetic Algorithm, and displays each scheduled or unplaced session with room, slot, hard-conflict count and soft preference penalty.

This version handles one five-course scenario per run, matching the Step 2 scenario structure. It is not a complete multi-week university scheduling system.

## Interface and method

- Interface type: Streamlit local web application
- Entry file: `app.py`
- Method adapter: `src/product_scheduler.py`
- Step 4 method: `src/run_genetic_algorithm.py` (`schedule_one_scenario`)
- Hard-conflict audit and room inventory: `src/run_baseline.py`
- Input: `course_id`, `cohort_id`, `faculty_id`, `weekly_sessions`, `duration_slots`, `required_room_type`, `room_capacity`, `slot_id`
- Output: per-session room and slot assignments, scheduled/unplaced status, hard violations, and soft preference penalties
- Data flow: input table or CSV → validation → Step 4 Genetic Algorithm → hard-conflict audit → timetable and downloadable CSV files

## Fixed assumptions

The app preserves the Step 1–4 example inventory: R1 classroom (60 seats), R2 classroom (60 seats), and R3 lab (30 seats); ten slots S1–S10; cohorts G1/G2; faculty F1–F3; course IDs C01–C05. A preferred slot is a soft preference. Room, faculty and cohort overlaps are hard constraints.

## Run instructions

From the repository root and the same `.venv` used in Step 4:

1. Install Product V1 dependencies: `python -m pip install -r requirements-product-v1.txt`
2. Launch the app: `python -m streamlit run app.py`
3. Open the local URL shown by Streamlit (normally `http://localhost:8501`).
4. Enter or upload five course rows, then choose **Generate timetable**.
5. Download the timetable or summary CSV from the results section.

Command-line consistency check: `python src/check_product_scheduler.py`

Automated tests: `python -m unittest discover -s tests -p "test_product_scheduler.py" -v`

## Actual test evidence

Record the observed result from your own app run. The automated unit tests do not replace manual interface testing.

| Case | Expected behaviour | Observed behaviour | Pass/Fail | Evidence path |
|---|---|---|---|---|
| Normal sample input | Generate a timetable and show summary | [record] | [record] | [screenshot/path] |
| Boundary values (1 and 4 sessions; 1 and 2 slots) | Accept documented limits | [record] | [record] | [screenshot/path] |
| Missing or invalid field | Show a clear field-specific message | [record] | [record] | [screenshot/path] |
| Room capacity above available inventory | Reject the input with a clear explanation | [record] | [record] | [screenshot/path] |
| Same input through app and method check | Produce matching deterministic output with same GA settings | [record] | [record] | [CSV/path] |

## Earlier feedback addressed

- Step 1: retains course, cohort, faculty, room and slot assumptions.
- Step 2: uses the documented five-course scenario input schema and simulated-data assumptions.
- Step 3: retains first-fit as the accepted baseline; this app uses the Step 4 GA as its scheduling method.
- Step 4: calls the existing GA with the documented room inventory and hard constraints. The first-fit and GA benchmark evidence is not overwritten.

## Limitations and responsible use

- The input is a simulated five-course case, not a live university timetable feed.
- The room inventory and faculty/cohort IDs are the fixed project assumptions, not verified university resources.
- An unplaced session is not proof of mathematical infeasibility; it can also reflect the current search budget, ordering and constraints.
- A successful hard-conflict audit only means the generated schedule passed the encoded room, faculty and cohort overlap checks.
- The Genetic Algorithm is stochastic in general; the app exposes a seed and search settings for reproducibility. Different settings may produce different outcomes.
- A timetable should be reviewed by the responsible coordinator before any real-world use.

## Screenshots and evidence

Save actual screenshots under `docs/evidence/step5/` showing:

1. The input form with five course rows.
2. A successful generated timetable and its metrics.
3. A clear validation error for a deliberately invalid input.
4. The downloaded output CSV or the consistency-check output.

## Team contributions

- [Member]: [specific implementation, testing or documentation work and evidence]
- [Member]: [specific implementation, testing or documentation work and evidence]
- [Add actual team members only]

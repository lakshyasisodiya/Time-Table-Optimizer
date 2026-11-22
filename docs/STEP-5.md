# Step 5 — Product V1

## Team and project

- Project: Time-Table Optimizer
- Team: Good Boys
- Team members:
  - Lakshya Sisodiya
  - Rahul Kumar Pathak
  - Md. Asif
- GitHub branch: `step-5-product-v1`
- Base commit before revision: `c2c35e1`

## User task

A timetable coordinator enters the requirements for five courses and requests a timetable. Product V1 validates the input, calls the Step 4 Genetic Algorithm, and displays scheduled and unplaced sessions with room assignments, time slots, hard-conflict counts and soft preference penalties.

This version handles one five-course scenario per run, matching the Step 2 scenario structure. It is not a complete multi-week university scheduling system.

## Interface and method

- Interface type: Streamlit local web application
- Entry file: `app.py`
- Method adapter: `src/product_scheduler.py`
- Step 4 method: `src/run_genetic_algorithm.py` (`schedule_one_scenario`)
- Hard-conflict audit and room inventory: `src/run_baseline.py`
- Input fields: `course_id`, `cohort_id`, `faculty_id`, `weekly_sessions`, `duration_slots`, `required_room_type`, `room_capacity` and `slot_id`
- Output: Per-session room and slot assignments, scheduled/unplaced status, hard violations and soft preference penalties.

### Data flow

Course input table or CSV → Input validation → Step 4 Genetic Algorithm → Hard-conflict audit → Generated timetable → Downloadable CSV files.

## Fixed assumptions

The application preserves the Step 1–4 example inventory:

- R1: Classroom, 60 seats
- R2: Classroom, 60 seats
- R3: Laboratory, 30 seats
- Time slots: S1–S10
- Cohorts: G1 and G2
- Faculty: F1, F2 and F3
- Course IDs: C01–C05

A preferred slot is a soft preference. Room, faculty and cohort overlaps are hard constraints.

## Run instructions

Run the application from the repository root using the project's configured Python virtual environment.

1. Activate the environment:

   `.\.venv\Scripts\Activate.ps1`

2. Launch Streamlit:

   `python -m streamlit run app.py`

3. Open the local URL shown in the terminal, normally `http://localhost:8501`.

4. Enter or upload five course rows.

5. Select **Generate timetable**.

6. Review the generated timetable and download the timetable or summary CSV.

Automated test command:

`python -m unittest discover -s tests -v`

## Actual test evidence

The following results were observed during manual application testing.

| Test | Expected behaviour | Actual observed result | Status |
|---|---|---|---|
| Normal sample input | Generate timetable and show summary | 8/8 scheduled, 0 unplaced, 0 hard violations, 3 soft penalties | PASS |
| Minimum weekly sessions | Accept 1 session | 7/7 scheduled, 0 unplaced, 0 hard violations | PASS |
| Maximum weekly sessions | Accept 4 sessions | 10/10 scheduled, 0 unplaced, 0 hard violations | PASS |
| Minimum duration | Accept 1 slot | 8/8 scheduled, 0 unplaced, 0 hard violations, 3 soft penalties | PASS |
| Maximum duration | Accept 2 slots | 8/8 scheduled, 0 unplaced, 0 hard violations, 3 soft penalties | PASS |
| Missing required field | Show a clear validation message | Empty C01 weekly_sessions was rejected. No timetable generated. | PASS |
| Invalid text input | Reject text in a numeric field | CSV value `abc` was rejected with an "enter a whole number" message. | PASS |
| Invalid room capacity | Reject capacity above available inventory | Lab capacity 31 was rejected. Maximum available lab capacity is 30. | PASS |
| Application and Python consistency | Produce matching results with identical inputs and GA settings | UI and Python reference timetables matched exactly. 8 scheduled, 0 unplaced, 0 hard violations. | PASS |
| Missing Genetic Algorithm file | Display a clear missing-file message | Updated application displayed a readable missing-file message instead of a Python traceback. | PASS |
| Recovery after restoring GA file | Resume normal timetable generation | Application generated 8/8 sessions, 0 unplaced and 0 hard violations after restoration. | PASS |

## Automated test results

The full Python automated test suite was executed using:

`python -m unittest discover -s tests -v`

Observed results:

| Test file | Passed tests |
|---|---:|
| Baseline scheduler | 3 |
| Genetic scheduler | 3 |
| Product scheduler | 7 |
| **Total** | **13** |

All 13 tests completed successfully with the final output showing `OK`.

## Application and Python consistency

The same five-course input was compared using the application and Python scheduling method with identical Genetic Algorithm settings:

- Population size: 8
- Generations: 5
- Random seed: 42

Observed result:

- UI and Python reference timetables matched exactly.
- Scheduled sessions: 8
- Unplaced sessions: 0
- Hard violations: 0

The comparison was performed using the Step 6 validation comparison script. The output files were generated under `data/reports/` in that validation work.

## Missing-file handling improvement

During the initial missing-file test, removing `src/run_genetic_algorithm.py` caused a Python `ModuleNotFoundError` traceback.

The `app.py` entry point was updated with missing-module handling.

After this improvement, the application displayed:

"Required scheduling file is missing: src/run_genetic_algorithm.py"

It also instructed the user to restore the missing file and restart the application.

The missing-file test was performed using a separate temporary project copy, leaving the original project files untouched.

After restoring the Genetic Algorithm file, the application successfully opened and generated the normal timetable again.

## Earlier feedback addressed

- Step 1: Retains the course, cohort, faculty, room and slot assumptions.
- Step 2: Uses the documented five-course scenario input structure and simulated-data assumptions.
- Step 3: Retains first-fit as the accepted baseline.
- Step 4: Calls the existing Genetic Algorithm with the documented room inventory and hard constraints.
- The accepted baseline and GA benchmark evidence remain unchanged.

## Limitations and responsible use

- The application uses simulated five-course inputs, not a live university timetable feed.
- The room inventory and faculty/cohort IDs are fixed project assumptions, not verified university resources.
- An unplaced session is not proof of mathematical infeasibility. Search budget, ordering and constraints may also affect placement.
- A successful hard-conflict audit only verifies the encoded room, faculty and cohort overlap checks.
- The Genetic Algorithm is stochastic in general. The application exposes a random seed and search settings for reproducibility.
- A timetable should be reviewed and approved by the responsible coordinator before real-world use.

## Screenshots and evidence

The following confirmed screenshots are saved in the repository:

1. [Normal generated timetable](evidence/step5/normal_result_retest.png)
2. [Missing Genetic Algorithm file error](evidence/step5/missing_GA_file_error.png)
3. [Successful recovery after restoring the file](evidence/step5/recovery_after_restore.png)
4. [Output explanation](evidence/step5/evidence/3/1b_output_explanation.png)

Screenshot folder:

`docs/evidence/step5/`

CSV comparison evidence was generated during Step 6 validation under:

`data/reports/step6_ui_schedule.csv`

`data/reports/step6_reference_schedule.csv`
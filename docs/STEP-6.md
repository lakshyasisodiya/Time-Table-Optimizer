# Step 6 — Testing and Validation

## 1. Project and Environment

- Project: Time-Table Optimizer
- Team: Good Boys
- Team members:
  - Lakshya Sisodiya
  - Rahul Kumar Pathak
  - Md. Asif
- Branch: `step-6-testing`
- Commit tested: `966cdea`
- Python version: 3.14.8
- Python environment: `.venv`
- Interface: Streamlit local web application
- Entry file: `app.py`
- Scheduling method: Step 4 Genetic Algorithm
- Launch command: `python -m streamlit run app.py`

## 2. Testing Objectives

The objective of Step 6 is to validate the Product V1 timetable application using normal inputs, boundary values, invalid inputs, missing dependencies, recovery testing, output consistency and automated unit tests.

The tests use the project's five-course scenario, fixed room inventory, faculty, cohorts and ten predefined time slots.

## 3. Planned Tests and Results

| ID | Input or Action | Expected Behaviour | Actual Result | Status |
|---|---|---|---|---|
| T01 | Generate timetable using default five-course inputs | Generate timetable, display scheduling metrics and provide CSV downloads | 8/8 scheduled, 0 unplaced, 0 hard violations, 3 soft penalties | PASS |
| T02 | Set C01 weekly sessions to 1 | Accept minimum boundary value | 7/7 scheduled, 0 unplaced, 0 hard violations, 2 soft penalties | PASS |
| T03 | Set C01 weekly sessions to 4 | Accept maximum boundary value | 10/10 scheduled, 0 unplaced, 0 hard violations, 5 soft penalties | PASS |
| T04 | Set C03 lab capacity to 31 | Reject capacity above available lab inventory | Displayed validation error: no lab can hold 31; maximum capacity is 30. No timetable generated. | PASS |
| T05 | Upload CSV with abc in C01 weekly_sessions | Reject text in a numeric field | Displayed "enter a whole number" validation message. No timetable generated. | PASS |
| T06 | Leave C01 weekly_sessions empty | Display missing-input validation error | Displayed row-specific error: enter a finite whole number. No timetable generated. | PASS |
| T07 | Temporarily rename GA file in a separate project copy | Display clear missing-dependency message | Updated application identified the missing GA file and instructed the user to restore it. | PASS |
| T08 | Restore GA file and relaunch application | Generate a normal timetable again | 8/8 scheduled, 0 unplaced, 0 hard violations, 3 soft penalties. | PASS |
| T09 | Compare UI timetable CSV with Python reference CSV | Matching results for identical inputs and GA settings | Both CSV files matched exactly across 8 records and 16 columns. | PASS |
| T10 | Run automated Python unit tests | All applicable tests should pass | Previous complete run: 13 tests passed, 0 failures. | PASS (previous run) |

## 4. Additional Boundary Testing

Duration boundaries were also tested.

| Input | Expected Behaviour | Observed Result | Status |
|---|---|---|---|
| C03 duration = 1 | Accept minimum duration | 8/8 scheduled, 0 unplaced, 0 hard violations, 3 soft penalties | PASS |
| C03 duration = 2 | Accept maximum duration | 8/8 scheduled, 0 unplaced, 0 hard violations, 3 soft penalties | PASS |

Both minimum and maximum duration values were accepted.

## 5. Detailed Test Observations

### T01 — Normal timetable generation

The default five-course input was submitted using the Genetic Algorithm settings:

- Population size: 8
- Generations: 5
- Random seed: 42

Observed results:

- Requested sessions: 8
- Scheduled sessions: 8
- Unplaced sessions: 0
- Hard violations: 0
- Soft preference penalties: 3

The application displayed the generated timetable and downloadable CSV files.

### T02 — Minimum weekly sessions

C01 weekly sessions were changed from 2 to 1.

The application accepted the minimum value and generated all seven requested sessions.

No unplaced sessions or hard violations were reported.

### T03 — Maximum weekly sessions

C01 weekly sessions were changed from 1 to 4.

The application accepted the maximum value and generated all ten requested sessions.

No unplaced sessions or hard violations were reported.

### T04 — Invalid room capacity

C03 required room capacity was set to 31 while its required room type remained lab.

The application rejected the value and displayed:

`Row 3 — room_capacity: no lab in the fixed room inventory can hold 31; maximum is 30.`

No timetable was generated.

### T05 — Invalid text input

A CSV containing `abc` in C01's weekly_sessions field was uploaded.

The application rejected the text and displayed:

`Row 1 — weekly_sessions: enter a whole number.`

No timetable was generated.

### T06 — Missing required input

C01 weekly_sessions was left empty while the other fields remained valid.

The application displayed:

`Row 1 — weekly_sessions: enter a finite whole number.`

No timetable was generated.

### T07 — Missing Genetic Algorithm dependency

The application was tested using a separate temporary project copy.

The file `src/run_genetic_algorithm.py` was temporarily renamed.

The initial implementation produced a Python ModuleNotFoundError traceback. The application entry point was subsequently improved to handle missing scheduler modules.

The updated application displayed a clear message identifying the missing file and instructing the user to restore it and restart the application.

### T08 — Recovery after restoring the dependency

The renamed Genetic Algorithm file was restored in the temporary project copy.

The application reopened successfully and generated the normal timetable.

Observed results:

- Scheduled sessions: 8/8
- Unplaced sessions: 0
- Hard violations: 0
- Soft penalties: 3

This confirmed that normal scheduling resumed after the missing dependency was restored.

### T09 — UI and Python reference comparison

The application timetable was compared with the Python reference timetable using the same input and Genetic Algorithm configuration.

Files:

- UI timetable: `data/reports/step6_ui_schedule.csv`
- Reference timetable: `data/reports/step5_ui_reference_schedule.csv`
- Comparison script: `src/compare_step6_schedules.py`

Configuration:

- Population size: 8
- Generations: 5
- Random seed: 42

Observed terminal result:

`PASS: UI and Python reference timetables match exactly.`

- UI records: 8
- Reference records: 8
- Compared columns: 16
- Differences: 0

### T10 — Automated testing

The complete automated test suite was previously executed using:

`python -m unittest discover -s tests -v`

Observed output from that run:

- Baseline scheduler tests: 3 passed
- Genetic scheduler tests: 3 passed
- Product scheduler tests: 7 passed
- Total tests: 13
- Failed tests: 0

The terminal ended with `Ran 13 tests` and `OK`.

This result was obtained during the earlier Step 6 test run, before the Step 6 branch was recreated. It is recorded as a previous successful run, not as a new execution on commit `966cdea`.

## 6. Evidence and Output Files

### CSV evidence

- `data/reports/step6_ui_schedule.csv`
- `data/reports/step5_ui_reference_schedule.csv`

### Comparison script

- `src/compare_step6_schedules.py`

### Screenshot evidence

Store the corresponding captured screenshots in:

`docs/evidence/step6/`

Suggested filenames:

- `T01_normal_result.png`
- `T02_minimum_weekly_sessions.png`
- `T03_maximum_weekly_sessions.png`
- `T04_invalid_lab_capacity.png`
- `T05_invalid_text_input.png`
- `T06_missing_input.png`
- `T07_missing_GA_file.png`
- `T08_recovery_result.png`
- `T09_csv_comparison.png`
- `T10_automated_tests.png`

## 7. Failures, Fixes and Retests

During the initial missing-dependency test, removing the Genetic Algorithm module caused a Python ModuleNotFoundError traceback.

The application entry point `app.py` was updated with missing-module handling.

The updated implementation identifies missing scheduler modules and displays a readable error message explaining that the file must be restored before restarting the application.

The fix was tested using a separate temporary copy of the project.

After restoring the missing Genetic Algorithm file, the application reopened and generated the normal timetable successfully.

The original project files were preserved during this test.

## 8. Known Limitations

- The application uses simulated five-course inputs rather than live university records.
- The room inventory is fixed and contains two classrooms and one laboratory.
- The scheduler uses ten predefined time slots.
- The application is not connected to a live university timetable system.
- Genetic Algorithm results depend on the search settings, random seed and constraints.
- An unplaced session does not necessarily prove mathematical infeasibility.
- A successful hard-conflict audit verifies only the constraints implemented in the application.
- A generated timetable should be reviewed before real-world use.

## 9. Final Validation Summary

The testing work covered:

- Normal timetable generation.
- Minimum and maximum weekly-session values.
- Minimum and maximum duration values.
- Invalid room capacity.
- Invalid text input.
- Missing required input.
- Missing scheduler dependency.
- Recovery after dependency restoration.
- UI and Python reference consistency.
- Automated unit testing.

Observed scheduling results showed zero hard violations in the successful timetable tests.

The UI and Python reference CSV comparison produced an exact match across eight records and sixteen columns.

The earlier automated test run completed with thirteen passing tests.

The previous successful results are documented with their execution history so that test evidence is not confused with a new run on the recreated branch.
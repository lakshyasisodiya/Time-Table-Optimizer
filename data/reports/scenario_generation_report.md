# Scenario Generation Report — Time-Table Optimizer

## Source method

`src/generate_scenarios.py` generates simulated timetable scenarios using a fixed random seed of 42 and the constraints documented in `data/README.md`.

## Valid scenario set

- Distinct valid scenarios: 10,000
- Course records after cleaning: 50,000
- Normal scenarios: 7,000
- Boundary scenarios: 2,000
- Stress scenarios: 1,000

## Invalid testing set

The invalid set is separate and is used only to show that the validation rules reject deliberately broken inputs.

- Invalid test scenarios: 100
- Invalid test course records: 500

| Invalid test type | Rows |
|---|---:|
| invalid_course_id | 100 |
| invalid_faculty_id | 100 |
| invalid_weekly_sessions | 100 |
| invalid_duration_slots | 100 |
| invalid_slot_id | 100 |

## Strict usage rule

Invalid testing scenarios are not included in `data/processed/cleaned_scenarios.csv` or any other valid processed scenario file.

## Reproducibility

Running `python src/generate_scenarios.py` with the same code and seed regenerates the same scenario family. Running `python src/prepare_data.py` produces the same cleaned output and report structure.

## Limitation

All scenarios are simulated for academic testing. They must not be described as real university timetable records.

# Step 2 Data Quality Report — Time-Table Optimizer

## 1. Project purpose

Prepare a reproducible collection of simulated timetable scenarios for the later baseline and Genetic Algorithm stages.

## 2. Provenance

The data is simulated by the team from the assumptions established in Step 1. It is not a real university timetable and is not claimed to be real-world observations.

## 3. Raw inspection

| Measure | Result |
|---|---:|
| Raw valid rows | 50,100 |
| Raw columns | 11 |
| Missing numeric cells before cleaning | 50 |
| Exact duplicate rows before cleaning | 100 |

## 4. Cleaning

The cleaning pipeline copied the raw dataframe, filled missing numeric feature values with the column median, converted numeric fields back to whole-number form where required, removed exact duplicate rows, and reset the index.

| Measure | Result |
|---|---:|
| Rows before cleaning | 50,100 |
| Rows after cleaning | 50,000 |
| Duplicate rows removed | 100 |
| Missing required cells after cleaning | 0 |

## 5. Validation

Every applicable validation count must be zero after cleaning.

```text
missing_required_columns: 0
rows_with_missing_values: 0
duplicate_rows: 0
non_numeric_columns: 0
invalid_case_types: 0
invalid_course_ids: 0
invalid_cohort_ids: 0
invalid_faculty_ids: 0
invalid_weekly_sessions: 0
invalid_duration_slots: 0
invalid_required_room_types: 0
invalid_room_types: 0
invalid_room_capacity: 0
invalid_slot_ids: 0
room_capacity_type_mismatch: 0
required_room_type_mismatch: 0
scenarios_not_equal_to_5_rows: 0
scenarios_missing_course: 0
```

## 6. Scenario coverage

| Scenario type | Scenarios |
|---|---:|
| Normal | 7,000 |
| Boundary | 2,000 |
| Stress | 1,000 |
| Total | 10,000 |

Each valid scenario contains five course records, one for C01, C02, C03, C04 and C05.

## 7. Processed outputs

- `data/processed/cleaned_scenarios.csv`
- `data/processed/normal_scenarios.csv`
- `data/processed/boundary_scenarios.csv`
- `data/processed/stress_scenarios.csv`

Invalid testing scenarios are intentionally kept outside these processed files.

## 8. Limitation

The scenarios are simulated educational inputs. They do not represent real university scheduling records.

## 9. Academic honesty note

The 10,000 scenarios are generated from documented Step 1 assumptions using a fixed seed. They are not copied duplicates of one record, and invalid test cases are not mixed into the valid prepared dataset.

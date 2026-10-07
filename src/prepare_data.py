"""Reusable Step 2 preparation pipeline for Time-Table-Optimizer.

Run from the repository root:
    python src/prepare_data.py
"""

from pathlib import Path
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = PROJECT_ROOT / "data" / "raw"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
REPORT_DIR = PROJECT_ROOT / "data" / "reports"

VALID_RAW_FILE = RAW_DIR / "timetable_scenarios_raw.csv"
INVALID_RAW_FILE = RAW_DIR / "timetable_invalid_test_scenarios_raw.csv"

CLEANED_FILE = PROCESSED_DIR / "cleaned_scenarios.csv"
NORMAL_FILE = PROCESSED_DIR / "normal_scenarios.csv"
BOUNDARY_FILE = PROCESSED_DIR / "boundary_scenarios.csv"
STRESS_FILE = PROCESSED_DIR / "stress_scenarios.csv"

REQUIRED_COLUMNS = [
    "scenario_id",
    "case_type",
    "course_id",
    "cohort_id",
    "faculty_id",
    "weekly_sessions",
    "duration_slots",
    "required_room_type",
    "room_capacity",
    "room_type",
    "slot_id",
]

NUMERIC_COLUMNS = [
    "weekly_sessions",
    "duration_slots",
    "room_capacity",
]

VALID_COURSES = {f"C0{i}" for i in range(1, 6)}
VALID_COHORTS = {"G1", "G2"}
VALID_FACULTY = {"F1", "F2", "F3"}
VALID_ROOM_TYPES = {"classroom", "lab"}
VALID_SLOTS = {f"S{i}" for i in range(1, 11)}
VALID_CASE_TYPES = {"normal", "boundary", "stress"}


def validation_results(df: pd.DataFrame) -> dict[str, int]:
    """Return validation counts. Zero means that rule passes."""
    results: dict[str, int] = {}

    missing_columns = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    results["missing_required_columns"] = len(missing_columns)

    if missing_columns:
        return results

    results["rows_with_missing_values"] = int(
        df[REQUIRED_COLUMNS].isna().any(axis=1).sum()
    )
    results["duplicate_rows"] = int(df.duplicated().sum())

    results["non_numeric_columns"] = int(
        sum(not pd.api.types.is_numeric_dtype(df[col]) for col in NUMERIC_COLUMNS)
    )

    results["invalid_case_types"] = int(
        (~df["case_type"].isin(VALID_CASE_TYPES)).sum()
    )
    results["invalid_course_ids"] = int(
        (~df["course_id"].isin(VALID_COURSES)).sum()
    )
    results["invalid_cohort_ids"] = int(
        (~df["cohort_id"].isin(VALID_COHORTS)).sum()
    )
    results["invalid_faculty_ids"] = int(
        (~df["faculty_id"].isin(VALID_FACULTY)).sum()
    )
    results["invalid_weekly_sessions"] = int(
        (~df["weekly_sessions"].between(1, 4)).sum()
    )
    results["invalid_duration_slots"] = int(
        (~df["duration_slots"].isin([1, 2])).sum()
    )
    results["invalid_required_room_types"] = int(
        (~df["required_room_type"].isin(VALID_ROOM_TYPES)).sum()
    )
    results["invalid_room_types"] = int(
        (~df["room_type"].isin(VALID_ROOM_TYPES)).sum()
    )
    results["invalid_room_capacity"] = int(
        (df["room_capacity"] <= 0).sum()
    )
    results["invalid_slot_ids"] = int(
        (~df["slot_id"].isin(VALID_SLOTS)).sum()
    )

    classroom_bad = (
        (df["room_type"] == "classroom") & (df["room_capacity"] != 60)
    )
    lab_bad = (
        (df["room_type"] == "lab") & (df["room_capacity"] != 30)
    )
    results["room_capacity_type_mismatch"] = int((classroom_bad | lab_bad).sum())

    results["required_room_type_mismatch"] = int(
        (df["required_room_type"] != df["room_type"]).sum()
    )

    scenario_sizes = df.groupby("scenario_id").size()
    results["scenarios_not_equal_to_5_rows"] = int(
        (scenario_sizes != 5).sum()
    )

    def has_all_courses(series: pd.Series) -> bool:
        return set(series) == VALID_COURSES

    scenario_course_check = df.groupby("scenario_id")["course_id"].apply(has_all_courses)
    results["scenarios_missing_course"] = int((~scenario_course_check).sum())

    return results


def validate_data(df: pd.DataFrame) -> dict[str, int]:
    """Raise ValueError if any validation count is non-zero."""
    results = validation_results(df)

    failures = {name: count for name, count in results.items() if count != 0}

    if failures:
        raise ValueError(f"Step 2 validation failed: {failures}")

    return results


def clean_data(df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """Clean a copy without modifying the raw input dataframe."""
    clean_df = df.copy()

    missing_before = int(clean_df[NUMERIC_COLUMNS].isna().sum().sum())
    duplicates_before = int(clean_df.duplicated().sum())
    rows_before = len(clean_df)

    for column in NUMERIC_COLUMNS:
        clean_df[column] = clean_df[column].fillna(clean_df[column].median())

    clean_df["weekly_sessions"] = (
        clean_df["weekly_sessions"].round().astype(int)
    )
    clean_df["duration_slots"] = (
        clean_df["duration_slots"].round().astype(int)
    )
    clean_df["room_capacity"] = (
        clean_df["room_capacity"].round().astype(int)
    )

    clean_df = clean_df.drop_duplicates().reset_index(drop=True)

    summary = {
        "rows_before": rows_before,
        "rows_after": len(clean_df),
        "missing_numeric_cells_before": missing_before,
        "duplicates_before": duplicates_before,
        "duplicates_removed": rows_before - len(clean_df) if duplicates_before else 0,
        "missing_cells_after": int(clean_df[REQUIRED_COLUMNS].isna().sum().sum()),
    }

    return clean_df, summary


def write_reports(
    raw_df: pd.DataFrame,
    clean_df: pd.DataFrame,
    cleaning_summary: dict,
    validation: dict[str, int],
    invalid_df: pd.DataFrame,
) -> None:
    """Write the two Step 2 reports from actual execution results."""
    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    scenario_counts = (
        clean_df[["scenario_id", "case_type"]]
        .drop_duplicates()["case_type"]
        .value_counts()
        .to_dict()
    )

    invalid_counts = invalid_df["invalid_reason"].value_counts().to_dict()

    quality_report = f"""# Step 2 Data Quality Report — Time-Table Optimizer

## 1. Project purpose

Prepare a reproducible collection of simulated timetable scenarios for the later baseline and Genetic Algorithm stages.

## 2. Provenance

The data is simulated by the team from the assumptions established in Step 1. It is not a real university timetable and is not claimed to be real-world observations.

## 3. Raw inspection

| Measure | Result |
|---|---:|
| Raw valid rows | {len(raw_df):,} |
| Raw columns | {len(raw_df.columns)} |
| Missing numeric cells before cleaning | {cleaning_summary["missing_numeric_cells_before"]:,} |
| Exact duplicate rows before cleaning | {cleaning_summary["duplicates_before"]:,} |

## 4. Cleaning

The cleaning pipeline copied the raw dataframe, filled missing numeric feature values with the column median, converted numeric fields back to whole-number form where required, removed exact duplicate rows, and reset the index.

| Measure | Result |
|---|---:|
| Rows before cleaning | {cleaning_summary["rows_before"]:,} |
| Rows after cleaning | {cleaning_summary["rows_after"]:,} |
| Duplicate rows removed | {cleaning_summary["duplicates_removed"]:,} |
| Missing required cells after cleaning | {cleaning_summary["missing_cells_after"]:,} |

## 5. Validation

Every applicable validation count must be zero after cleaning.

```text
{chr(10).join(f"{name}: {count}" for name, count in validation.items())}
```

## 6. Scenario coverage

| Scenario type | Scenarios |
|---|---:|
| Normal | {scenario_counts.get("normal", 0):,} |
| Boundary | {scenario_counts.get("boundary", 0):,} |
| Stress | {scenario_counts.get("stress", 0):,} |
| Total | {clean_df["scenario_id"].nunique():,} |

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
"""

    scenario_report = f"""# Scenario Generation Report — Time-Table Optimizer

## Source method

`src/generate_scenarios.py` generates simulated timetable scenarios using a fixed random seed of 42 and the constraints documented in `data/README.md`.

## Valid scenario set

- Distinct valid scenarios: {clean_df["scenario_id"].nunique():,}
- Course records after cleaning: {len(clean_df):,}
- Normal scenarios: {scenario_counts.get("normal", 0):,}
- Boundary scenarios: {scenario_counts.get("boundary", 0):,}
- Stress scenarios: {scenario_counts.get("stress", 0):,}

## Invalid testing set

The invalid set is separate and is used only to show that the validation rules reject deliberately broken inputs.

- Invalid test scenarios: {invalid_df["scenario_id"].nunique():,}
- Invalid test course records: {len(invalid_df):,}

| Invalid test type | Rows |
|---|---:|
{chr(10).join(f"| {reason} | {count:,} |" for reason, count in invalid_counts.items())}

## Strict usage rule

Invalid testing scenarios are not included in `data/processed/cleaned_scenarios.csv` or any other valid processed scenario file.

## Reproducibility

Running `python src/generate_scenarios.py` with the same code and seed regenerates the same scenario family. Running `python src/prepare_data.py` produces the same cleaned output and report structure.

## Limitation

All scenarios are simulated for academic testing. They must not be described as real university timetable records.
"""

    (REPORT_DIR / "data_quality_report.md").write_text(
        quality_report, encoding="utf-8"
    )
    (REPORT_DIR / "scenario_generation_report.md").write_text(
        scenario_report, encoding="utf-8"
    )


def run_pipeline() -> None:
    """Run the complete reusable Step 2 pipeline."""
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    if not VALID_RAW_FILE.exists():
        raise FileNotFoundError(
            "Missing data/raw/timetable_scenarios_raw.csv. "
            "Run python src/generate_scenarios.py first."
        )

    if not INVALID_RAW_FILE.exists():
        raise FileNotFoundError(
            "Missing data/raw/timetable_invalid_test_scenarios_raw.csv. "
            "Run python src/generate_scenarios.py first."
        )

    raw_df = pd.read_csv(VALID_RAW_FILE)
    invalid_df = pd.read_csv(INVALID_RAW_FILE)

    clean_df, cleaning_summary = clean_data(raw_df)
    validation = validate_data(clean_df)

    clean_df.to_csv(CLEANED_FILE, index=False)
    clean_df[clean_df["case_type"] == "normal"].to_csv(NORMAL_FILE, index=False)
    clean_df[clean_df["case_type"] == "boundary"].to_csv(
        BOUNDARY_FILE, index=False
    )
    clean_df[clean_df["case_type"] == "stress"].to_csv(STRESS_FILE, index=False)

    write_reports(
        raw_df=raw_df,
        clean_df=clean_df,
        cleaning_summary=cleaning_summary,
        validation=validation,
        invalid_df=invalid_df,
    )

    print("TIME-TABLE OPTIMIZER STEP 2 DATA PIPELINE COMPLETED")
    print("-" * 65)
    print(f"Raw rows: {len(raw_df):,}")
    print(f"Cleaned rows: {len(clean_df):,}")
    print(f"Rows removed as exact duplicates: {cleaning_summary['duplicates_removed']:,}")
    print(f"Missing required cells after cleaning: {cleaning_summary['missing_cells_after']:,}")
    print(f"Valid scenarios: {clean_df['scenario_id'].nunique():,}")
    print("Scenario categories:")
    print(
        clean_df[["scenario_id", "case_type"]]
        .drop_duplicates()["case_type"]
        .value_counts()
    )
    print("Validation: PASS")
    print(f"Output folder: {PROCESSED_DIR.relative_to(PROJECT_ROOT)}")
    print(f"Report folder: {REPORT_DIR.relative_to(PROJECT_ROOT)}")


if __name__ == "__main__":
    run_pipeline()

"""Step 1 data validator for the Time-Table-Optimizer project.

Run from the repository root:
    python src/validate_data.py
"""

from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_FILE = PROJECT_ROOT / "data" / "sample_input.csv"

REQUIRED_COLUMNS = [
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
NUMERIC_COLUMNS = ["weekly_sessions", "duration_slots", "room_capacity"]

VALID_COURSES = {f"C0{i}" for i in range(1, 6)}      # C01..C05
VALID_COHORTS = {"G1", "G2"}
VALID_FACULTY = {"F1", "F2", "F3"}
VALID_ROOM_TYPES = {"classroom", "lab"}
VALID_SLOTS = {f"S{i}" for i in range(1, 11)}        # S1..S10


def check(condition, message):
    """Stop the script with a clear message if a rule fails."""
    assert condition, message


def main():
    df = pd.read_csv(DATA_FILE)

    print("STEP 1 DATA VALIDATION")
    print("-" * 45)
    print(f"Data shape: {df.shape[0]} rows x {df.shape[1]} columns")
    print(f"Columns: {df.columns.tolist()}")

    # 1. Required columns
    missing_cols = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    check(not missing_cols, f"Missing required columns: {missing_cols}")

    # 2. Missing values (shows which rows are bad)
    missing_per_col = df[REQUIRED_COLUMNS].isna().sum()
    print("\nMissing values per column:")
    print(missing_per_col)
    bad_rows = df[df[REQUIRED_COLUMNS].isna().any(axis=1)]
    if not bad_rows.empty:
        print("\nRows with missing values (CSV line = index + 2):")
        print(bad_rows)
    check(missing_per_col.sum() == 0, "Missing values found in the starter data.")

    # 3. Numeric columns really are numbers
    for col in NUMERIC_COLUMNS:
        check(pd.api.types.is_numeric_dtype(df[col]), f"{col} must be numeric.")

    # 4. Domain rules
    check(df["course_id"].isin(VALID_COURSES).all(), "course_id must be C01 to C05.")
    check(df["cohort_id"].isin(VALID_COHORTS).all(), "cohort_id must be G1 or G2.")
    check(df["faculty_id"].isin(VALID_FACULTY).all(), "faculty_id must be F1 to F3.")
    check(df["weekly_sessions"].between(1, 4).all(), "weekly_sessions must be 1 to 4.")
    check(df["duration_slots"].isin([1, 2]).all(), "duration_slots must be 1 or 2.")
    check(df["required_room_type"].isin(VALID_ROOM_TYPES).all(),
          "required_room_type must be classroom or lab.")
    check(df["room_type"].isin(VALID_ROOM_TYPES).all(),
          "room_type must be classroom or lab.")
    check((df["room_capacity"] > 0).all(), "room_capacity must be positive.")
    check(df["slot_id"].isin(VALID_SLOTS).all(), "slot_id must be S1 to S10.")

    print("\nSTEP 1 DATA CHECK PASSED")


if __name__ == "__main__":
    main()
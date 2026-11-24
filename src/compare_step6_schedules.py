
"""Compare the Step 6 UI timetable with the Python reference timetable."""

from pathlib import Path
import sys

import pandas as pd
from pandas.testing import assert_frame_equal

ROOT = Path(__file__).resolve().parents[1]
REPORT_DIR = ROOT / "data" / "reports"

UI_FILE = REPORT_DIR / "step6_ui_schedule.csv"
REFERENCE_FILE = REPORT_DIR / "step5_ui_reference_schedule.csv"

SORT_COLUMNS = ["scenario_id", "course_id", "session_number"]


def main():
    # Check that both CSV files exist.
    for path in (UI_FILE, REFERENCE_FILE):
        if not path.is_file():
            print(f"FAIL: Required CSV file not found: {path}")
            return 1

    try:
        ui_df = pd.read_csv(UI_FILE, encoding="utf-8-sig")
        reference_df = pd.read_csv(
            REFERENCE_FILE,
            encoding="utf-8-sig",
        )

        # Check that both files contain the same columns.
        if list(ui_df.columns) != list(reference_df.columns):
            print("FAIL: CSV columns do not match.")
            print("UI columns:", list(ui_df.columns))
            print("Reference columns:", list(reference_df.columns))
            return 1

        # Check the required identifying columns.
        missing = [
            column for column in SORT_COLUMNS
            if column not in ui_df.columns
        ]

        if missing:
            print(f"FAIL: Required columns are missing: {missing}")
            return 1

        # Sort both results so row order does not affect comparison.
        ui_df = (
            ui_df.sort_values(SORT_COLUMNS, kind="stable")
            .reset_index(drop=True)
        )

        reference_df = (
            reference_df.sort_values(SORT_COLUMNS, kind="stable")
            .reset_index(drop=True)
        )

        # Compare every output column and every session.
        assert_frame_equal(
            ui_df,
            reference_df,
            check_dtype=False,
            check_exact=True,
        )

        print("PASS: UI and Python reference timetables match exactly.")
        print(f"UI records: {len(ui_df)}")
        print(f"Reference records: {len(reference_df)}")
        print("Compared columns:", len(ui_df.columns))
        print(f"UI CSV: {UI_FILE}")
        print(f"Reference CSV: {REFERENCE_FILE}")

        return 0

    except (OSError, ValueError, AssertionError) as error:
        print("FAIL: Timetable comparison did not match.")
        print(error)
        return 1


if __name__ == "__main__":
    sys.exit(main())

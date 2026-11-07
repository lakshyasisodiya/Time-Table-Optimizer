"""Reproduce the sample timetable used by the Product V1 interface.

Run from the repository root:
    python src/check_product_scheduler.py
"""
from pathlib import Path
import sys

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.product_scheduler import run_product_schedule
INPUT_FILE = ROOT / "data" / "sample_product_v1_input.csv"
OUTPUT_DIR = ROOT / "data" / "reports"
OUTPUT_FILE = OUTPUT_DIR / "step5_ui_reference_schedule.csv"


def main() -> None:
    if not INPUT_FILE.is_file():
        raise FileNotFoundError(f"Sample input not found: {INPUT_FILE}")
    user_input = pd.read_csv(INPUT_FILE)
    schedule, summary = run_product_schedule(user_input, seed=42, population_size=8, generations=5)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    schedule.to_csv(OUTPUT_FILE, index=False)
    print("STEP 5 PRODUCT METHOD CHECK")
    print("---------------------------")
    print(f"Requested sessions: {summary['requested_sessions']}")
    print(f"Scheduled sessions: {summary['scheduled_sessions']}")
    print(f"Unplaced sessions: {summary['unplaced_sessions']}")
    print(f"Hard violations: {summary['hard_violations']}")
    print(f"Soft preference penalties: {summary['soft_preference_penalties']}")
    print(f"Saved reference schedule: {OUTPUT_FILE.relative_to(ROOT)}")


if __name__ == "__main__":
    main()

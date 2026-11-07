"""Product V1 input validation and connection to the Step 4 Genetic Algorithm.

This module does not change or retrain the GA. It validates one user-entered
five-course scenario, adapts it to the Step 4 schema, and calls the saved GA code.
"""
from __future__ import annotations

import math
from typing import Any

import pandas as pd

from src.run_baseline import ROOMS, audit_schedule
from src.run_genetic_algorithm import schedule_one_scenario

INPUT_COLUMNS = [
    "course_id",
    "cohort_id",
    "faculty_id",
    "weekly_sessions",
    "duration_slots",
    "required_room_type",
    "room_capacity",
    "slot_id",
]

VALID_COURSES = {f"C0{i}" for i in range(1, 6)}
VALID_COHORTS = {"G1", "G2"}
VALID_FACULTY = {"F1", "F2", "F3"}
VALID_ROOM_TYPES = {"classroom", "lab"}
VALID_SLOTS = {f"S{i}" for i in range(1, 11)}
SCENARIO_ID = "USER-INPUT-001"

SAMPLE_INPUT = pd.DataFrame(
    [
        ["C01", "G1", "F1", 2, 1, "classroom", 60, "S2"],
        ["C02", "G1", "F2", 2, 1, "classroom", 60, "S3"],
        ["C03", "G2", "F3", 2, 2, "lab", 30, "S5"],
        ["C04", "G2", "F1", 1, 1, "classroom", 60, "S7"],
        ["C05", "G1", "F3", 1, 1, "lab", 30, "S8"],
    ],
    columns=INPUT_COLUMNS,
)


def _integer_value(value: Any, field: str, row_number: int) -> int:
    """Convert a user value to an integer without silently rounding it."""
    if value is None or (isinstance(value, str) and not value.strip()):
        raise ValueError(f"Row {row_number} — {field}: enter a value.")
    try:
        numeric = float(value)
    except (TypeError, ValueError) as error:
        raise ValueError(f"Row {row_number} — {field}: enter a whole number.") from error
    if not math.isfinite(numeric) or not numeric.is_integer():
        raise ValueError(f"Row {row_number} — {field}: enter a finite whole number.")
    return int(numeric)


def validate_and_prepare_input(user_input: pd.DataFrame) -> pd.DataFrame:
    """Validate exactly five course rows and return the Step 4 GA input schema."""
    if not isinstance(user_input, pd.DataFrame):
        raise ValueError("Course input must be a table.")
    missing_columns = [column for column in INPUT_COLUMNS if column not in user_input.columns]
    if missing_columns:
        raise ValueError(f"Missing required columns: {', '.join(missing_columns)}.")
    if len(user_input) != 5:
        raise ValueError("Enter exactly five course rows (C01 to C05) for one scenario.")

    clean = user_input[INPUT_COLUMNS].copy().reset_index(drop=True)
    for column in ("course_id", "cohort_id", "faculty_id", "required_room_type", "slot_id"):
        if clean[column].isna().any():
            row = int(clean.index[clean[column].isna()][0]) + 1
            raise ValueError(f"Row {row} — {column}: enter a value.")
        clean[column] = clean[column].astype(str).str.strip()

    if clean["course_id"].duplicated().any():
        duplicate = clean.loc[clean["course_id"].duplicated(), "course_id"].iloc[0]
        raise ValueError(f"Course {duplicate} is repeated. Use each course ID C01–C05 once.")
    if set(clean["course_id"]) != VALID_COURSES:
        raise ValueError("Use each course ID exactly once: C01, C02, C03, C04 and C05.")

    for index, row in clean.iterrows():
        row_number = index + 1
        if row["cohort_id"] not in VALID_COHORTS:
            raise ValueError(f"Row {row_number} — cohort_id: choose G1 or G2.")
        if row["faculty_id"] not in VALID_FACULTY:
            raise ValueError(f"Row {row_number} — faculty_id: choose F1, F2 or F3.")
        if row["required_room_type"] not in VALID_ROOM_TYPES:
            raise ValueError(f"Row {row_number} — required_room_type: choose classroom or lab.")
        if row["slot_id"] not in VALID_SLOTS:
            raise ValueError(f"Row {row_number} — slot_id: choose S1 through S10.")

        weekly = _integer_value(row["weekly_sessions"], "weekly_sessions", row_number)
        duration = _integer_value(row["duration_slots"], "duration_slots", row_number)
        capacity = _integer_value(row["room_capacity"], "room_capacity", row_number)
        if not 1 <= weekly <= 4:
            raise ValueError(f"Row {row_number} — weekly_sessions: enter a value from 1 to 4.")
        if duration not in (1, 2):
            raise ValueError(f"Row {row_number} — duration_slots: choose 1 or 2.")
        if capacity <= 0:
            raise ValueError(f"Row {row_number} — room_capacity: enter a positive capacity.")
        max_capacity = max(
            room["room_capacity"] for room in ROOMS
            if room["room_type"] == row["required_room_type"]
        )
        if capacity > max_capacity:
            raise ValueError(
                f"Row {row_number} — room_capacity: no {row['required_room_type']} in the fixed "
                f"room inventory can hold {capacity}; maximum is {max_capacity}."
            )
        clean.at[index, "weekly_sessions"] = weekly
        clean.at[index, "duration_slots"] = duration
        clean.at[index, "room_capacity"] = capacity

    # Preserve the earlier data contract and fixed Step 1–4 inventory assumptions.
    clean.insert(0, "scenario_id", SCENARIO_ID)
    clean.insert(1, "case_type", "user_input")
    clean["room_type"] = clean["required_room_type"]
    return clean


def run_product_schedule(
    user_input: pd.DataFrame,
    seed: int = 42,
    population_size: int = 8,
    generations: int = 5,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Validate user input and run the Step 4 GA with the supplied settings."""
    scenario = validate_and_prepare_input(user_input)
    records, summary = schedule_one_scenario(
        scenario,
        seed=int(seed),
        population_size=int(population_size),
        generations=int(generations),
    )
    schedule = pd.DataFrame(records)
    hard_violations = int(audit_schedule(schedule))
    if hard_violations != 0:
        raise RuntimeError(f"The generated timetable has {hard_violations} hard violations.")

    result_summary = dict(summary)
    result_summary["hard_violations"] = hard_violations
    result_summary["soft_preference_penalties"] = int(result_summary["preference_penalties"])
    result_summary["method"] = "Step 4 Genetic Algorithm"
    result_summary["room_inventory"] = "; ".join(
        f"{room['room_id']}: {room['room_type']} ({room['room_capacity']} seats)" for room in ROOMS
    )
    return schedule, result_summary

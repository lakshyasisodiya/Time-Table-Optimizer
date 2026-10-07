"""Generate reproducible simulated timetable scenarios for Step 2.

Run from the repository root:
    python src/generate_scenarios.py

This generator creates:
- 10,000 valid scenarios
- 5 course records per valid scenario
- 100 invalid test scenarios (separate file)
- a fixed random seed of 42

The data is simulated from the Step 1 project assumptions. It is not real
university data.
"""

from pathlib import Path
import random
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = PROJECT_ROOT / "data" / "raw"
RAW_DIR.mkdir(parents=True, exist_ok=True)

SEED = 42
VALID_SCENARIO_COUNT = 10_000
INVALID_SCENARIO_COUNT = 100

VALID_OUTPUT = RAW_DIR / "timetable_scenarios_raw.csv"
INVALID_OUTPUT = RAW_DIR / "timetable_invalid_test_scenarios_raw.csv"

COURSES = [f"C0{i}" for i in range(1, 6)]
COHORTS = ["G1", "G2"]
FACULTY = ["F1", "F2", "F3"]
ROOM_TYPES = ["classroom", "lab"]
SLOTS = [f"S{i}" for i in range(1, 11)]

VALID_COLUMNS = [
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


def build_scenario(case_type: str, rng: random.Random) -> list[dict]:
    """Create one 5-course scenario with a deliberate difficulty profile."""
    rows = []

    # Stress scenarios intentionally reuse faculty/cohort values to increase
    # scheduling pressure while keeping every input field valid.
    if case_type == "stress":
        shared_faculty = rng.choice(FACULTY)
        shared_cohort = rng.choice(COHORTS)

    for course_id in COURSES:
        if case_type == "normal":
            cohort_id = rng.choice(COHORTS)
            faculty_id = rng.choice(FACULTY)
            weekly_sessions = rng.randint(1, 3)
            duration_slots = rng.choice([1, 2])

        elif case_type == "boundary":
            cohort_id = rng.choice(COHORTS)
            faculty_id = rng.choice(FACULTY)
            weekly_sessions = rng.choice([3, 4])
            duration_slots = rng.choice([1, 2])

        else:  # stress
            cohort_id = shared_cohort if rng.random() < 0.70 else rng.choice(COHORTS)
            faculty_id = shared_faculty if rng.random() < 0.70 else rng.choice(FACULTY)
            weekly_sessions = 4
            duration_slots = 2

        required_room_type = rng.choice(ROOM_TYPES)
        room_capacity = 30 if required_room_type == "lab" else 60
        room_type = required_room_type
        slot_id = rng.choice(SLOTS)

        rows.append(
            {
                "course_id": course_id,
                "cohort_id": cohort_id,
                "faculty_id": faculty_id,
                "weekly_sessions": weekly_sessions,
                "duration_slots": duration_slots,
                "required_room_type": required_room_type,
                "room_capacity": room_capacity,
                "room_type": room_type,
                "slot_id": slot_id,
            }
        )

    return rows


def scenario_signature(rows: list[dict]) -> tuple:
    """Return a hashable signature so scenarios are genuinely varied."""
    return tuple(
        (
            row["course_id"],
            row["cohort_id"],
            row["faculty_id"],
            row["weekly_sessions"],
            row["duration_slots"],
            row["required_room_type"],
            row["room_capacity"],
            row["room_type"],
            row["slot_id"],
        )
        for row in rows
    )


def generate_valid_scenarios() -> pd.DataFrame:
    """Generate 10,000 distinct scenario instances."""
    rng = random.Random(SEED)
    seen = set()
    all_rows = []

    scenario_number = 1

    for case_type, scenario_count in [
        ("normal", 7_000),
        ("boundary", 2_000),
        ("stress", 1_000),
    ]:
        created = 0

        while created < scenario_count:
            course_rows = build_scenario(case_type, rng)
            signature = scenario_signature(course_rows)

            if signature in seen:
                continue

            seen.add(signature)
            scenario_id = f"TTO-{scenario_number:05d}"
            scenario_number += 1
            created += 1

            for row in course_rows:
                row_with_ids = {
                    "scenario_id": scenario_id,
                    "case_type": case_type,
                    **row,
                }
                all_rows.append(row_with_ids)

    df = pd.DataFrame(all_rows, columns=VALID_COLUMNS)

    # Deliberately create a small amount of raw-data quality noise so that the
    # Step 2 cleaning stage has real before/after evidence:
    # - 50 missing numeric cells
    # - 100 exact duplicate rows
    df.loc[df.index[:50], "weekly_sessions"] = pd.NA

    duplicate_rows = df.iloc[100:200].copy()
    df = pd.concat([df, duplicate_rows], ignore_index=True)

    return df


def generate_invalid_test_scenarios() -> pd.DataFrame:
    """Create 100 separate invalid scenarios for validation evidence."""
    rng = random.Random(SEED + 1)
    rows = []

    invalid_rules = [
        ("invalid_course_id", lambda row: row.__setitem__("course_id", "C99")),
        ("invalid_faculty_id", lambda row: row.__setitem__("faculty_id", "F9")),
        ("invalid_weekly_sessions", lambda row: row.__setitem__("weekly_sessions", 0)),
        ("invalid_duration_slots", lambda row: row.__setitem__("duration_slots", 3)),
        ("invalid_slot_id", lambda row: row.__setitem__("slot_id", "S11")),
    ]

    for number in range(1, INVALID_SCENARIO_COUNT + 1):
        reason, mutate = invalid_rules[(number - 1) % len(invalid_rules)]
        scenario_id = f"TTO-INV-{number:03d}"

        base_rows = build_scenario("normal", rng)

        for position, row in enumerate(base_rows):
            row = dict(row)

            if position == 0:
                mutate(row)

            rows.append(
                {
                    "scenario_id": scenario_id,
                    "case_type": "invalid",
                    **row,
                    "invalid_reason": reason,
                }
            )

    return pd.DataFrame(rows)


def main() -> None:
    valid_df = generate_valid_scenarios()
    invalid_df = generate_invalid_test_scenarios()

    valid_df.to_csv(VALID_OUTPUT, index=False)
    invalid_df.to_csv(INVALID_OUTPUT, index=False)

    print("TIME-TABLE OPTIMIZER STEP 2 SCENARIO GENERATOR")
    print("-" * 55)
    print(f"Seed: {SEED}")
    print(f"Valid scenarios: {VALID_SCENARIO_COUNT:,}")
    print(f"Valid course records before raw-data cleanup: {VALID_SCENARIO_COUNT * 5:,}")
    print(f"Raw valid rows written: {len(valid_df):,}")
    print(f"Deliberate duplicate rows: {int(valid_df.duplicated().sum()):,}")
    print(
        "Missing weekly_sessions cells: "
        f"{int(valid_df['weekly_sessions'].isna().sum()):,}"
    )
    print("Valid scenario categories:")
    print(valid_df[["scenario_id", "case_type"]].drop_duplicates()["case_type"].value_counts())
    print()
    print(f"Invalid test scenarios: {INVALID_SCENARIO_COUNT:,}")
    print(f"Invalid test course records: {len(invalid_df):,}")
    print()
    print(f"Valid raw output: {VALID_OUTPUT.relative_to(PROJECT_ROOT)}")
    print(f"Invalid raw output: {INVALID_OUTPUT.relative_to(PROJECT_ROOT)}")


if __name__ == "__main__":
    main()

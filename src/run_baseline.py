"""Run a deterministic first-fit baseline for Time-Table Optimizer.

Run from repository root:
    python src/run_baseline.py

This is a simple non-Soft-Computing baseline, not the Genetic Algorithm.
It consumes the clean, valid scenario data produced by Step 2.
"""
from __future__ import annotations

from pathlib import Path
import json
import pandas as pd
import matplotlib.pyplot as plt

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_FILE = PROJECT_ROOT / "data" / "processed" / "cleaned_scenarios.csv"
RESULTS_DIR = PROJECT_ROOT / "results" / "step3_baseline"
SLOT_NUMBERS = list(range(1, 11))
SLOT_COUNT = len(SLOT_NUMBERS)

# Step 1 fixture says there are three rooms. These are the documented example rooms.
ROOMS = [
    {"room_id": "R1", "room_type": "classroom", "room_capacity": 60},
    {"room_id": "R2", "room_type": "classroom", "room_capacity": 60},
    {"room_id": "R3", "room_type": "lab", "room_capacity": 30},
]

REQUIRED_COLUMNS = {
    "scenario_id", "case_type", "course_id", "cohort_id", "faculty_id",
    "weekly_sessions", "duration_slots", "required_room_type", "room_capacity",
    "room_type", "slot_id",
}
VALID_COURSES = {f"C0{i}" for i in range(1, 6)}
VALID_COHORTS = {"G1", "G2"}
VALID_FACULTY = {"F1", "F2", "F3"}
VALID_ROOM_TYPES = {"classroom", "lab"}
VALID_SLOTS = {f"S{i}" for i in SLOT_NUMBERS}
VALID_CASE_TYPES = {"normal", "boundary", "stress"}


def load_scenarios(path: Path = DATA_FILE) -> pd.DataFrame:
    """Load and check Step 2's clean scenario file."""
    if not path.exists():
        raise FileNotFoundError(
            f"Cannot find {path.relative_to(PROJECT_ROOT)}. Run "
            "python src/prepare_data.py first."
        )
    df = pd.read_csv(path)
    missing_cols = sorted(REQUIRED_COLUMNS - set(df.columns))
    if missing_cols:
        raise ValueError(f"Missing required scenario columns: {missing_cols}")
    if df[list(REQUIRED_COLUMNS)].isna().any().any():
        raise ValueError("The clean scenario file still contains missing values.")
    if df.duplicated().any():
        raise ValueError("The clean scenario file still contains duplicate rows.")
    if not df["course_id"].isin(VALID_COURSES).all():
        raise ValueError("Invalid course_id found.")
    if not df["cohort_id"].isin(VALID_COHORTS).all():
        raise ValueError("Invalid cohort_id found.")
    if not df["faculty_id"].isin(VALID_FACULTY).all():
        raise ValueError("Invalid faculty_id found.")
    if not df["required_room_type"].isin(VALID_ROOM_TYPES).all():
        raise ValueError("Invalid required_room_type found.")
    if not df["slot_id"].isin(VALID_SLOTS).all():
        raise ValueError("Invalid slot_id found.")
    if not df["case_type"].isin(VALID_CASE_TYPES).all():
        raise ValueError("Invalid case_type found in valid scenario file.")
    if not df["weekly_sessions"].between(1, 4).all():
        raise ValueError("weekly_sessions must be in 1..4.")
    if not df["duration_slots"].isin([1, 2]).all():
        raise ValueError("duration_slots must be 1 or 2.")
    if not (df["room_capacity"] > 0).all():
        raise ValueError("room_capacity must be positive.")

    scenario_counts = df.groupby("scenario_id")["course_id"].agg(list)
    for scenario_id, course_ids in scenario_counts.items():
        if len(course_ids) != 5 or set(course_ids) != VALID_COURSES:
            raise ValueError(
                f"Scenario {scenario_id} must contain one record for each of C01..C05."
            )
    return df


def _slot_label(number: int) -> str:
    return f"S{number}"


def _session_conflict(
    room_id: str,
    faculty_id: str,
    cohort_id: str,
    occupied_slots: list[int],
    room_occupied: set[tuple[str, int]],
    faculty_occupied: set[tuple[str, int]],
    cohort_occupied: set[tuple[str, int]],
) -> bool:
    """Return True if a room, faculty, or cohort has an overlapping session."""
    for slot in occupied_slots:
        if (room_id, slot) in room_occupied:
            return True
        if (faculty_id, slot) in faculty_occupied:
            return True
        if (cohort_id, slot) in cohort_occupied:
            return True
    return False


def audit_schedule(schedule: pd.DataFrame) -> int:
    """Count hard clashes in scheduled rows; a correct output should have zero."""
    room_used: set[tuple[str, int, str]] = set()
    faculty_used: set[tuple[str, int, str]] = set()
    cohort_used: set[tuple[str, int, str]] = set()
    violations = 0
    assigned = schedule[schedule["status"] == "scheduled"]
    for row in assigned.to_dict("records"):
        duration = int(row["duration_slots"])
        start = int(str(row["start_slot"])[1:])
        occupied = range(start, start + duration)
        for slot in occupied:
            room_key = (row["scenario_id"], slot, row["room_id"])
            faculty_key = (row["scenario_id"], slot, row["faculty_id"])
            cohort_key = (row["scenario_id"], slot, row["cohort_id"])
            if room_key in room_used:
                violations += 1
            if faculty_key in faculty_used:
                violations += 1
            if cohort_key in cohort_used:
                violations += 1
            room_used.add(room_key)
            faculty_used.add(faculty_key)
            cohort_used.add(cohort_key)
    return violations


def schedule_one_scenario(scenario_df: pd.DataFrame) -> tuple[list[dict], dict]:
    """Schedule each requested weekly session using first-fit, without hard clashes.

    The Step 2 ``slot_id`` is treated as a soft preferred start slot for this
    baseline. The algorithm itself scans S1 onward as specified by the Step 1
    first-fit plan; an assigned session outside its preferred start slot adds a
    soft preference penalty but is not a hard failure.
    """
    scenario_id = str(scenario_df["scenario_id"].iloc[0])
    case_type = str(scenario_df["case_type"].iloc[0])
    room_occupied: set[tuple[str, int]] = set()
    faculty_occupied: set[tuple[str, int]] = set()
    cohort_occupied: set[tuple[str, int]] = set()
    records: list[dict] = []
    requested_sessions = 0

    scenario_df = scenario_df.sort_values("course_id")
    for course in scenario_df.to_dict("records"):
        weekly_sessions = int(course["weekly_sessions"])
        duration = int(course["duration_slots"])
        preferred_slot = int(str(course["slot_id"])[1:])
        requested_sessions += weekly_sessions
        compatible_rooms = [
            room for room in ROOMS
            if room["room_type"] == course["required_room_type"]
            and room["room_capacity"] >= int(course["room_capacity"])
        ]

        for session_number in range(1, weekly_sessions + 1):
            selected = None
            # Scan slots first, from earliest to latest; try compatible rooms in R1/R2/R3 order.
            last_start = SLOT_COUNT - duration + 1
            for start in range(1, last_start + 1):
                occupied_slots = list(range(start, start + duration))
                for room in compatible_rooms:
                    if not _session_conflict(
                        room["room_id"], course["faculty_id"], course["cohort_id"],
                        occupied_slots, room_occupied, faculty_occupied, cohort_occupied,
                    ):
                        selected = (room, start, occupied_slots)
                        break
                if selected is not None:
                    break

            common = {
                "scenario_id": scenario_id,
                "case_type": case_type,
                "course_id": course["course_id"],
                "session_number": session_number,
                "faculty_id": course["faculty_id"],
                "cohort_id": course["cohort_id"],
                "required_room_type": course["required_room_type"],
                "duration_slots": duration,
                "preferred_slot": _slot_label(preferred_slot),
            }

            if selected is None:
                records.append({
                    **common,
                    "room_id": "",
                    "room_type": "",
                    "start_slot": "",
                    "occupied_slots": "",
                    "preference_penalty": 0,
                    "status": "unplaced",
                    "unplaced_reason": "No compatible room/slot available without a hard clash",
                })
                continue

            room, start, occupied_slots = selected
            for slot in occupied_slots:
                room_occupied.add((room["room_id"], slot))
                faculty_occupied.add((course["faculty_id"], slot))
                cohort_occupied.add((course["cohort_id"], slot))
            penalty = int(start != preferred_slot)
            records.append({
                **common,
                "room_id": room["room_id"],
                "room_type": room["room_type"],
                "start_slot": _slot_label(start),
                "occupied_slots": "|".join(_slot_label(slot) for slot in occupied_slots),
                "preference_penalty": penalty,
                "status": "scheduled",
                "unplaced_reason": "",
            })

    schedule_df = pd.DataFrame(records)
    scheduled_df = schedule_df[schedule_df["status"] == "scheduled"]
    unplaced_df = schedule_df[schedule_df["status"] == "unplaced"]
    scheduled_slot_units = int(scheduled_df["duration_slots"].sum())
    total_room_slot_capacity = len(ROOMS) * SLOT_COUNT
    requested_slot_units = int(
        (scenario_df["weekly_sessions"].astype(int) * scenario_df["duration_slots"].astype(int)).sum()
    )
    summary = {
        "scenario_id": scenario_id,
        "case_type": case_type,
        "course_count": int(scenario_df["course_id"].nunique()),
        "requested_sessions": int(requested_sessions),
        "scheduled_sessions": int(len(scheduled_df)),
        "unplaced_sessions": int(len(unplaced_df)),
        "unplaced_courses": int(unplaced_df["course_id"].nunique()),
        "requested_slot_units": requested_slot_units,
        "scheduled_slot_units": scheduled_slot_units,
        "room_slot_utilization_pct": round(100 * scheduled_slot_units / total_room_slot_capacity, 2),
        "preference_penalties": int(scheduled_df["preference_penalty"].sum()),
        "feasible": bool(unplaced_df.empty),
    }
    return records, summary


def _summarize_by_case(metrics: pd.DataFrame) -> pd.DataFrame:
    grouped = metrics.groupby("case_type", sort=False)
    result = grouped.agg(
        scenarios=("scenario_id", "nunique"),
        requested_sessions=("requested_sessions", "sum"),
        scheduled_sessions=("scheduled_sessions", "sum"),
        unplaced_sessions=("unplaced_sessions", "sum"),
        feasible_scenarios=("feasible", "sum"),
        mean_unplaced_sessions=("unplaced_sessions", "mean"),
        mean_coverage_pct=("coverage_pct", "mean"),
        mean_room_slot_utilization_pct=("room_slot_utilization_pct", "mean"),
        preference_penalties=("preference_penalties", "sum"),
        hard_violations=("hard_violations", "sum"),
    ).reset_index()
    result["feasibility_rate_pct"] = (100 * result["feasible_scenarios"] / result["scenarios"]).round(2)
    for column in ["mean_unplaced_sessions", "mean_coverage_pct", "mean_room_slot_utilization_pct"]:
        result[column] = result[column].round(2)
    return result


def save_results(schedule: pd.DataFrame, metrics: pd.DataFrame, by_case: pd.DataFrame) -> None:
    """Save repeatable CSV, chart and metadata evidence under results/step3_baseline."""
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    schedule.to_csv(RESULTS_DIR / "baseline_schedule.csv", index=False)
    metrics.to_csv(RESULTS_DIR / "baseline_metrics.csv", index=False)
    by_case.to_csv(RESULTS_DIR / "baseline_metrics_by_case.csv", index=False)

    sample_id = metrics.iloc[0]["scenario_id"]
    schedule[schedule["scenario_id"] == sample_id].to_csv(
        RESULTS_DIR / "sample_scenario_schedule.csv", index=False
    )

    plt.figure(figsize=(7, 4))
    plt.bar(by_case["case_type"], by_case["feasibility_rate_pct"])
    plt.title("First-Fit Baseline: Fully Scheduled Scenarios by Case Type")
    plt.xlabel("Scenario category")
    plt.ylabel("Fully scheduled scenarios (%)")
    plt.ylim(0, 100)
    plt.tight_layout()
    plt.savefig(RESULTS_DIR / "scenario_feasibility_by_case.png", dpi=160)
    plt.close()

    plt.figure(figsize=(7, 4))
    plt.bar(by_case["case_type"], by_case["mean_unplaced_sessions"])
    plt.title("First-Fit Baseline: Mean Unplaced Sessions")
    plt.xlabel("Scenario category")
    plt.ylabel("Mean unplaced sessions per scenario")
    plt.tight_layout()
    plt.savefig(RESULTS_DIR / "mean_unplaced_sessions_by_case.png", dpi=160)
    plt.close()

    metadata = {
        "project": "Time-Table Optimizer",
        "step": 3,
        "method": "Deterministic first-fit baseline scheduler",
        "is_trained_model": False,
        "seed_required": False,
        "input_file": "data/processed/cleaned_scenarios.csv",
        "scenario_count": int(metrics["scenario_id"].nunique()),
        "input_course_record_count": int(sum(metrics["course_count"])),
        "slots": [f"S{i}" for i in SLOT_NUMBERS],
        "room_inventory": ROOMS,
        "hard_constraints": [
            "a room cannot host two sessions in an overlapping slot",
            "a faculty member cannot teach overlapping sessions",
            "a cohort cannot attend overlapping sessions",
            "a session duration must fit within S1..S10",
            "a room must satisfy required_room_type and capacity",
        ],
        "soft_preference": "slot_id from the scenario row is treated as a preferred session start; each assigned session starting elsewhere adds one penalty",
        "limitation": "The room inventory and single ten-slot weekly timeline are simplified assumptions inherited from the Step 1 teaching fixture.",
    }
    (RESULTS_DIR / "baseline_metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")


def run_pipeline(input_path: Path = DATA_FILE) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Run all valid scenarios and save results."""
    df = load_scenarios(input_path)
    all_schedule_records: list[dict] = []
    metric_records: list[dict] = []

    for _, scenario_df in df.groupby("scenario_id", sort=True):
        schedule_records, summary = schedule_one_scenario(scenario_df)
        all_schedule_records.extend(schedule_records)
        metric_records.append(summary)

    schedule = pd.DataFrame(all_schedule_records)
    metrics = pd.DataFrame(metric_records)
    metrics["coverage_pct"] = (
        100 * metrics["scheduled_sessions"] / metrics["requested_sessions"]
    ).round(2)
    metrics["hard_violations"] = 0

    # Audit the final assignments; fail loudly if a hard conflict ever appears.
    # Scenario id is included in all keys so separate scenarios cannot conflict with one another.
    hard_violations = audit_schedule(schedule)
    if hard_violations:
        raise AssertionError(f"Baseline output contains {hard_violations} hard violations.")
    metrics["hard_violations"] = 0

    by_case = _summarize_by_case(metrics)
    save_results(schedule, metrics, by_case)

    print("TIME-TABLE OPTIMIZER STEP 3 BASELINE COMPLETED")
    print("-" * 60)
    print(f"Input course records: {len(df):,}")
    print(f"Scenarios evaluated: {metrics['scenario_id'].nunique():,}")
    print(f"Sessions requested: {int(metrics['requested_sessions'].sum()):,}")
    print(f"Sessions scheduled: {int(metrics['scheduled_sessions'].sum()):,}")
    print(f"Sessions unplaced: {int(metrics['unplaced_sessions'].sum()):,}")
    print(f"Hard violations in saved schedules: {hard_violations}")
    print(f"Total preference penalties: {int(metrics['preference_penalties'].sum()):,}")
    print("\nRESULTS BY SCENARIO CATEGORY")
    print(by_case.to_string(index=False))
    print(f"\nResults saved to: {RESULTS_DIR.relative_to(PROJECT_ROOT)}")
    print("Baseline is a deterministic comparator; it is not the Genetic Algorithm.")
    return schedule, metrics, by_case


def main() -> None:
    run_pipeline()


if __name__ == "__main__":
    main()

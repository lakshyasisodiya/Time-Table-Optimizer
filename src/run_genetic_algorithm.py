"""Small permutation Genetic Algorithm for timetable scheduling.

Run the complete fair comparison with:
    python src/compare_baseline.py

The GA uses the same room inventory and hard constraints as src/run_baseline.py.
It evolves the order in which individual course meetings are placed. The decoder
always produces a clash-free partial schedule and marks meetings unplaced when
no compatible room/slot remains.
"""
from __future__ import annotations

import random
from typing import Any

import pandas as pd

from src.run_baseline import ROOMS, SLOT_COUNT, _slot_label, audit_schedule

POPULATION_SIZE = 8
GENERATIONS = 5
CROSSOVER_RATE = 0.85
MUTATION_RATE = 0.25
UNPLACED_WEIGHT = 1000


def _candidate_starts(preferred: int, duration: int) -> list[int]:
    """Valid starts in preference-distance order, ties resolved to earlier slots."""
    valid = list(range(1, SLOT_COUNT - duration + 2))
    return sorted(valid, key=lambda slot: (abs(slot - preferred), slot))


def _make_meetings(scenario_df: pd.DataFrame) -> list[dict[str, Any]]:
    meetings: list[dict[str, Any]] = []
    for course in scenario_df.sort_values("course_id").to_dict("records"):
        for session_number in range(1, int(course["weekly_sessions"]) + 1):
            meetings.append({
                "scenario_id": str(course["scenario_id"]),
                "case_type": str(course["case_type"]),
                "course_id": str(course["course_id"]),
                "session_number": session_number,
                "faculty_id": str(course["faculty_id"]),
                "cohort_id": str(course["cohort_id"]),
                "required_room_type": str(course["required_room_type"]),
                "required_capacity": int(course["room_capacity"]),
                "duration_slots": int(course["duration_slots"]),
                "preferred_slot_num": int(str(course["slot_id"])[1:]),
                "preferred_slot": str(course["slot_id"]),
            })
    return meetings


def _decode(order: list[int], meetings: list[dict[str, Any]]) -> tuple[list[dict], dict]:
    """Greedily decode a meeting-order chromosome into a clash-free schedule."""
    if not meetings:
        raise ValueError("A scenario must contain at least one requested meeting.")

    scenario_id = meetings[0]["scenario_id"]
    case_type = meetings[0]["case_type"]
    room_used: set[tuple[str, int]] = set()
    faculty_used: set[tuple[str, int]] = set()
    cohort_used: set[tuple[str, int]] = set()
    output: dict[int, dict] = {}

    for meeting_index in order:
        meeting = meetings[meeting_index]
        duration = meeting["duration_slots"]
        compatible_rooms = [
            room for room in ROOMS
            if room["room_type"] == meeting["required_room_type"]
            and room["room_capacity"] >= meeting["required_capacity"]
        ]
        selected = None
        for start in _candidate_starts(meeting["preferred_slot_num"], duration):
            occupied = list(range(start, start + duration))
            for room in compatible_rooms:
                conflict = any(
                    (room["room_id"], slot) in room_used
                    or (meeting["faculty_id"], slot) in faculty_used
                    or (meeting["cohort_id"], slot) in cohort_used
                    for slot in occupied
                )
                if not conflict:
                    selected = (room, start, occupied)
                    break
            if selected is not None:
                break

        common = {
            "scenario_id": scenario_id,
            "case_type": case_type,
            "course_id": meeting["course_id"],
            "session_number": meeting["session_number"],
            "faculty_id": meeting["faculty_id"],
            "cohort_id": meeting["cohort_id"],
            "required_room_type": meeting["required_room_type"],
            "duration_slots": duration,
            "preferred_slot": meeting["preferred_slot"],
        }
        if selected is None:
            output[meeting_index] = {
                **common, "room_id": "", "room_type": "", "start_slot": "",
                "occupied_slots": "", "preference_penalty": 0,
                "status": "unplaced",
                "unplaced_reason": "No compatible room/slot available without a hard clash",
            }
            continue

        room, start, occupied = selected
        for slot in occupied:
            room_used.add((room["room_id"], slot))
            faculty_used.add((meeting["faculty_id"], slot))
            cohort_used.add((meeting["cohort_id"], slot))
        output[meeting_index] = {
            **common,
            "room_id": room["room_id"],
            "room_type": room["room_type"],
            "start_slot": _slot_label(start),
            "occupied_slots": "|".join(_slot_label(slot) for slot in occupied),
            "preference_penalty": int(start != meeting["preferred_slot_num"]),
            "status": "scheduled",
            "unplaced_reason": "",
        }

    records = [output[i] for i in range(len(meetings))]
    scheduled = [row for row in records if row["status"] == "scheduled"]
    unplaced = [row for row in records if row["status"] == "unplaced"]
    requested_slot_units = int(sum(m["duration_slots"] for m in meetings))
    scheduled_slot_units = int(sum(int(row["duration_slots"]) for row in scheduled))
    summary = {
        "scenario_id": scenario_id,
        "case_type": case_type,
        "course_count": int(len({m["course_id"] for m in meetings})),
        "requested_sessions": int(len(meetings)),
        "scheduled_sessions": int(len(scheduled)),
        "unplaced_sessions": int(len(unplaced)),
        "unplaced_courses": int(len({row["course_id"] for row in unplaced})),
        "requested_slot_units": requested_slot_units,
        "scheduled_slot_units": scheduled_slot_units,
        "room_slot_utilization_pct": round(100 * scheduled_slot_units / (len(ROOMS) * SLOT_COUNT), 2),
        "preference_penalties": int(sum(int(row["preference_penalty"]) for row in scheduled)),
        "feasible": bool(not unplaced),
        # The decoder only accepts conflict-free placements; final output is audited below.
        "hard_violations": 0,
    }
    summary["coverage_pct"] = round(100 * summary["scheduled_sessions"] / summary["requested_sessions"], 2)
    return records, summary


def _order_crossover(parent_a: list[int], parent_b: list[int], rng: random.Random) -> list[int]:
    """Order crossover (OX) for permutation chromosomes."""
    size = len(parent_a)
    if size < 2:
        return parent_a.copy()
    left, right = sorted(rng.sample(range(size), 2))
    child: list[int | None] = [None] * size
    child[left:right + 1] = parent_a[left:right + 1]
    existing = set(child[left:right + 1])
    fill_values = [gene for gene in parent_b[right + 1:] + parent_b[:right + 1] if gene not in existing]
    positions = list(range(right + 1, size)) + list(range(0, left))
    # Positions between left and right already contain the copied segment.
    for position, gene in zip(positions, fill_values):
        child[position] = gene
    # Defensive check: every meeting index must appear exactly once.
    if any(gene is None for gene in child) or len(set(child)) != size:
        return parent_a.copy()
    return [int(gene) for gene in child]


def _mutate(order: list[int], rng: random.Random) -> list[int]:
    result = order.copy()
    if len(result) > 1 and rng.random() < MUTATION_RATE:
        i, j = rng.sample(range(len(result)), 2)
        result[i], result[j] = result[j], result[i]
    return result


def schedule_one_scenario(
    scenario_df: pd.DataFrame,
    seed: int = 42,
    population_size: int = POPULATION_SIZE,
    generations: int = GENERATIONS,
) -> tuple[list[dict], dict]:
    """Optimize scheduling order with a deterministic permutation GA.

    Fitness = 1000 * unplaced sessions + preference penalties. The large first
    weight prioritizes placing as many meetings as possible; preference matches
    break ties. Hard conflicts are prevented by the decoder, not traded away.
    """
    if population_size < 4:
        raise ValueError("population_size must be at least 4.")
    if generations < 1:
        raise ValueError("generations must be at least 1.")
    meetings = _make_meetings(scenario_df)
    if not meetings:
        raise ValueError("Scenario contains no meetings.")
    rng = random.Random(seed)
    base = list(range(len(meetings)))
    cache: dict[tuple[int, ...], tuple[int, list[dict], dict]] = {}

    def evaluate(order: list[int]):
        key = tuple(order)
        if key not in cache:
            records, summary = _decode(order, meetings)
            cost = UNPLACED_WEIGHT * summary["unplaced_sessions"] + summary["preference_penalties"]
            cache[key] = (int(cost), records, summary)
        return cache[key]

    population = [base.copy()]
    while len(population) < population_size:
        candidate = base.copy()
        rng.shuffle(candidate)
        population.append(candidate)

    def tournament() -> list[int]:
        candidates = rng.sample(population, min(3, len(population)))
        return min(candidates, key=lambda item: evaluate(item)[0]).copy()

    for _ in range(generations):
        population.sort(key=lambda item: evaluate(item)[0])
        next_population = [population[0].copy(), population[1].copy()]
        while len(next_population) < population_size:
            parent_a = tournament()
            parent_b = tournament()
            if rng.random() < CROSSOVER_RATE:
                child = _order_crossover(parent_a, parent_b, rng)
            else:
                child = parent_a.copy()
            next_population.append(_mutate(child, rng))
        population = next_population

    best = min(population, key=lambda item: evaluate(item)[0])
    _, records, summary = evaluate(best)
    summary["hard_violations"] = int(audit_schedule(pd.DataFrame(records)))
    if summary["hard_violations"] != 0:
        raise AssertionError(f"GA output contains {summary['hard_violations']} hard violations.")
    summary["ga_population_size"] = population_size
    summary["ga_generations"] = generations
    summary["ga_seed"] = seed
    return records, summary

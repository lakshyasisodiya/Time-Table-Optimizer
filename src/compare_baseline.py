"""Compare first-fit with a permutation Genetic Algorithm on identical scenarios.

Run from repository root:
    python src/compare_baseline.py

The comparison uses every valid Step 2 scenario (10,000 total). Both methods
run on the exact same scenario IDs, and a check ensures no scenario ID is split
across normal, boundary, or stress categories.
"""
from __future__ import annotations

from pathlib import Path
import json
import sys
import hashlib
import tempfile
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))
from src.run_baseline import DATA_FILE, ROOMS, SLOT_COUNT, load_scenarios, schedule_one_scenario as run_first_fit, audit_schedule
from src.run_genetic_algorithm import schedule_one_scenario as run_ga, POPULATION_SIZE, GENERATIONS

PROJECT_ROOT = Path(__file__).resolve().parents[1]
REPORT_DIR = PROJECT_ROOT / "data" / "reports"
RESULTS_DIR = PROJECT_ROOT / "results"
EXPECTED_SCENARIOS = 10_000
CASE_ORDER = ["normal", "boundary", "stress"]
METHODS = ["First-fit baseline", "Genetic Algorithm"]


def _select_scenarios(df: pd.DataFrame) -> pd.DataFrame:
    """Use all Step 2 scenarios after checking IDs and category separation."""
    if df.empty:
        raise ValueError("The cleaned scenario file is empty.")

    if not {"scenario_id", "course_id", "case_type"}.issubset(df.columns):
        raise ValueError("Scenario data must include scenario_id, course_id, and case_type.")

    scenario_info = df.groupby("scenario_id", dropna=False).agg(
        rows=("course_id", "size"),
        unique_courses=("course_id", "nunique"),
        case_types=("case_type", "nunique"),
    )
    bad_rows = scenario_info[scenario_info["rows"] != 5]
    if not bad_rows.empty:
        raise ValueError(f"Every scenario must contain exactly five course rows; invalid IDs: {list(bad_rows.index[:5])}")
    bad_courses = scenario_info[scenario_info["unique_courses"] != 5]
    if not bad_courses.empty:
        raise ValueError(f"Scenario course IDs are duplicated or incomplete: {list(bad_courses.index[:5])}")
    cross_category = scenario_info[scenario_info["case_types"] != 1]
    if not cross_category.empty:
        raise ValueError(f"Scenario IDs overlap category groups: {list(cross_category.index[:5])}")

    categories = set(df["case_type"].astype(str).unique())
    if categories != set(CASE_ORDER):
        raise ValueError(f"Expected categories {CASE_ORDER}, found {sorted(categories)}.")

    scenario_count = int(df["scenario_id"].nunique())
    if scenario_count != EXPECTED_SCENARIOS:
        raise ValueError(
            f"Expected all {EXPECTED_SCENARIOS:,} Step 2 scenarios, found {scenario_count:,}. "
            "Regenerate/prepare the official Step 2 scenario data before comparing."
        )
    expected_category_counts = {"normal": 7_000, "boundary": 2_000, "stress": 1_000}
    actual_category_counts = (
        df[["scenario_id", "case_type"]].drop_duplicates()["case_type"].value_counts().to_dict()
    )
    if actual_category_counts != expected_category_counts:
        raise ValueError(
            "The Step 2 category counts do not match the fixed benchmark. "
            f"Expected {expected_category_counts}, found {actual_category_counts}."
        )

    # Make the evaluation order explicit and reproducible. There is no random sampling.
    return df.sort_values(["scenario_id", "course_id"]).reset_index(drop=True)


def _normalise_summary(summary: dict, schedule_records: list[dict]) -> dict:
    result = dict(summary)
    schedule = pd.DataFrame(schedule_records)
    result["hard_violations"] = int(audit_schedule(schedule))
    result["coverage_pct"] = round(100 * result["scheduled_sessions"] / result["requested_sessions"], 2) if result["requested_sessions"] else 0.0
    result["feasible"] = bool(result["unplaced_sessions"] == 0)
    if result["hard_violations"] != 0:
        raise AssertionError(f"A saved method schedule has {result['hard_violations']} hard violations.")
    return result


def _summarise(paired: pd.DataFrame) -> pd.DataFrame:
    rows = []
    case_groups = [("overall", paired)]
    case_groups.extend((case, paired[paired["case_type"] == case]) for case in CASE_ORDER)
    for case, frame in case_groups:
        for method, prefix in [(METHODS[0], "baseline"), (METHODS[1], "ga")]:
            rows.append({
                "case_type": case,
                "method": method,
                "scenarios": int(frame["scenario_id"].nunique()),
                "requested_sessions": int(frame[f"{prefix}_requested_sessions"].sum()),
                "scheduled_sessions": int(frame[f"{prefix}_scheduled_sessions"].sum()),
                "unplaced_sessions": int(frame[f"{prefix}_unplaced_sessions"].sum()),
                "mean_coverage_pct": round(float(frame[f"{prefix}_coverage_pct"].mean()), 2),
                "mean_unplaced_sessions_per_scenario": round(float(frame[f"{prefix}_unplaced_sessions"].mean()), 2),
                "preference_penalties": int(frame[f"{prefix}_preference_penalties"].sum()),
                "hard_violations": int(frame[f"{prefix}_hard_violations"].sum()),
                "feasible_scenarios": int(frame[f"{prefix}_feasible"].sum()),
                "feasibility_rate_pct": round(100 * float(frame[f"{prefix}_feasible"].mean()), 2),
                "room_slot_utilization_pct_mean": round(float(frame[f"{prefix}_room_slot_utilization_pct"].mean()), 2),
            })
    return pd.DataFrame(rows)


def _make_comparison(metrics: pd.DataFrame) -> pd.DataFrame:
    measure_info = [
        ("mean_coverage_pct", "higher is better"),
        ("mean_unplaced_sessions_per_scenario", "lower is better"),
        ("preference_penalties", "lower is better"),
        ("hard_violations", "must remain zero"),
        ("feasibility_rate_pct", "higher is better"),
        ("room_slot_utilization_pct_mean", "interpret with coverage and unplaced sessions"),
    ]
    rows = []
    for case in ["overall", *CASE_ORDER]:
        subset = metrics[metrics["case_type"] == case].set_index("method")
        if not all(method in subset.index for method in METHODS):
            continue
        for metric, direction in measure_info:
            baseline = float(subset.loc[METHODS[0], metric])
            ga = float(subset.loc[METHODS[1], metric])
            rows.append({
                "case_type": case,
                "measure": metric,
                "first_fit_baseline": baseline,
                "genetic_algorithm": ga,
                "ga_minus_baseline": round(ga - baseline, 2),
                "interpretation_direction": direction,
            })
    return pd.DataFrame(rows)


def _write_chart(metrics: pd.DataFrame) -> Path:
    overall = metrics[metrics["case_type"] == "overall"].set_index("method")
    # Bar chart includes metrics with different scales in separate panels.
    fig, axes = plt.subplots(1, 3, figsize=(13, 4.5))
    categories = METHODS
    coverage = [float(overall.loc[m, "mean_coverage_pct"]) for m in categories]
    unplaced = [float(overall.loc[m, "mean_unplaced_sessions_per_scenario"]) for m in categories]
    penalties = [float(overall.loc[m, "preference_penalties"]) for m in categories]
    axes[0].bar(categories, coverage)
    axes[0].set_title("Mean session coverage")
    axes[0].set_ylabel("Percent (higher is better)")
    axes[0].set_ylim(0, 100)
    axes[1].bar(categories, unplaced)
    axes[1].set_title("Mean unplaced sessions")
    axes[1].set_ylabel("Sessions per scenario (lower is better)")
    axes[2].bar(categories, penalties)
    axes[2].set_title("Preference penalties total")
    axes[2].set_ylabel("Count (lower is better)")
    for axis in axes:
        axis.tick_params(axis="x", labelrotation=12)
        axis.grid(axis="y", alpha=0.25)
    fig.suptitle("Step 4 — First-fit Baseline vs Genetic Algorithm (all Step 2 scenarios)")
    fig.tight_layout()
    path = RESULTS_DIR / "step4_baseline_vs_ga.png"
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=180, bbox_inches="tight")
    plt.close(fig)
    return path


def _write_report(metrics: pd.DataFrame, comparison: pd.DataFrame, paired: pd.DataFrame, chart_path: Path) -> None:
    overall = metrics[metrics["case_type"] == "overall"].set_index("method")
    b = overall.loc[METHODS[0]]
    g = overall.loc[METHODS[1]]
    coverage_delta = float(g["mean_coverage_pct"] - b["mean_coverage_pct"])
    scheduled_delta = int(g["scheduled_sessions"] - b["scheduled_sessions"])
    unplaced_delta = float(g["mean_unplaced_sessions_per_scenario"] - b["mean_unplaced_sessions_per_scenario"])
    pref_delta = int(g["preference_penalties"] - b["preference_penalties"])
    if scheduled_delta > 0:
        placement_statement = f"Across all scenarios, the GA scheduled {scheduled_delta:,} more sessions than first-fit ({int(g['scheduled_sessions']):,} versus {int(b['scheduled_sessions']):,})."
    elif scheduled_delta < 0:
        placement_statement = f"Across all scenarios, the GA scheduled {abs(scheduled_delta):,} fewer sessions than first-fit ({int(g['scheduled_sessions']):,} versus {int(b['scheduled_sessions']):,})."
    else:
        placement_statement = "Both methods scheduled the same total number of sessions."
    if coverage_delta > 0:
        coverage_statement = f"The GA's mean coverage was {coverage_delta:.2f} percentage points higher than first-fit."
    elif coverage_delta < 0:
        coverage_statement = f"The GA's mean coverage was {abs(coverage_delta):.2f} percentage points lower than first-fit."
    else:
        coverage_statement = "The two methods had the same mean coverage across the full benchmark."
    if unplaced_delta < 0:
        unplaced_statement = f"The GA left {abs(unplaced_delta):.2f} fewer sessions unplaced per scenario on average."
    elif unplaced_delta > 0:
        unplaced_statement = f"The GA left {unplaced_delta:.2f} more sessions unplaced per scenario on average."
    else:
        unplaced_statement = "Both methods left the same mean number of sessions unplaced per scenario."
    if pref_delta < 0:
        pref_statement = f"The GA recorded {abs(pref_delta):,} fewer soft preference penalties over the evaluated scenarios."
    elif pref_delta > 0:
        pref_statement = f"The GA recorded {pref_delta:,} more soft preference penalties over the evaluated scenarios."
    else:
        pref_statement = "Both methods recorded the same total number of soft preference penalties."
    case_rows = []
    for case in ["overall", *CASE_ORDER]:
        for method in METHODS:
            row = metrics[(metrics.case_type == case) & (metrics.method == method)].iloc[0]
            case_rows.append(
                f"| {case} | {method} | {int(row.scenarios)} | {int(row.requested_sessions)} | {int(row.scheduled_sessions)} | {int(row.unplaced_sessions)} | {row.mean_coverage_pct:.2f} | {row.mean_unplaced_sessions_per_scenario:.2f} | {int(row.preference_penalties)} | {int(row.hard_violations)} | {row.feasibility_rate_pct:.2f}% |"
            )
    sample_count = paired["scenario_id"].nunique()
    text = f"""# Step 4 — Fair Baseline Comparison

## Team and project

- Project: Time-Table Optimizer (timetable scheduling / SC05-style adaptation)
- Team members and contributions: **Replace this prompt with the real member names and their specific work before submission. Do not invent contributions.**
- Branch: `step-4-baseline`

## Question

On identical simulated timetable scenarios, does a permutation Genetic Algorithm improve session coverage or soft time-preference satisfaction compared with deterministic first-fit, while keeping hard room, faculty and cohort conflicts at zero?

## Data and scenarios

- Source: `data/processed/cleaned_scenarios.csv`, generated by the project's Step 2 scenario pipeline.
- The source contains 10,000 simulated scenarios: normal, boundary and stress cases. It is not real university scheduling data.
- Evaluation set: all {sample_count:,} scenarios from Step 2; no scenario sampling is performed.
- Scenario ID check: every ID has exactly five distinct course rows and belongs to exactly one category (normal, boundary, or stress). This catches IDs accidentally shared across scenario groups.
- The exact same scenario IDs and meeting requests are run by both methods. Scenario IDs and per-method measures are recorded in `data/reports/step4_paired_scenario_results.csv`.

## Baseline rule

First-fit processes courses in course-code order and expands each course's `weekly_sessions`. For every meeting it scans candidate start slots from S1 onward and then compatible rooms (R1/R2/R3 order). It accepts the first assignment that avoids room, faculty and cohort overlap. If no assignment is possible, the meeting is marked unplaced. A meeting that starts outside its course's `slot_id` preference receives one soft preference penalty.

## Genetic Algorithm rule

The GA chromosome is a permutation of individual requested meetings. Its decoder places meetings in chromosome order, trying compatible start slots nearest to the course's preferred `slot_id`, then rooms. The decoder rejects conflicting placements, so hard room/faculty/cohort conflicts are never exchanged for a better score. The fitness is `1000 × unplaced sessions + preference penalties`, so placing an additional meeting takes priority over reducing a soft penalty. Order crossover and swap mutation search alternative meeting orders. Settings: population {POPULATION_SIZE}, generations {GENERATIONS}, fixed deterministic seeds per scenario.

## Fair-comparison checks

- [x] Both methods use the same simulated scenario rows and simplified room inventory.
- [x] Both methods use the same hard constraints: room, faculty and cohort cannot overlap in any occupied slot.
- [x] All 10,000 fixed Step 2 scenario IDs are used by both methods; the script rejects category overlap or missing scenarios.
- [x] Both outputs are audited for hard clashes; the reported totals below are measured from the run.
- [x] Soft preference penalties are separated from hard violations.
- [x] No results are filled from the SC11 worked example; all numbers below come from this project's run.

## Results

| Scenario group | Method | Scenarios | Requested | Scheduled | Unplaced | Mean coverage (%) | Mean unplaced / scenario | Preference penalties | Hard violations | Feasibility rate |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
{chr(10).join(case_rows)}

### Interpretation

{placement_statement} {coverage_statement} {unplaced_statement} {pref_statement} Both methods recorded zero hard violations across the complete benchmark.

The GA improves placement and soft preference penalties on this simulated benchmark, but it still leaves sessions unplaced. Those requests are not necessarily mathematically infeasible; they may remain unplaced because of the finite GA search budget and the decoder's greedy placement choices. Room-slot utilization should be interpreted alongside coverage and unplaced meetings, not as a stand-alone success measure.

## Limitations and responsible use

The data is simulated from simplified assumptions: three example rooms, ten available slots and five courses per scenario. The comparison uses all 10,000 generated scenarios, but this is still not evidence of performance on a real university timetable. The GA uses a population of {POPULATION_SIZE} and {GENERATIONS} generations per scenario. It depends on its encoded representation, fitness priorities, population and generation settings; it is not guaranteed to find a global optimum. Unplaced sessions are not necessarily truly infeasible: the greedy decoder or finite GA search may fail to find another valid ordering. A zero clash count does not mean every request was scheduled, so unplaced sessions are reported separately.

## Reproducibility and evidence

- Script: `src/compare_baseline.py`
- GA implementation: `src/run_genetic_algorithm.py`
- Executed notebook: `notebooks/03_baseline_comparison.ipynb` (run all cells and save outputs)
- Metrics: `data/reports/step4_baseline_metrics.csv`
- Comparison: `data/reports/step4_comparison.csv`
- Paired scenario outcomes: `data/reports/step4_paired_scenario_results.csv`
- Chart: `results/step4_baseline_vs_ga.png`
- Rerun from the repository root: `python src/compare_baseline.py`
- Automated tests: `python -m unittest discover -s tests -v`

## Team contributions

Before submission, replace this paragraph with each real member's name, specific implementation or analysis contribution, and corresponding evidence. Do not claim work that the member did not perform.
"""
    target = PROJECT_ROOT / "docs" / "STEP-4.md"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding="utf-8")


def _checkpoint_paths() -> tuple[Path, Path]:
    """Keep progress files in the OS temp folder, not in the Git repository."""
    identity = hashlib.sha256(str(PROJECT_ROOT.resolve()).encode("utf-8")).hexdigest()[:12]
    folder = Path(tempfile.gettempdir()) / f"time_table_optimizer_step4_{identity}"
    return folder / "paired_checkpoint.csv", folder / "checkpoint_metadata.json"


def _checkpoint_metadata() -> dict:
    data_hash = hashlib.sha256(DATA_FILE.read_bytes()).hexdigest()
    baseline_path = Path(__file__).resolve().with_name("run_baseline.py")
    ga_path = Path(__file__).resolve().with_name("run_genetic_algorithm.py")
    comparison_hash = hashlib.sha256(Path(__file__).resolve().read_bytes()).hexdigest()
    baseline_hash = hashlib.sha256(baseline_path.read_bytes()).hexdigest()
    ga_hash = hashlib.sha256(ga_path.read_bytes()).hexdigest()
    return {
        "source_sha256": data_hash,
        "comparison_script_sha256": comparison_hash,
        "baseline_script_sha256": baseline_hash,
        "ga_script_sha256": ga_hash,
        "population_size": POPULATION_SIZE,
        "generations": GENERATIONS,
        "seed_policy": "4200 + zero-based index in sorted scenario IDs",
        "room_inventory": ROOMS,
        "slot_count": SLOT_COUNT,
    }


def _load_checkpoint(
    csv_path: Path,
    metadata_path: Path,
    expected_metadata: dict,
    valid_scenario_ids: set[str],
) -> dict[str, dict]:
    """Load compatible partial work; discard stale/corrupt progress safely."""
    if not csv_path.is_file() or not metadata_path.is_file():
        return {}
    try:
        saved_metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        saved = pd.read_csv(csv_path)
        required_checkpoint_columns = {
            "scenario_id", "case_type", "baseline_requested_sessions", "baseline_scheduled_sessions",
            "baseline_unplaced_sessions", "baseline_coverage_pct", "baseline_preference_penalties",
            "baseline_hard_violations", "baseline_feasible", "baseline_room_slot_utilization_pct",
            "ga_requested_sessions", "ga_scheduled_sessions", "ga_unplaced_sessions", "ga_coverage_pct",
            "ga_preference_penalties", "ga_hard_violations", "ga_feasible", "ga_room_slot_utilization_pct",
        }
        if saved_metadata != expected_metadata or not required_checkpoint_columns.issubset(saved.columns):
            print("Ignoring an old Step 4 checkpoint because the data/settings changed or the checkpoint is incomplete.")
            csv_path.unlink(missing_ok=True)
            metadata_path.unlink(missing_ok=True)
            return {}
        saved["scenario_id"] = saved["scenario_id"].astype(str)
        if saved["scenario_id"].duplicated().any() or not set(saved["scenario_id"]).issubset(valid_scenario_ids):
            print("Ignoring an invalid Step 4 checkpoint and restarting safely.")
            csv_path.unlink(missing_ok=True)
            metadata_path.unlink(missing_ok=True)
            return {}
        return {str(row["scenario_id"]): row for row in saved.to_dict("records")}
    except (OSError, ValueError, json.JSONDecodeError, pd.errors.ParserError):
        print("Ignoring an unreadable Step 4 checkpoint and restarting safely.")
        csv_path.unlink(missing_ok=True)
        metadata_path.unlink(missing_ok=True)
        return {}


def _save_checkpoint(csv_path: Path, metadata_path: Path, records_by_id: dict[str, dict], metadata: dict) -> None:
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    ordered = [records_by_id[scenario_id] for scenario_id in sorted(records_by_id)]
    pd.DataFrame(ordered).to_csv(csv_path, index=False)
    metadata_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")


def main() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    if not DATA_FILE.exists():
        raise FileNotFoundError(f"Missing {DATA_FILE.relative_to(PROJECT_ROOT)}. Run python src/prepare_data.py first.")
    source = load_scenarios(DATA_FILE)
    selected = _select_scenarios(source)
    scenario_ids = sorted(selected["scenario_id"].astype(str).unique())
    valid_ids = set(scenario_ids)
    # Group once; do not repeatedly filter the entire 50,000-row table by each ID.
    scenario_groups = list(selected.groupby("scenario_id", sort=True))
    checkpoint_csv, checkpoint_meta_path = _checkpoint_paths()
    checkpoint_meta = _checkpoint_metadata()
    records_by_id = _load_checkpoint(checkpoint_csv, checkpoint_meta_path, checkpoint_meta, valid_ids)
    if records_by_id:
        print(f"Resuming Step 4 comparison from {len(records_by_id):,}/{len(scenario_ids):,} saved scenarios.")
    else:
        print(f"Starting Step 4 comparison on all {len(scenario_ids):,} scenarios.")
    checkpoint_meta_path.parent.mkdir(parents=True, exist_ok=True)
    checkpoint_meta_path.write_text(json.dumps(checkpoint_meta, indent=2), encoding="utf-8")

    for index, (scenario_id, scenario) in enumerate(scenario_groups):
        scenario_id = str(scenario_id)
        if scenario_id in records_by_id:
            continue
        scenario = scenario.copy()
        # First-fit baseline.
        b_records, b_summary = run_first_fit(scenario)
        b_summary = _normalise_summary(b_summary, b_records)
        # GA uses the exact same scenario; a stable seed makes the run repeatable.
        g_records, g_summary = run_ga(scenario, seed=4200 + index)
        g_summary = _normalise_summary(g_summary, g_records)
        rec = {
            "scenario_id": scenario_id,
            "case_type": str(scenario["case_type"].iloc[0]),
        }
        for prefix, summary in [("baseline", b_summary), ("ga", g_summary)]:
            for key in ["requested_sessions", "scheduled_sessions", "unplaced_sessions", "coverage_pct", "preference_penalties", "hard_violations", "feasible", "room_slot_utilization_pct"]:
                # Store feasibility as 0/1 so a checkpoint reload is unambiguous.
                value = summary[key]
                rec[f"{prefix}_{key}"] = int(value) if key == "feasible" else value
        records_by_id[scenario_id] = rec
        processed = len(records_by_id)
        if processed % 250 == 0:
            _save_checkpoint(checkpoint_csv, checkpoint_meta_path, records_by_id, checkpoint_meta)
        if processed % 500 == 0 or processed == len(scenario_ids):
            print(f"Evaluated {processed:,}/{len(scenario_ids):,} scenarios...")

    paired = pd.DataFrame([records_by_id[scenario_id] for scenario_id in scenario_ids])
    if paired.empty:
        raise ValueError("No scenarios were selected for comparison.")
    if int(paired["baseline_hard_violations"].sum()) != 0 or int(paired["ga_hard_violations"].sum()) != 0:
        raise AssertionError("At least one method produced hard violations; comparison stopped.")
    metrics = _summarise(paired)
    comparison = _make_comparison(metrics)

    # Guard against an accidental change to the accepted Step 3 comparator inputs/rules.
    baseline = metrics[(metrics["case_type"] == "overall") & (metrics["method"] == METHODS[0])].iloc[0]
    accepted_step3_totals = {
        "requested_sessions": 125_109,
        "scheduled_sessions": 84_845,
        "unplaced_sessions": 40_264,
        "preference_penalties": 76_364,
        "hard_violations": 0,
    }
    observed_step3_totals = {
        "requested_sessions": int(baseline["requested_sessions"]),
        "scheduled_sessions": int(baseline["scheduled_sessions"]),
        "unplaced_sessions": int(baseline["unplaced_sessions"]),
        "preference_penalties": int(baseline["preference_penalties"]),
        "hard_violations": int(baseline["hard_violations"]),
    }
    if observed_step3_totals != accepted_step3_totals:
        raise AssertionError(
            "First-fit no longer matches accepted Step 3 totals. Do not compare until "
            f"the scenario data, room inventory and constraints are reconciled. Found {observed_step3_totals}."
        )

    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    metrics_path = REPORT_DIR / "step4_baseline_metrics.csv"
    comparison_path = REPORT_DIR / "step4_comparison.csv"
    paired_path = REPORT_DIR / "step4_paired_scenario_results.csv"
    metrics.to_csv(metrics_path, index=False)
    comparison.to_csv(comparison_path, index=False)
    paired.to_csv(paired_path, index=False)
    chart_path = _write_chart(metrics)
    _write_report(metrics, comparison, paired, chart_path)

    overall = metrics[metrics["case_type"] == "overall"]
    print("\nTIME-TABLE OPTIMIZER STEP 4 COMPARISON COMPLETED")
    print("=" * 64)
    print(f"Source scenarios available: {source['scenario_id'].nunique():,}")
    print(f"Scenarios evaluated by both methods: {paired['scenario_id'].nunique():,}")
    print(f"Methods: {', '.join(METHODS)}")
    print(f"GA settings per scenario: population={POPULATION_SIZE}, generations={GENERATIONS}")
    print("Step 3 first-fit totals verified against the accepted benchmark.")
    print("\nOVERALL MEASUREMENTS")
    print(overall.to_string(index=False))
    print("\nGA minus first-fit differences")
    print(comparison[comparison["case_type"] == "overall"].to_string(index=False))
    print(f"\nMetrics: {metrics_path.relative_to(PROJECT_ROOT)}")
    print(f"Comparison: {comparison_path.relative_to(PROJECT_ROOT)}")
    print(f"Paired results: {paired_path.relative_to(PROJECT_ROOT)}")
    print(f"Chart: {chart_path.relative_to(PROJECT_ROOT)}")
    print("Report updated: docs/STEP-4.md")
    print("Both hard-violation totals are zero; compare unplaced sessions and soft penalties too.")
    checkpoint_csv.unlink(missing_ok=True)
    checkpoint_meta_path.unlink(missing_ok=True)
    try:
        checkpoint_meta_path.parent.rmdir()
    except OSError:
        pass
    print("Temporary progress checkpoint cleared.")
    return metrics, comparison, paired


if __name__ == "__main__":
    main()

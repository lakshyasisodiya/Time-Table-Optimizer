"""Time-Table Optimizer Product V1 web interface.

Launch from the repository root with:
    python -m streamlit run app.py
"""
from __future__ import annotations

import pandas as pd
import streamlit as st

from src.product_scheduler import INPUT_COLUMNS, SAMPLE_INPUT, ROOMS, run_product_schedule

st.set_page_config(page_title="Time-Table Optimizer | Product V1", page_icon="📅", layout="wide")
st.title("Time-Table Optimizer")
st.subheader("Product V1 — Genetic Algorithm timetable builder")
st.write(
    "Enter five courses and their scheduling requirements. The app validates the input, "
    "runs the project's Step 4 Genetic Algorithm, and shows scheduled and unplaced sessions."
)
st.info(
    "This first version handles one five-course scenario per run, matching the Step 2 data design. "
    "It uses the same fixed rooms and ten time slots used in Steps 3 and 4."
)

with st.expander("Room and slot assumptions", expanded=False):
    st.dataframe(pd.DataFrame(ROOMS), hide_index=True, use_container_width=True)
    st.write("Available start slots: S1 to S10. A two-slot session occupies its start slot and the next slot.")
    st.write("Hard constraints: no room, faculty, or cohort overlap. Soft preference: the requested slot is preferred.")

st.sidebar.header("Genetic Algorithm settings")
population_size = st.sidebar.slider("Population size", min_value=4, max_value=16, value=8, step=2)
generations = st.sidebar.slider("Generations", min_value=1, max_value=20, value=5, step=1)
seed = st.sidebar.number_input("Random seed", min_value=0, max_value=999999, value=42, step=1)
st.sidebar.caption("Defaults match the Step 4 GA comparison settings.")

st.header("1. Enter course requirements")
st.caption(
    "Use each course ID C01–C05 once. Room capacity is the required student capacity, "
    "not a room number. The preferred slot is a soft preference, not a hard restriction."
)

uploaded = st.file_uploader("Optional: load a course-input CSV", type=["csv"])
if uploaded is not None:
    try:
        starting_input = pd.read_csv(uploaded)
        missing = [column for column in INPUT_COLUMNS if column not in starting_input.columns]
        if missing:
            st.error("Uploaded CSV is missing columns: " + ", ".join(missing))
            starting_input = SAMPLE_INPUT.copy()
        else:
            starting_input = starting_input[INPUT_COLUMNS].copy()
    except Exception as error:
        st.error(f"Could not read the CSV: {error}")
        starting_input = SAMPLE_INPUT.copy()
else:
    starting_input = SAMPLE_INPUT.copy()

with st.form("timetable_input_form"):
    edited_input = st.data_editor(
        starting_input,
        hide_index=True,
        num_rows="fixed",
        use_container_width=True,
        column_config={
            "course_id": st.column_config.SelectboxColumn("Course ID", options=[f"C0{i}" for i in range(1, 6)], disabled=True),
            "cohort_id": st.column_config.SelectboxColumn("Cohort", options=["G1", "G2"]),
            "faculty_id": st.column_config.SelectboxColumn("Faculty", options=["F1", "F2", "F3"]),
            "weekly_sessions": st.column_config.NumberColumn("Sessions per week", min_value=1, max_value=4, step=1, format="%d"),
            "duration_slots": st.column_config.NumberColumn("Duration (slots)", min_value=1, max_value=2, step=1, format="%d"),
            "required_room_type": st.column_config.SelectboxColumn("Required room", options=["classroom", "lab"]),
            "room_capacity": st.column_config.NumberColumn("Required capacity", min_value=1, max_value=60, step=1, format="%d"),
            "slot_id": st.column_config.SelectboxColumn("Preferred slot", options=[f"S{i}" for i in range(1, 11)]),
        },
    )
    submitted = st.form_submit_button("Generate timetable", type="primary", use_container_width=True)

if submitted:
    try:
        schedule, summary = run_product_schedule(
            edited_input,
            seed=int(seed),
            population_size=int(population_size),
            generations=int(generations),
        )
        st.session_state["step5_schedule"] = schedule
        st.session_state["step5_summary"] = summary
        st.session_state["step5_input"] = edited_input.copy()
    except (ValueError, RuntimeError) as error:
        st.error(str(error))
        st.session_state.pop("step5_schedule", None)
        st.session_state.pop("step5_summary", None)

if "step5_schedule" in st.session_state:
    schedule = st.session_state["step5_schedule"]
    summary = st.session_state["step5_summary"]
    st.header("2. Generated timetable")
    metric_cols = st.columns(4)
    metric_cols[0].metric("Sessions scheduled", f"{summary['scheduled_sessions']} / {summary['requested_sessions']}")
    metric_cols[1].metric("Unplaced sessions", int(summary["unplaced_sessions"]))
    metric_cols[2].metric("Hard violations", int(summary["hard_violations"]))
    metric_cols[3].metric("Soft penalties", int(summary["soft_preference_penalties"]))

    if summary["hard_violations"] == 0:
        st.success("The generated schedule passed the hard-conflict audit.")
    if summary["unplaced_sessions"]:
        st.warning(
            "Some sessions could not be placed under the current inputs and fixed room/slot assumptions. "
            "This does not prove they are mathematically impossible; a different search result or constraints may change placement."
        )
    else:
        st.success("All requested sessions were placed.")

    display_columns = [
        "course_id", "session_number", "cohort_id", "faculty_id", "room_id",
        "start_slot", "occupied_slots", "preferred_slot", "preference_penalty", "status", "unplaced_reason",
    ]
    st.dataframe(schedule[display_columns], hide_index=True, use_container_width=True)

    csv_bytes = schedule.to_csv(index=False).encode("utf-8")
    summary_bytes = pd.DataFrame([{
        key: value for key, value in summary.items() if key != "room_inventory"
    }]).to_csv(index=False).encode("utf-8")
    download_cols = st.columns(2)
    download_cols[0].download_button(
        "Download timetable CSV", data=csv_bytes,
        file_name="step5_timetable_output.csv", mime="text/csv", use_container_width=True,
    )
    download_cols[1].download_button(
        "Download summary CSV", data=summary_bytes,
        file_name="step5_timetable_summary.csv", mime="text/csv", use_container_width=True,
    )

    st.header("3. What the results mean")
    st.write(f"**Session coverage:** {summary['coverage_pct']:.2f}% of requested sessions were placed.")
    st.write(
        f"**Soft preference penalties:** {summary['soft_preference_penalties']} scheduled sessions "
        "started outside their preferred slot. These are preferences, not hard clashes."
    )
    st.caption(
        "This is an educational prototype using simulated inputs and a fixed example room inventory. "
        "It is not connected to a live university timetable or room-management system. Review and approve "
        "any timetable before real use."
    )
else:
    st.caption("No timetable has been generated in this session yet.")

st.divider()
st.caption("Time-Table Optimizer Product V1 | Uses the Step 4 Genetic Algorithm; no model training occurs in this interface.")

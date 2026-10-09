"""Small automated checks for the Step 3 first-fit baseline.

Run from the repository root:
    python -m unittest discover -s tests -v
"""
import unittest
import pandas as pd
from src.run_baseline import schedule_one_scenario


def make_scenario(rows):
    return pd.DataFrame(rows)


def course(course_id, cohort, faculty, room_type, sessions=1, duration=1, preferred="S10"):
    capacity = 30 if room_type == "lab" else 60
    return {
        "scenario_id": "TEST-001",
        "case_type": "normal",
        "course_id": course_id,
        "cohort_id": cohort,
        "faculty_id": faculty,
        "weekly_sessions": sessions,
        "duration_slots": duration,
        "required_room_type": room_type,
        "room_capacity": capacity,
        "room_type": room_type,
        "slot_id": preferred,
    }


class BaselineSchedulerTests(unittest.TestCase):
    def test_basic_fixture_is_scheduled_without_hard_clashes(self):
        data = make_scenario([
            course("C01", "G1", "F1", "classroom"),
            course("C02", "G1", "F2", "lab"),
            course("C03", "G2", "F3", "classroom"),
            course("C04", "G2", "F1", "classroom"),
            course("C05", "G1", "F3", "classroom"),
        ])
        schedule, summary = schedule_one_scenario(data)
        schedule = pd.DataFrame(schedule)
        self.assertEqual(summary["requested_sessions"], 5)
        self.assertEqual(summary["scheduled_sessions"], 5)
        self.assertEqual(summary["unplaced_sessions"], 0)
        self.assertTrue((schedule["status"] == "scheduled").all())

    def test_soft_preference_penalty_is_not_a_hard_violation(self):
        data = make_scenario([
            course("C01", "G1", "F1", "classroom", preferred="S10"),
            course("C02", "G2", "F2", "classroom"),
            course("C03", "G1", "F3", "lab"),
            course("C04", "G2", "F1", "lab"),
            course("C05", "G1", "F2", "classroom"),
        ])
        schedule, summary = schedule_one_scenario(data)
        schedule = pd.DataFrame(schedule)
        c01 = schedule[(schedule.course_id == "C01") & (schedule.session_number == 1)].iloc[0]
        self.assertEqual(c01["status"], "scheduled")
        self.assertEqual(c01["start_slot"], "S1")
        self.assertEqual(int(c01["preference_penalty"]), 1)
        self.assertEqual(summary["unplaced_sessions"], 0)

    def test_high_demand_can_leave_sessions_unplaced_without_crashing(self):
        data = make_scenario([
            course("C01", "G1", "F1", "classroom", sessions=4, duration=2),
            course("C02", "G1", "F2", "classroom", sessions=4, duration=2),
            course("C03", "G1", "F3", "classroom", sessions=4, duration=2),
            course("C04", "G1", "F1", "classroom", sessions=4, duration=2),
            course("C05", "G1", "F2", "classroom", sessions=4, duration=2),
        ])
        schedule, summary = schedule_one_scenario(data)
        schedule = pd.DataFrame(schedule)
        self.assertGreater(summary["unplaced_sessions"], 0)
        self.assertTrue((schedule["status"].isin(["scheduled", "unplaced"])).all())


if __name__ == "__main__":
    unittest.main()

"""Quick correctness tests for the Step 4 Genetic Algorithm scheduler."""
import unittest
import pandas as pd
from src.run_genetic_algorithm import schedule_one_scenario
from src.run_baseline import audit_schedule


def course(course_id, cohort, faculty, room_type, sessions=1, duration=1, preferred="S10"):
    capacity = 30 if room_type == "lab" else 60
    return {
        "scenario_id": "TEST-GA-001", "case_type": "normal", "course_id": course_id,
        "cohort_id": cohort, "faculty_id": faculty, "weekly_sessions": sessions,
        "duration_slots": duration, "required_room_type": room_type,
        "room_capacity": capacity, "room_type": room_type, "slot_id": preferred,
    }


class GeneticSchedulerTests(unittest.TestCase):
    def test_ga_schedules_simple_fixture_without_hard_clashes(self):
        data = pd.DataFrame([
            course("C01", "G1", "F1", "classroom", preferred="S3"),
            course("C02", "G1", "F2", "lab", preferred="S4"),
            course("C03", "G2", "F3", "classroom", preferred="S5"),
            course("C04", "G2", "F1", "classroom", preferred="S6"),
            course("C05", "G1", "F3", "classroom", preferred="S7"),
        ])
        records, summary = schedule_one_scenario(data, seed=7, population_size=8, generations=3)
        schedule = pd.DataFrame(records)
        self.assertEqual(summary["requested_sessions"], 5)
        self.assertEqual(summary["scheduled_sessions"], 5)
        self.assertEqual(summary["unplaced_sessions"], 0)
        self.assertEqual(audit_schedule(schedule), 0)

    def test_ga_is_reproducible_with_same_seed(self):
        data = pd.DataFrame([
            course("C01", "G1", "F1", "classroom", sessions=2, preferred="S4"),
            course("C02", "G2", "F2", "classroom", sessions=2, preferred="S4"),
            course("C03", "G1", "F3", "lab", sessions=2, preferred="S5"),
            course("C04", "G2", "F1", "lab", preferred="S7"),
            course("C05", "G1", "F2", "classroom", preferred="S8"),
        ])
        first_records, first_summary = schedule_one_scenario(data, seed=22, population_size=8, generations=3)
        second_records, second_summary = schedule_one_scenario(data, seed=22, population_size=8, generations=3)
        self.assertEqual(first_records, second_records)
        self.assertEqual(first_summary["unplaced_sessions"], second_summary["unplaced_sessions"])
        self.assertEqual(first_summary["preference_penalties"], second_summary["preference_penalties"])

    def test_high_demand_is_reported_without_hard_clashes(self):
        data = pd.DataFrame([
            course("C01", "G1", "F1", "classroom", sessions=4, duration=2),
            course("C02", "G1", "F2", "classroom", sessions=4, duration=2),
            course("C03", "G1", "F3", "classroom", sessions=4, duration=2),
            course("C04", "G1", "F1", "classroom", sessions=4, duration=2),
            course("C05", "G1", "F2", "classroom", sessions=4, duration=2),
        ])
        records, summary = schedule_one_scenario(data, seed=5, population_size=8, generations=3)
        self.assertGreater(summary["unplaced_sessions"], 0)
        self.assertEqual(audit_schedule(pd.DataFrame(records)), 0)


if __name__ == "__main__":
    unittest.main()

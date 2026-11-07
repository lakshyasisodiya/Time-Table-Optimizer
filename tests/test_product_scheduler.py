"""Product V1 validation and GA connection tests."""
from __future__ import annotations

import unittest

import pandas as pd

from src.product_scheduler import SAMPLE_INPUT, run_product_schedule, validate_and_prepare_input


class ProductSchedulerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.sample = SAMPLE_INPUT.copy()

    def test_normal_input_runs_and_has_no_hard_conflicts(self) -> None:
        schedule, summary = run_product_schedule(self.sample)
        self.assertEqual(len(self.sample), 5)
        self.assertEqual(summary["hard_violations"], 0)
        self.assertEqual(summary["requested_sessions"], int(self.sample["weekly_sessions"].sum()))
        self.assertEqual(len(schedule), summary["requested_sessions"])

    def test_boundary_session_values_are_accepted(self) -> None:
        boundary = self.sample.copy()
        boundary.loc[0, "weekly_sessions"] = 1
        boundary.loc[1, "weekly_sessions"] = 4
        boundary.loc[2, "duration_slots"] = 2
        prepared = validate_and_prepare_input(boundary)
        self.assertEqual(int(prepared.loc[0, "weekly_sessions"]), 1)
        self.assertEqual(int(prepared.loc[1, "weekly_sessions"]), 4)

    def test_missing_faculty_is_rejected(self) -> None:
        invalid = self.sample.copy()
        invalid.loc[0, "faculty_id"] = ""
        with self.assertRaisesRegex(ValueError, "faculty_id"):
            validate_and_prepare_input(invalid)

    def test_out_of_range_weekly_sessions_are_rejected(self) -> None:
        invalid = self.sample.copy()
        invalid.loc[0, "weekly_sessions"] = 5
        with self.assertRaisesRegex(ValueError, "weekly_sessions"):
            validate_and_prepare_input(invalid)

    def test_room_capacity_above_inventory_is_rejected(self) -> None:
        invalid = self.sample.copy()
        invalid.loc[0, "required_room_type"] = "lab"
        invalid.loc[0, "room_capacity"] = 31
        with self.assertRaisesRegex(ValueError, "maximum is 30"):
            validate_and_prepare_input(invalid)

    def test_same_input_and_seed_give_same_result(self) -> None:
        first_schedule, first_summary = run_product_schedule(self.sample, seed=7)
        second_schedule, second_summary = run_product_schedule(self.sample, seed=7)
        pd.testing.assert_frame_equal(first_schedule, second_schedule)
        self.assertEqual(first_summary["scheduled_sessions"], second_summary["scheduled_sessions"])
        self.assertEqual(first_summary["soft_preference_penalties"], second_summary["soft_preference_penalties"])

    def test_wrong_number_of_courses_is_rejected(self) -> None:
        invalid = self.sample.iloc[:4].copy()
        with self.assertRaisesRegex(ValueError, "exactly five"):
            validate_and_prepare_input(invalid)


if __name__ == "__main__":
    unittest.main()

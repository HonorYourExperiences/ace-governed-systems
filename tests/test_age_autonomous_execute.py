import unittest

from scripts.age_autonomous_execute import TERMINAL_STATUSES, candidate_rows, find_handler


class AgeAutonomousExecuteTests(unittest.TestCase):
    def test_terminal_statuses_protect_human_closed_boundary(self):
        self.assertIn("Verified", TERMINAL_STATUSES)
        self.assertIn("Closed", TERMINAL_STATUSES)
        self.assertIn("Superseded", TERMINAL_STATUSES)

    def test_registered_handler_matches_known_high_ap_failure(self):
        row = {
            "failure_mode": "Regex-based parser fragile to format variations",
        }

        handler = find_handler(row)

        self.assertIsNotNone(handler)
        self.assertEqual(handler.name, "dashboard-schema-validation")

    def test_current_repo_has_no_eligible_high_ap_rows(self):
        self.assertEqual(candidate_rows(100), [])


if __name__ == "__main__":
    unittest.main()

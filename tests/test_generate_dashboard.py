import unittest
from datetime import datetime

from scripts.generate_dashboard import (
    build_dashboard_data,
    parse_audit_log,
    validate_dashboard_data,
)


class GenerateDashboardTests(unittest.TestCase):
    def test_parse_audit_log_extracts_structured_entries(self):
        content = """# Audit Log

## Audit: Example 1
**Allowed:** false
**Reason:** Operational changes must come through verified SAGA

## Audit: Example 2
**Allowed:** true
**Reason:** Clear
"""
        entries = parse_audit_log(content)

        self.assertEqual(len(entries), 2)
        self.assertFalse(entries[0]["allowed"])
        self.assertEqual(entries[0]["reason"], "Operational changes must come through verified SAGA")
        self.assertTrue(entries[1]["allowed"])

    def test_build_dashboard_data_has_valid_schema(self):
        entries = [
            {"title": "## Audit: One", "allowed": False, "reason": "Blocked"},
            {"title": "## Audit: Two", "allowed": True, "reason": "Clear"},
        ]

        data = build_dashboard_data(entries, now=datetime(2026, 6, 28, 12, 0, 0))

        self.assertEqual(data["total_audits"], 2)
        self.assertEqual(data["refusals"], 1)
        self.assertEqual(data["approvals"], 1)
        self.assertEqual(data["refusal_rate"], 50.0)
        validate_dashboard_data(data)

    def test_validate_dashboard_data_rejects_inconsistent_counts(self):
        data = {
            "last_updated": "2026-06-28T12:00:00Z",
            "total_audits": 1,
            "refusals": 1,
            "approvals": 1,
            "refusal_rate": 100.0,
            "top_reasons": [],
        }

        with self.assertRaises(ValueError):
            validate_dashboard_data(data)


if __name__ == "__main__":
    unittest.main()

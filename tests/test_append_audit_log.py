import argparse
import tempfile
import unittest
from pathlib import Path

from scripts import append_audit_log


class AppendAuditLogTests(unittest.TestCase):
    def test_normal_event_uses_dashboard_compatible_fields(self):
        args = argparse.Namespace(
            title="Blocked policy change",
            issue="42",
            action="update_policy",
            allowed="false",
            reason="Needs verified SAGA",
            source="runtime-monitor",
        )

        lines = append_audit_log.audit_event_lines(args)

        self.assertEqual(lines[0], "## Audit: Blocked policy change")
        self.assertIn("- **Allowed:** false", lines)
        self.assertIn("- **Issue:** #42", lines)

    def test_processor_error_is_a_refusal_audit_entry(self):
        args = argparse.Namespace(issue="42", stage="pfmea_append", error="bad\nthing")

        lines = append_audit_log.processor_error_lines(args)

        self.assertTrue(lines[0].startswith("## Audit: Processor Error"))
        self.assertIn("- **Action:** audit_processor_error", lines)
        self.assertIn("- **Allowed:** false", lines)
        self.assertIn("- **Stage:** pfmea_append", lines)
        self.assertIn("- **Error:** bad thing", lines)

    def test_append_block_writes_trailing_blank_line(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "AUDIT-LOG.md"
            append_audit_log.append_block(["## Audit: Test", "- **Allowed:** true"], path)
            self.assertEqual(path.read_text(encoding="utf-8"), "## Audit: Test\n- **Allowed:** true\n\n")


if __name__ == "__main__":
    unittest.main()

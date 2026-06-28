import tempfile
import unittest
from pathlib import Path

from scripts import validate_runtime_monitor_entrypoints as validator


class RuntimeMonitorEntrypointTests(unittest.TestCase):
    def test_state_mutating_workflow_requires_gate_marker(self):
        with tempfile.TemporaryDirectory() as tmp:
            workflow = Path(tmp) / "unguarded.yml"
            workflow.write_text("permissions:\n  contents: write\nsteps:\n  - run: git push\n", encoding="utf-8")

            item = validator.inspect_workflow(workflow)

            self.assertTrue(item["mutates_state"])
            self.assertFalse(item["covered"])
            self.assertEqual(len(validator.failures([item])), 1)

    def test_state_mutating_workflow_with_preflight_is_covered(self):
        with tempfile.TemporaryDirectory() as tmp:
            workflow = Path(tmp) / "guarded.yml"
            workflow.write_text(
                "permissions:\n  contents: write\nsteps:\n  - run: python3 scripts/age_engineer.py preflight\n  - run: git push\n",
                encoding="utf-8",
            )

            item = validator.inspect_workflow(workflow)

            self.assertTrue(item["mutates_state"])
            self.assertTrue(item["covered"])
            self.assertEqual(validator.failures([item]), [])

    def test_current_repository_workflows_are_covered(self):
        missing = validator.failures(validator.inventory())
        self.assertEqual(missing, [])


if __name__ == "__main__":
    unittest.main()

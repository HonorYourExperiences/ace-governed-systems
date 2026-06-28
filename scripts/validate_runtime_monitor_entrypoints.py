#!/usr/bin/env python3
"""Inventory repository-mutating workflow entrypoints and verify governance gates."""

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
WORKFLOW_DIR = REPO_ROOT / ".github" / "workflows"

STATE_MUTATION_MARKERS = [
    "contents: write",
    "issues: write",
    "pull-requests: write",
    "actions: write",
    "git push",
    "git commit",
    "issues.create",
    "pulls.create",
    "add-and-commit",
]

GOVERNANCE_GATE_MARKERS = [
    "runtime monitor",
    "verified label gate",
    "needs-verification",
    "verified saga",
    "age_engineer.py preflight",
    "validate_governance_change.py",
    "validate_runtime_monitor_entrypoints.py",
]


def workflow_files(workflow_dir: Path = WORKFLOW_DIR) -> list[Path]:
    if not workflow_dir.exists():
        return []
    return sorted([*workflow_dir.glob("*.yml"), *workflow_dir.glob("*.yaml")])


def inspect_workflow(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    lower = text.lower()
    mutation_markers = [marker for marker in STATE_MUTATION_MARKERS if marker in lower]
    gate_markers = [marker for marker in GOVERNANCE_GATE_MARKERS if marker in lower]
    return {
        "path": path.as_posix(),
        "mutates_state": bool(mutation_markers),
        "mutation_markers": mutation_markers,
        "governance_gate_markers": gate_markers,
        "covered": bool(gate_markers) or not mutation_markers,
    }


def inventory(workflow_dir: Path = WORKFLOW_DIR) -> list[dict]:
    return [inspect_workflow(path) for path in workflow_files(workflow_dir)]


def failures(items: list[dict]) -> list[str]:
    return [
        f"{item['path']}: state-mutating workflow has no runtime monitor / verified-SAGA gate marker"
        for item in items
        if item["mutates_state"] and not item["covered"]
    ]


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate runtime monitor coverage for workflow entrypoints")
    parser.add_argument("--json", action="store_true", help="Print full inventory as JSON")
    args = parser.parse_args()

    items = inventory()
    if args.json:
        print(json.dumps(items, indent=2))

    missing = failures(items)
    if missing:
        print("Runtime monitor entrypoint validation failed:")
        for failure in missing:
            print(f"- {failure}")
        return 1

    covered_count = len([item for item in items if item["mutates_state"]])
    print(f"Runtime monitor entrypoint validation PASS ({covered_count} state-mutating workflows covered)")
    return 0


if __name__ == "__main__":
    sys.exit(main())

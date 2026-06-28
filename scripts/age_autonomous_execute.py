#!/usr/bin/env python3
"""
AGE autonomous executor for high-AP FMEA rows.

This is intentionally not a generic code-writing bot. It selects the highest
non-verified row above the configured High AP threshold and executes a registered
deterministic handler. If no handler exists, it refuses to mutate the repo.
"""

import argparse
import json
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

try:
    from age_engineer import SOP_PATH, get_open_rows, load_config
except ImportError:
    from scripts.age_engineer import SOP_PATH, get_open_rows, load_config


REPO_ROOT = Path(__file__).resolve().parent.parent
TERMINAL_STATUSES = {"Verified", "Closed", "Superseded"}


@dataclass(frozen=True)
class Handler:
    name: str
    evidence: str
    note: str
    match: Callable[[dict], bool]
    validations: tuple[tuple[str, ...], ...]


def run_command(command: tuple[str, ...]) -> None:
    subprocess.run(command, cwd=REPO_ROOT, check=True)


def row_arg(row: dict, status: str, note: str) -> tuple[str, ...]:
    return (
        sys.executable,
        "scripts/age_engineer.py",
        "update-status",
        "--table",
        row["table"],
        "--step",
        row["step_or_element"],
        "--failure",
        row["failure_mode"],
        "--status",
        status,
        "--note",
        note,
    )


def verify_arg(row: dict, evidence: str) -> tuple[str, ...]:
    return (
        sys.executable,
        "scripts/age_engineer.py",
        "verify-closure",
        "--table",
        row["table"],
        "--step",
        row["step_or_element"],
        "--failure",
        row["failure_mode"],
        "--evidence",
        evidence,
    )


def contains_failure(fragment: str) -> Callable[[dict], bool]:
    needle = fragment.lower()
    return lambda row: needle in row["failure_mode"].lower()


HANDLERS = (
    Handler(
        name="proposal-structure-governance-gate",
        evidence="file:scripts/validate_governance_change.py",
        note="autonomous handler verified proposal structure gate via validate_governance_change.py, age-pr-analysis.yml, and audit-processor proposal template.",
        match=contains_failure("Current State → Target State → Delta"),
        validations=(
            (
                sys.executable,
                "scripts/validate_governance_change.py",
                ".github/workflows/age-pr-analysis.yml",
                ".github/workflows/audit-processor.yml",
                "proposals/prop-AGE-2026-06-27-evidence-first-framing.md",
            ),
        ),
    ),
    Handler(
        name="runtime-monitor-workflow-gate",
        evidence="file:RUNTIME-MONITOR-WIRING.md",
        note="autonomous handler verified state-mutating workflow changes are gated for runtime monitor or verified-SAGA controls.",
        match=contains_failure("Monitor not wired to all policy/content modification points"),
        validations=(
            (
                sys.executable,
                "scripts/validate_governance_change.py",
                ".github/workflows/age-pr-analysis.yml",
                ".github/workflows/audit-processor.yml",
                ".github/workflows/generate-dashboard.yml",
            ),
        ),
    ),
    Handler(
        name="aspiration-theater-content-gate",
        evidence="file:scripts/scan_content_antipatterns.py",
        note="autonomous handler verified evidence-first/content anti-pattern scan is clean.",
        match=contains_failure("Aspiration theater framing"),
        validations=((sys.executable, "scripts/scan_content_antipatterns.py", "--path", "cape-able-heroes"),),
    ),
    Handler(
        name="verification-label-gate",
        evidence="file:.github/workflows/age-pr-analysis.yml",
        note="autonomous handler verified policy/proposal changes are blocked unless linked needs-verification issues are verified.",
        match=contains_failure("No automated gate preventing un-verified proposals"),
        validations=((sys.executable, "scripts/validate_governance_change.py", ".github/workflows/age-pr-analysis.yml"),),
    ),
    Handler(
        name="dashboard-schema-validation",
        evidence="file:tests/test_generate_dashboard.py",
        note="autonomous handler verified dashboard parser schema validation and unit tests pass.",
        match=contains_failure("Regex-based parser fragile"),
        validations=((sys.executable, "-m", "unittest", "tests.test_generate_dashboard"),),
    ),
    Handler(
        name="proposal-bypass-governance-gate",
        evidence="file:scripts/validate_governance_change.py",
        note="autonomous handler verified proposal/workflow bypass gate is active.",
        match=contains_failure("Proposal bypasses verification pipeline"),
        validations=((sys.executable, "scripts/validate_governance_change.py", ".github/workflows/age-pr-analysis.yml"),),
    ),
    Handler(
        name="way-through-content-gate",
        evidence="file:scripts/scan_content_antipatterns.py",
        note="autonomous handler verified Way Through content scan is clean.",
        match=contains_failure("Rescue modeling in hero / parent copy"),
        validations=((sys.executable, "scripts/scan_content_antipatterns.py", "--path", "cape-able-heroes"),),
    ),
)


def candidate_rows(min_rpn: int) -> list[dict]:
    return [
        row
        for row in get_open_rows(SOP_PATH)
        if row["rpn"] >= min_rpn and row["status"] not in TERMINAL_STATUSES
    ]


def find_handler(row: dict) -> Handler | None:
    for handler in HANDLERS:
        if handler.match(row):
            return handler
    return None


def execute_row(row: dict, handler: Handler, dry_run: bool) -> dict:
    result = {
        "row": {
            "table": row["table"],
            "rpn": row["rpn"],
            "step_or_element": row["step_or_element"],
            "failure_mode": row["failure_mode"],
            "status_before": row["status"],
        },
        "handler": handler.name,
        "evidence": handler.evidence,
        "dry_run": dry_run,
        "actions": [],
    }

    if dry_run:
        result["actions"].append("would run handler validations")
        result["actions"].append("would transition row to Solution Designed if needed")
        result["actions"].append("would run verify-closure")
        result["actions"].append("would transition row to Verified")
        return result

    for command in handler.validations:
        run_command(command)
        result["actions"].append("validation: " + " ".join(command))

    if row["status"] != "Solution Designed":
        run_command(row_arg(row, "Solution Designed", handler.note))
        result["actions"].append("status: Solution Designed")

    run_command(verify_arg(row, handler.evidence))
    result["actions"].append("verify-closure PASS")

    run_command(row_arg(row, "Verified", f"verify-closure PASS; {handler.note}"))
    result["actions"].append("status: Verified")

    run_command((sys.executable, "scripts/age_engineer.py", "report"))
    result["actions"].append("report regenerated")

    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Execute the highest supported High AP FMEA row")
    parser.add_argument("--dry-run", action="store_true", help="Plan without mutating files")
    parser.add_argument("--output", help="Write JSON execution result to this path")
    args = parser.parse_args()

    config = load_config()
    min_rpn = config.get("risk_thresholds", {}).get("high_rpn_floor", 100)

    subprocess.run((sys.executable, "scripts/age_engineer.py", "preflight"), cwd=REPO_ROOT, check=True)

    rows = candidate_rows(min_rpn)
    if not rows:
        result = {
            "status": "no_eligible_rows",
            "message": f"No non-verified FMEA rows found with RPN >= {min_rpn}.",
        }
        print(json.dumps(result, indent=2))
        if args.output:
            Path(args.output).write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
        return 0

    row = rows[0]
    handler = find_handler(row)
    if handler is None:
        result = {
            "status": "unsupported_row",
            "message": "No deterministic autonomous handler is registered for the highest AP row.",
            "row": {
                "table": row["table"],
                "rpn": row["rpn"],
                "step_or_element": row["step_or_element"],
                "failure_mode": row["failure_mode"],
                "status": row["status"],
                "recommended_action": row["action"],
            },
        }
        print(json.dumps(result, indent=2))
        if args.output:
            Path(args.output).write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
        return 2

    result = execute_row(row, handler, args.dry_run)
    result["status"] = "planned" if args.dry_run else "executed"
    print(json.dumps(result, indent=2))
    if args.output:
        Path(args.output).write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())

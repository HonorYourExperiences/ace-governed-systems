#!/usr/bin/env python3
"""
AGE Engineer — FMEA Lifecycle Management Engine

Manages the complete lifecycle of FMEA rows in governed_systems_SOP_PFMEA_DFMEA.md:
  scan          List all open rows sorted by RPN descending
  queue         Show prioritized work queue (Critical/High/Medium)
  update-status Transition a row's lifecycle state with an evidence note
  verify-closure Validate a row is ready for Verified status
  report        Regenerate AGE-WORKBENCH.md
  lint-proposal  Validate a proposal file conforms to 7-section SAGA format

Exit codes: 0=success, 1=error, 2=no rows found / empty queue
"""

import argparse
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

try:
    from validate_governance_change import proposal_failures
except ImportError:
    proposal_failures = None

SOP_PATH = Path(__file__).parent.parent / "governed_systems_SOP_PFMEA_DFMEA.md"
WORKBENCH_PATH = Path(__file__).parent.parent / "AGE-WORKBENCH.md"
CONFIG_PATH = Path(__file__).parent.parent / "fmea-agent.config.json"
AUDIT_LOG_PATH = Path(__file__).parent.parent / "AUDIT-LOG.md"

REQUIRED_SOP_SECTIONS = [
    "## Context",
    "## Prerequisites",
    "## Steps",
    "## Verification",
    "## Turnback Criteria",
]

REQUIRED_PROPOSAL_SECTIONS = [
    "## 1. Current State Assessment",
    "## 2. Target State Definition",
    "## 3. Delta Identification",
    "## 4. Gap-Closing Proposals",
    "## 5. Verification Checklist",
    "## 6. Success Metrics",
    "## 7. Phase Completion Triggers",
]


def load_config():
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH) as f:
            return json.load(f)
    return {"risk_thresholds": {"critical_rpn_floor": 150, "high_rpn_floor": 100}}


def split_table_cells(line: str, expected_cols: int = 11) -> list[str]:
    """
    Split a markdown table row into cells while preserving delimiter characters in the final cell.

    Args:
        line: Markdown table row string, e.g. "| a | b | ... | status |".
        expected_cols: Number of cells expected after splitting.

    We intentionally use maxsplit=(expected_cols - 1) so content in the status cell can contain
    additional `|` characters (for example in evidence comments) without shifting column indexes.
    The default expected column count is 11 because PFMEA/DFMEA tables in this repository use
    exactly 11 columns (through the Status field).
    Returns [] when the row is malformed or does not match the expected column count.
    """
    stripped = line.strip()
    if not (stripped.startswith("|") and stripped.endswith("|")):
        # Caller treats [] as "not a data row or malformed row" and skips it.
        return []
    # expected_cols - 1 splits yield expected_cols cells and preserve any extra pipes in the final cell.
    cells = [c.strip() for c in stripped[1:-1].split("|", expected_cols - 1)]
    # Return [] on malformed row so downstream callers safely skip it via len(cells) checks.
    return cells if len(cells) == expected_cols else []


def sanitize_status_note(note: str) -> str:
    """Sanitize evidence note text for safe embedding in a markdown table HTML comment."""
    escaped = note.replace("|", "/").replace("<", "[").replace(">", "]")
    normalized_hyphens = re.sub(r"-{2,}", "- -", escaped)
    return " ".join(normalized_hyphens.replace("\r", " ").replace("\n", " ").split())


def parse_fmea_rows(sop_path: Path) -> list[dict]:
    """
    Parse all PFMEA and DFMEA rows from the SOP file.
    Returns rows excluding header rows, sorted by RPN descending.
    Each row dict: table, step_or_element, failure_mode, effect, s, cause, o,
                   controls, d, rpn, action, status, raw_status, line_number
    """
    text = sop_path.read_text(encoding="utf-8")
    lines = text.splitlines()
    rows = []

    current_table = None
    for line_num, line in enumerate(lines):
        stripped = line.strip()

        if "## 2. Process Failure Mode" in stripped:
            current_table = "pfmea"
            continue
        elif "## 3. Design Failure Mode" in stripped:
            current_table = "dfmea"
            continue

        if current_table and stripped.startswith("|") and stripped.endswith("|"):
            cells = split_table_cells(stripped)

            if len(cells) < 11:
                continue

            # Skip header rows
            if cells[0] in ("Process Step", "Design Element", "---", ""):
                continue
            if cells[0].startswith("---"):
                continue

            rpn_raw = cells[8]
            # Strip HTML comments from RPN cell for numeric parsing
            rpn_clean = re.sub(r"<!--.*?-->", "", rpn_raw).strip()
            try:
                rpn = int(rpn_clean)
            except ValueError:
                continue

            # Skip rows where step is clearly a separator
            if cells[0].startswith("---") or cells[1].startswith("---"):
                continue

            raw_status = cells[10]
            # Extract clean status (before any HTML comment)
            clean_status = re.sub(r"<!--.*?-->", "", raw_status).strip()

            rows.append(
                {
                    "table": current_table,
                    "step_or_element": cells[0],
                    "failure_mode": cells[1],
                    "effect": cells[2],
                    "s": cells[3],
                    "cause": cells[4],
                    "o": cells[5],
                    "controls": cells[6],
                    "d": cells[7],
                    "rpn": rpn,
                    "action": cells[9],
                    "status": clean_status,
                    "raw_status": raw_status,
                    "line_number": line_num,
                }
            )

    rows.sort(key=lambda r: r["rpn"], reverse=True)
    return rows


def get_open_rows(sop_path: Path) -> list[dict]:
    all_rows = parse_fmea_rows(sop_path)
    return [r for r in all_rows if "Closed" not in r["status"] and "Superseded" not in r["status"]]


def priority_label(rpn: int, config: dict) -> str:
    thresholds = config.get("risk_thresholds", {})
    critical = thresholds.get("critical_rpn_floor", 150)
    high = thresholds.get("high_rpn_floor", 100)
    if rpn >= critical:
        return "[CRITICAL]"
    elif rpn >= high:
        return "[HIGH]    "
    else:
        return "[MONITOR] "


def cmd_scan(args):
    rows = get_open_rows(SOP_PATH)
    if not rows:
        print("No non-closed FMEA rows found.")
        return 2

    config = load_config()
    print(f"\n{'Priority':<12} {'Table':<6} {'RPN':<5} {'Status':<20} {'Step / Failure Mode'}")
    print("-" * 100)
    for r in rows:
        label = priority_label(r["rpn"], config)
        status_display = r["status"][:18]
        print(
            f"{label} {r['table'].upper():<6} {r['rpn']:<5} {status_display:<20} "
            f"{r['step_or_element'][:30]} / {r['failure_mode'][:35]}"
        )
    print(f"\nTotal non-closed rows: {len(rows)}")
    return 0


def cmd_queue(args):
    rows = get_open_rows(SOP_PATH)
    config = load_config()
    thresholds = config.get("risk_thresholds", {})
    critical_floor = thresholds.get("critical_rpn_floor", 150)
    high_floor = thresholds.get("high_rpn_floor", 100)

    critical = [r for r in rows if r["rpn"] >= critical_floor]
    high = [r for r in rows if high_floor <= r["rpn"] < critical_floor]
    medium = [r for r in rows if r["rpn"] < high_floor]

    queue = {"critical": critical, "high": high, "medium": medium}

    if args.output_json:
        print(json.dumps(queue, indent=2, default=str))
        return 0 if rows else 2

    def print_bucket(label, bucket):
        print(f"\n### {label} ({len(bucket)} rows)")
        if not bucket:
            print("  (none)")
            return
        for r in bucket:
            print(f"  RPN {r['rpn']:>3}  [{r['table'].upper()}]  {r['step_or_element']} / {r['failure_mode']}")
            print(f"         Status: {r['status']}")

    print_bucket(f"CRITICAL — RPN ≥ {critical_floor} (requires active work)", critical)
    print_bucket(f"HIGH — RPN {high_floor}–{critical_floor - 1} (SAGA trigger threshold)", high)
    print_bucket("MONITOR — RPN < 100", medium)
    print(f"\nTotal: {len(rows)} non-closed | {len(critical)} Critical | {len(high)} High | {len(medium)} Monitor")
    return 0 if rows else 2


def cmd_update_status(args):
    sop_path = SOP_PATH
    text = sop_path.read_text(encoding="utf-8")
    lines = text.splitlines()

    if args.status == "Closed":
        print("ERROR: 'Closed' is a human-only transition. The AGE cannot mark rows Closed.", file=sys.stderr)
        print("To close a row: human reviewer must confirm Verified state and manually update.", file=sys.stderr)
        return 1

    # Find the matching row
    found_line = None
    current_table = None
    for i, line in enumerate(lines):
        stripped = line.strip()
        if "## 2. Process Failure Mode" in stripped:
            current_table = "pfmea"
        elif "## 3. Design Failure Mode" in stripped:
            current_table = "dfmea"

        if current_table and current_table == args.table and stripped.startswith("|"):
            cells = split_table_cells(stripped)
            if len(cells) < 11:
                continue
            if cells[0] in ("Process Step", "Design Element"):
                continue
            if cells[0] == args.step and cells[1] == args.failure:
                found_line = i
                break

    if found_line is None:
        print(f"ERROR: Row not found in {args.table.upper()}: '{args.step}' / '{args.failure}'", file=sys.stderr)
        return 1

    # Reconstruct the line with updated status cell
    cells = split_table_cells(lines[found_line])
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    note_safe = sanitize_status_note(args.note)
    new_status = f"{args.status} <!-- AGE: {timestamp} | {note_safe} -->"
    cells[10] = new_status
    lines[found_line] = "| " + " | ".join(cells) + " |"

    sop_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Updated [{args.table.upper()}] '{args.step}' / '{args.failure}' → {args.status}")
    print(f"Evidence note: {args.note}")
    return 0


def cmd_verify_closure(args):
    rows = get_open_rows(SOP_PATH)

    matching = [
        r for r in rows
        if r["table"] == args.table
        and r["step_or_element"] == args.step
        and r["failure_mode"] == args.failure
    ]

    result = {"result": "FAIL", "notes": []}

    if not matching:
        # Also check all rows (might be Superseded)
        all_rows = parse_fmea_rows(SOP_PATH)
        matching = [
            r for r in all_rows
            if r["table"] == args.table
            and r["step_or_element"] == args.step
            and r["failure_mode"] == args.failure
        ]
        if matching:
            result["notes"].append(
                f"Row found but current status is '{matching[0]['status']}'. "
                "Expected 'Solution Designed' for verification."
            )
        else:
            result["notes"].append("Row not found in FMEA table. Verify table, step, and failure_mode arguments.")
        print(json.dumps(result, indent=2))
        return 1

    row = matching[0]

    # Check 1: status precondition
    if "Solution Designed" not in row["status"]:
        result["notes"].append(
            f"Row status is '{row['status']}'. "
            "Must be 'Solution Designed' before verification. "
            "Transition to Solution Designed first."
        )
    else:
        result["status_precondition_met"] = True

    # Check 2: evidence is non-trivial
    if not args.evidence or len(args.evidence.strip()) < 10:
        result["notes"].append(
            "Evidence string is too short or empty. "
            "Provide a specific artifact: commit hash, GitHub issue number, or file path."
        )
    else:
        result["evidence_valid"] = True

    # Check 3: evidence references something real (basic format check)
    evidence = args.evidence.strip()
    evidence_formats = ["commit:", "issue:#", "issue: #", "pr:#", "run:", "file:", "http"]
    if not any(evidence.lower().startswith(fmt) for fmt in evidence_formats):
        result["notes"].append(
            f"Evidence format not recognized: '{evidence}'. "
            "Expected format: 'commit:abc1234', 'issue:#42', 'file:path/to/file.md', or a URL."
        )
    else:
        result["evidence_format_valid"] = True

    # Note: RPN reduction cannot be validated from the original row alone.
    # The AGE must append a new row with updated S/O/D via pfmea_append.py.
    result["notes"].append(
        "NOTE: RPN reduction cannot be auto-validated from the original row. "
        "Confirm a new row with updated S/O/D and Status:Closed was appended via pfmea_append.py."
    )

    # Determine overall result
    failures = [n for n in result["notes"] if not n.startswith("NOTE:")]
    if not failures:
        result["result"] = "PASS"

    print(json.dumps(result, indent=2))
    return 0 if result["result"] == "PASS" else 1


def get_refusal_rate() -> float:
    if not AUDIT_LOG_PATH.exists():
        return 0.0
    text = AUDIT_LOG_PATH.read_text(encoding="utf-8")
    total = len(re.findall(r"## Audit:", text))
    refusals = len(re.findall(r"\*\*Allowed:\*\*\s*false", text, re.IGNORECASE))
    if total == 0:
        return 0.0
    return round(refusals / total * 100, 1)


def cmd_report(args):
    rows = get_open_rows(SOP_PATH)
    config = load_config()
    thresholds = config.get("risk_thresholds", {})
    critical_floor = thresholds.get("critical_rpn_floor", 150)
    high_floor = thresholds.get("high_rpn_floor", 100)

    critical = [r for r in rows if r["rpn"] >= critical_floor]
    high = [r for r in rows if high_floor <= r["rpn"] < critical_floor]
    medium = [r for r in rows if r["rpn"] < high_floor]
    in_progress = [r for r in rows if "In Progress" in r["status"] or "Solution Designed" in r["status"]]

    refusal_rate = get_refusal_rate()
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    def rpn_band(rpn):
        if rpn >= critical_floor:
            return "[CRITICAL]"
        elif rpn >= high_floor:
            return "[HIGH]    "
        else:
            return "[MONITOR] "

    lines = [
        "# AGE Workbench",
        f"**Last Updated:** {now}",
        "**AGE Status:** Active",
        "",
        "---",
        "",
        "## RPN Heat Map — Non-Closed Items",
        "",
        "| Priority | Table | RPN | Status | Process Step / Design Element | Failure Mode |",
        "|----------|-------|-----|--------|-------------------------------|--------------|",
    ]

    for r in rows:
        band = rpn_band(r["rpn"])
        status_short = r["status"][:25]
        lines.append(
            f"| {band} | {r['table'].upper()} | {r['rpn']} | {status_short} "
            f"| {r['step_or_element'][:40]} | {r['failure_mode'][:45]} |"
        )

    lines += [
        "",
        f"**Total Non-Closed:** {len(rows)} | "
        f"**Critical:** {len(critical)} | "
        f"**High:** {len(high)} | "
        f"**Monitor:** {len(medium)}",
        "",
        "---",
        "",
        "## Work Queue",
        "",
        f"### Critical (RPN ≥ {critical_floor}) — Requires Active Work",
    ]

    if critical:
        for r in critical:
            lines.append(f"- **RPN {r['rpn']}** [{r['table'].upper()}] {r['step_or_element']} / {r['failure_mode']}")
            lines.append(f"  - Status: {r['status']}")
            lines.append(f"  - Recommended Action: {r['action'][:80]}")
    else:
        lines.append("*(none — all Critical rows resolved)*")

    lines += [
        "",
        f"### High (RPN {high_floor}–{critical_floor - 1}) — SAGA Trigger Threshold",
    ]
    if high:
        for r in high:
            lines.append(f"- **RPN {r['rpn']}** [{r['table'].upper()}] {r['step_or_element']} / {r['failure_mode']}")
            lines.append(f"  - Status: {r['status']}")
    else:
        lines.append(f"*(none — all High rows resolved)*")

    lines += [
        "",
        "### Monitor (RPN < 100) — Track, No Immediate Action",
    ]
    if medium:
        for r in medium:
            lines.append(f"- **RPN {r['rpn']}** [{r['table'].upper()}] {r['step_or_element']} / {r['failure_mode']}")
            lines.append(f"  - Status: {r['status']}")
    else:
        lines.append("*(none — all Monitor rows resolved)*")

    lines += [
        "",
        "---",
        "",
        "## In-Progress Items",
        "",
    ]
    if in_progress:
        for r in in_progress:
            lines.append(f"- [{r['table'].upper()}] RPN {r['rpn']} — {r['step_or_element']} / {r['failure_mode']}")
            lines.append(f"  - Status: {r['raw_status']}")
    else:
        lines.append("*(No rows currently In Progress or Solution Designed)*")

    # Git state for health pulse. Avoid embedding the current commit SHA because
    # regenerating the report after a commit would immediately dirty the file.
    try:
        git_branch = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True, text=True, timeout=5
        ).stdout.strip() or "unknown"
    except Exception:
        git_branch = "unknown"

    # Proposal pipeline counts from row statuses
    pipeline = {
        "Solution Designed": len([r for r in rows if "Solution Designed" in r["status"]]),
        "In Progress": len([r for r in rows if "In Progress" in r["status"] and "Solution Designed" not in r["status"]]),
        "Triaged": len([r for r in rows if "Triaged" in r["status"] and "In Progress" not in r["status"] and "Solution Designed" not in r["status"]]),
    }

    lines += [
        "",
        "---",
        "",
        "## System Health Pulse",
        "",
        f"- **Non-closed rows:** {len(rows)}",
        f"- **Critical unaddressed (Open/Triaged):** "
        f"{len([r for r in critical if r['status'] in ('Open', 'Triaged')])}",
        f"- **Refusal rate (AUDIT-LOG.md):** {refusal_rate}%",
        "- **Last SAGA cycle:** see `saga-analyze.yml` run history",
        f"- **Workbench last updated:** {now}",
        f"- **Git branch:** `{git_branch}`",
        f"- **Proposal pipeline:** {pipeline['Solution Designed']} Solution Designed | "
        f"{pipeline['In Progress']} In Progress | {pipeline['Triaged']} Triaged",
        "",
        "---",
        "",
        "## Session Pulse Log",
        "",
        "| Session | Date | Actions Taken | Rows Moved | Notes |",
        "|---------|------|---------------|------------|-------|",
        "| *(Updated by AGE at each session end)* | | | | |",
        "",
        "---",
        "",
        "## Recently Closed Items",
        "",
        "*(No closed items yet — updated as rows reach Closed status)*",
    ]

    report = "\n".join(lines) + "\n"

    if args.dry_run:
        print(report)
    else:
        WORKBENCH_PATH.write_text(report, encoding="utf-8")
        print(f"AGE-WORKBENCH.md updated: {len(rows)} non-closed rows.")

    return 0


def cmd_preflight(args):
    config = load_config()
    thresholds = config.get("risk_thresholds", {})
    critical_floor = thresholds.get("critical_rpn_floor", 150)

    failures = []
    warnings = []

    # Check 1: critical config files readable
    for label, path in [("fmea-agent.config.json", CONFIG_PATH), ("SOP file", SOP_PATH)]:
        if not path.exists():
            failures.append(f"[config-check] {label} not found at {path}")

    if failures:
        for f in failures:
            print(f"FAIL {f}")
        return 2

    all_rows = parse_fmea_rows(SOP_PATH)

    # Check 2: Critical rows with Open/Triaged status and no AGE evidence note
    critical_unaddressed = [
        r for r in all_rows
        if r["rpn"] >= critical_floor
        and r["status"] in ("Open", "Triaged")
        and "<!-- AGE:" not in r["raw_status"]
    ]
    for r in critical_unaddressed:
        warnings.append(
            f"[critical-unaddressed] RPN {r['rpn']} [{r['table'].upper()}] "
            f"'{r['step_or_element']} / {r['failure_mode']}' — "
            f"status '{r['status']}' with no AGE triage note"
        )

    # Check 3: Closed rows without evidence artifact
    closed_no_evidence = [
        r for r in all_rows
        if "Closed" in r["status"] and "<!-- AGE:" not in r["raw_status"]
    ]
    for r in closed_no_evidence:
        failures.append(
            f"[integrity-violation] RPN {r['rpn']} [{r['table'].upper()}] "
            f"'{r['step_or_element']} / {r['failure_mode']}' — "
            f"Closed without AGE evidence artifact"
        )

    # Check 4: Proposal lint
    proposals_dir = SOP_PATH.parent / "proposals"
    if proposals_dir.exists():
        for pf in sorted(proposals_dir.glob("prop-AGE-*.md")):
            text = pf.read_text(encoding="utf-8")
            missing = [s for s in REQUIRED_PROPOSAL_SECTIONS if s not in text]
            if missing:
                failures.append(
                    f"[proposal-lint] {pf.name} missing: {', '.join(missing)}"
                )

    # Check 5: runtime monitor coverage on state-mutating workflow entrypoints
    runtime_validator = SOP_PATH.parent / "scripts" / "validate_runtime_monitor_entrypoints.py"
    if runtime_validator.exists():
        result = subprocess.run(
            [sys.executable, str(runtime_validator)],
            capture_output=True,
            text=True,
            timeout=20,
        )
        if result.returncode != 0:
            detail = (result.stdout + "\n" + result.stderr).strip()
            failures.append(f"[runtime-monitor-entrypoints] {detail}")
    else:
        failures.append("[runtime-monitor-entrypoints] validator missing at scripts/validate_runtime_monitor_entrypoints.py")

    for w in warnings:
        print(f"WARN {w}")
    for f in failures:
        print(f"FAIL {f}")

    if failures:
        print(f"\nPreflight: {len(failures)} FAIL, {len(warnings)} WARN")
        return 2
    elif warnings:
        print(f"\nPreflight: 0 FAIL, {len(warnings)} WARN — system operational with warnings")
        return 0
    else:
        print("Preflight: all checks PASS — system clear")
        return 0


def cmd_lint_sop(args):
    path = Path(args.file)
    if not path.exists():
        print(f"ERROR: File not found: {path}", file=sys.stderr)
        return 1

    text = path.read_text(encoding="utf-8")
    missing = [s for s in REQUIRED_SOP_SECTIONS if s not in text]

    if missing:
        print(f"FAIL: SOP {path.name} is missing required sections:")
        for m in missing:
            print(f"  - {m}")
        return 1
    else:
        print(f"PASS: {path.name} conforms to 5-section SOP format.")
        return 0


def cmd_lint_proposal(args):
    path = Path(args.file)
    if not path.exists():
        print(f"ERROR: File not found: {path}", file=sys.stderr)
        return 1

    text = path.read_text(encoding="utf-8")
    missing = []
    for section in REQUIRED_PROPOSAL_SECTIONS:
        if section not in text:
            missing.append(section)

    if proposal_failures is not None:
        for failure in proposal_failures(path, text):
            if failure not in missing:
                missing.append(failure)

    # Check Section 4 contains a concrete action (not just prose)
    section4_start = text.find("## 4. Gap-Closing Proposals")
    section5_start = text.find("## 5. Verification Checklist")
    if section4_start != -1 and section5_start != -1:
        section4_content = text[section4_start:section5_start]
        has_concrete = any(
            keyword in section4_content.lower()
            for keyword in ["script", ".py", ".yml", ".md", "scripts/", "workflow", "append", "update", "add ", "create "]
        )
        if not has_concrete:
            missing.append("Section 4: No concrete implementation mechanism found (needs a script, file, or workflow reference)")

    if missing:
        print(f"FAIL: Proposal {path.name} is missing required content:")
        for m in missing:
            print(f"  - {m}")
        return 1
    else:
        print(f"PASS: {path.name} conforms to 7-section SAGA format.")
        return 0


def main():
    parser = argparse.ArgumentParser(
        description="AGE Engineer — FMEA Lifecycle Management Engine"
    )
    subparsers = parser.add_subparsers(dest="command")

    # scan
    subparsers.add_parser("scan", help="List all open FMEA rows sorted by RPN")

    # queue
    queue_parser = subparsers.add_parser("queue", help="Show prioritized work queue")
    queue_parser.add_argument("--output-json", action="store_true", help="Output as JSON")

    # update-status
    us_parser = subparsers.add_parser("update-status", help="Transition a row's lifecycle state")
    us_parser.add_argument("--table", required=True, choices=["pfmea", "dfmea"])
    us_parser.add_argument("--step", required=True, help="Process Step / Design Element (exact match)")
    us_parser.add_argument("--failure", required=True, help="Failure Mode (exact match)")
    us_parser.add_argument("--status", required=True,
                           choices=["Triaged", "In Progress", "Solution Designed", "Verified", "Superseded"])
    us_parser.add_argument("--note", required=True, help="Evidence note (stored as HTML comment in status cell)")

    # verify-closure
    vc_parser = subparsers.add_parser("verify-closure", help="Validate a row is ready for Verified status")
    vc_parser.add_argument("--table", required=True, choices=["pfmea", "dfmea"])
    vc_parser.add_argument("--step", required=True)
    vc_parser.add_argument("--failure", required=True)
    vc_parser.add_argument("--evidence", required=True,
                           help="Artifact reference: 'commit:abc1234', 'issue:#42', 'file:path', or URL")

    # report
    report_parser = subparsers.add_parser("report", help="Regenerate AGE-WORKBENCH.md")
    report_parser.add_argument("--dry-run", action="store_true", help="Print to stdout instead of writing file")

    # lint-proposal
    lint_parser = subparsers.add_parser("lint-proposal", help="Validate a proposal file")
    lint_parser.add_argument("--file", required=True, help="Path to the proposal markdown file")

    # preflight
    subparsers.add_parser("preflight", help="Run system integrity checks before session work")

    # lint-sop
    sop_lint_parser = subparsers.add_parser("lint-sop", help="Validate a SOP file conforms to 5-section format")
    sop_lint_parser.add_argument("--file", required=True, help="Path to the SOP markdown file")

    args = parser.parse_args()

    dispatch = {
        "scan": cmd_scan,
        "queue": cmd_queue,
        "update-status": cmd_update_status,
        "verify-closure": cmd_verify_closure,
        "report": cmd_report,
        "lint-proposal": cmd_lint_proposal,
        "preflight": cmd_preflight,
        "lint-sop": cmd_lint_sop,
    }

    if args.command not in dispatch:
        parser.print_help()
        return 1

    return dispatch[args.command](args)


if __name__ == "__main__":
    sys.exit(main())

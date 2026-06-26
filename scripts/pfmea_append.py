"""
pfmea_append.py — Append a new row to the PFMEA or DFMEA table in
governed_systems_SOP_PFMEA_DFMEA.md.

Usage (called by audit-processor workflow):
    python3 scripts/pfmea_append.py \
        --table pfmea \
        --step "SAGA Loop Operation" \
        --failure-mode "Proposal approved without delta evidence" \
        --effect "SAGA Theater; no measurable improvement" \
        --severity 7 \
        --cause "Proposal template did not require delta metric" \
        --occurrence 4 \
        --controls "Manual review" \
        --detection 5 \
        --action "Enforce delta metric in proposal template" \
        --status Open \
        --issue 42

For DFMEA use --table dfmea and replace --step with --element.
"""

import argparse
import os
import re
import sys

SOP_PATH = os.path.join(
    os.path.dirname(__file__), "..", "governed_systems_SOP_PFMEA_DFMEA.md"
)

PFMEA_MARKER = "<!-- PFMEA_AUTO_APPEND_MARKER -->"
DFMEA_MARKER = "<!-- DFMEA_AUTO_APPEND_MARKER -->"


def _escape(value: str) -> str:
    """Escape pipe characters so the value is safe inside a Markdown table cell."""
    return str(value).replace("|", "\\|").strip()


def build_pfmea_row(args) -> str:
    s, o, d = int(args.severity), int(args.occurrence), int(args.detection)
    rpn = s * o * d
    issue_ref = f"Issue #{args.issue}" if args.issue else "auto"
    label = _escape(args.step)
    return (
        f"| {label} "
        f"| {_escape(args.failure_mode)} "
        f"| {_escape(args.effect)} "
        f"| {s} "
        f"| {_escape(args.cause)} "
        f"| {o} "
        f"| {_escape(args.controls)} "
        f"| {d} "
        f"| {rpn} "
        f"| {_escape(args.action)} ({issue_ref}) "
        f"| {_escape(args.status)} |\n"
    )


def build_dfmea_row(args) -> str:
    s, o, d = int(args.severity), int(args.occurrence), int(args.detection)
    rpn = s * o * d
    issue_ref = f"Issue #{args.issue}" if args.issue else "auto"
    label = _escape(args.element)
    return (
        f"| {label} "
        f"| {_escape(args.failure_mode)} "
        f"| {_escape(args.effect)} "
        f"| {s} "
        f"| {_escape(args.cause)} "
        f"| {o} "
        f"| {_escape(args.controls)} "
        f"| {d} "
        f"| {rpn} "
        f"| {_escape(args.action)} ({issue_ref}) "
        f"| {_escape(args.status)} |\n"
    )


def append_row(table: str, row: str, sop_path: str = SOP_PATH) -> None:
    marker = PFMEA_MARKER if table == "pfmea" else DFMEA_MARKER

    with open(sop_path, "r", encoding="utf-8") as fh:
        content = fh.read()

    if marker not in content:
        print(
            f"ERROR: Marker '{marker}' not found in {sop_path}. "
            "Cannot append row safely.",
            file=sys.stderr,
        )
        sys.exit(1)

    updated = content.replace(marker, row + "\n" + marker, 1)

    with open(sop_path, "w", encoding="utf-8") as fh:
        fh.write(updated)

    print(f"Appended new {table.upper()} row successfully.")


def parse_args():
    parser = argparse.ArgumentParser(
        description="Append a row to the PFMEA or DFMEA table."
    )
    parser.add_argument(
        "--table",
        choices=["pfmea", "dfmea"],
        required=True,
        help="Which table to append to.",
    )
    parser.add_argument(
        "--step", default="", help="Process step (PFMEA only)."
    )
    parser.add_argument(
        "--element", default="", help="Design element (DFMEA only)."
    )
    parser.add_argument("--failure-mode", required=True)
    parser.add_argument("--effect", required=True)
    parser.add_argument("--severity", type=int, required=True)
    parser.add_argument("--cause", required=True)
    parser.add_argument("--occurrence", type=int, required=True)
    parser.add_argument("--controls", default="None")
    parser.add_argument("--detection", type=int, required=True)
    parser.add_argument("--action", required=True)
    parser.add_argument("--status", default="Open")
    parser.add_argument("--issue", default="", help="GitHub issue number.")
    return parser.parse_args()


def main():
    args = parse_args()

    if args.table == "pfmea":
        if not args.step:
            print("ERROR: --step is required for PFMEA rows.", file=sys.stderr)
            sys.exit(1)
        row = build_pfmea_row(args)
    else:
        if not args.element:
            print("ERROR: --element is required for DFMEA rows.", file=sys.stderr)
            sys.exit(1)
        row = build_dfmea_row(args)

    append_row(args.table, row)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Append normal audit events and audit-processor error events to AUDIT-LOG.md."""

import argparse
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
AUDIT_LOG_PATH = REPO_ROOT / "AUDIT-LOG.md"


def timestamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def clean(value: str | None, default: str = "") -> str:
    text = default if value is None or value == "" else str(value)
    return " ".join(text.replace("\r", " ").replace("\n", " ").split())


def append_block(lines: list[str], audit_log_path: Path = AUDIT_LOG_PATH) -> None:
    audit_log_path.parent.mkdir(parents=True, exist_ok=True)
    with audit_log_path.open("a", encoding="utf-8") as handle:
        handle.write("\n".join(lines).rstrip() + "\n\n")


def audit_event_lines(args: argparse.Namespace) -> list[str]:
    return [
        f"## Audit: {clean(args.title, 'Untitled')}",
        f"- **Issue:** #{clean(args.issue, 'unknown')}",
        f"- **Action:** {clean(args.action, 'unknown')}",
        f"- **Allowed:** {clean(args.allowed, 'false').lower()}",
        f"- **Reason:** {clean(args.reason, 'unspecified')}",
        f"- **Source:** {clean(args.source, 'unknown')}",
        f"- **Timestamp:** {timestamp()}",
    ]


def processor_error_lines(args: argparse.Namespace) -> list[str]:
    issue = clean(args.issue, "unknown")
    stage = clean(args.stage, "unknown-stage")
    error = clean(args.error, "No error detail captured")
    return [
        f"## Audit: Processor Error - Issue #{issue} - {stage}",
        f"- **Issue:** #{issue}",
        "- **Action:** audit_processor_error",
        "- **Allowed:** false",
        f"- **Reason:** audit-processor stage failed: {stage}",
        "- **Source:** audit-processor.yml",
        f"- **Stage:** {stage}",
        f"- **Error:** {error}",
        f"- **Timestamp:** {timestamp()}",
    ]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Append an audit log event")
    subparsers = parser.add_subparsers(dest="command", required=True)

    event = subparsers.add_parser("event", help="Append a normal audit event")
    event.add_argument("--title", required=True)
    event.add_argument("--issue", required=True)
    event.add_argument("--action", required=True)
    event.add_argument("--allowed", choices=["true", "false", "True", "False"], required=True)
    event.add_argument("--reason", default="")
    event.add_argument("--source", default="unknown")

    error = subparsers.add_parser("processor-error", help="Append an audit processor failure event")
    error.add_argument("--issue", required=True)
    error.add_argument("--stage", required=True)
    error.add_argument("--error", default="")

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "event":
        append_block(audit_event_lines(args))
    elif args.command == "processor-error":
        append_block(processor_error_lines(args))
    else:
        parser.error(f"Unsupported command: {args.command}")

    print(f"Appended audit log entry to {AUDIT_LOG_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

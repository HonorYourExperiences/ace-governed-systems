#!/usr/bin/env python3
"""
Validate governance-sensitive changed files.

This script closes two AGE gaps:
- RPN 210: changed proposal files must use explicit Current -> Target -> Delta
  -> Gap-Closing structure.
- RPN 180: changed GitHub workflows that can modify repository state must include
  an explicit runtime monitor / verification-gate control.
"""

import argparse
import re
import sys
from pathlib import Path

PROPOSAL_PATH_RE = re.compile(r"(^|/)proposals/.*\.md$")
WORKFLOW_PATH_RE = re.compile(r"(^|/)\.github/workflows/.*\.ya?ml$")

REQUIRED_PROPOSAL_SECTIONS = [
    "## 1. Current State Assessment",
    "## 2. Target State Definition",
    "## 3. Delta Identification",
    "## 4. Gap-Closing Proposals",
    "## 5. Verification Checklist",
    "## 6. Success Metrics",
    "## 7. Phase Completion Triggers",
]

REQUIRED_DELTA_TERMS = [
    "current",
    "target",
    "delta",
    "gap",
]

STATE_MUTATION_MARKERS = [
    "contents: write",
    "issues: write",
    "pull-requests: write",
    "git push",
    "git commit",
    "issues.create",
    "pulls.create",
    "add-and-commit",
]

RUNTIME_MONITOR_MARKERS = [
    "runtime monitor",
    "verified label gate",
    "needs-verification",
    "verified saga",
    "age_engineer.py preflight",
    "validate_governance_change.py",
]


def normalize_path(path: str) -> str:
    return path.replace("\\", "/").lstrip("./")


def read_changed_files(path: Path) -> list[Path]:
    if not path.exists():
        raise FileNotFoundError(path)
    files = []
    for line in path.read_text(encoding="utf-8").splitlines():
        clean = line.strip()
        if clean:
            files.append(Path(clean))
    return files


def proposal_failures(path: Path, text: str) -> list[str]:
    failures = []
    for section in REQUIRED_PROPOSAL_SECTIONS:
        if section not in text:
            failures.append(f"{path}: missing required section `{section}`")

    lower = text.lower()
    for term in REQUIRED_DELTA_TERMS:
        if term not in lower:
            failures.append(f"{path}: missing explicit `{term}` language")

    section3_start = text.find("## 3. Delta Identification")
    section4_start = text.find("## 4. Gap-Closing Proposals")
    if section3_start != -1 and section4_start != -1:
        section3 = text[section3_start:section4_start].lower()
        for term in ("current", "target", "delta"):
            if term not in section3:
                failures.append(f"{path}: Section 3 must name `{term}` explicitly")

    section4_start = text.find("## 4. Gap-Closing Proposals")
    section5_start = text.find("## 5. Verification Checklist")
    if section4_start != -1 and section5_start != -1:
        section4 = text[section4_start:section5_start].lower()
        has_concrete = any(
            marker in section4
            for marker in ("script", ".py", ".yml", ".yaml", ".md", "workflow", "append", "update", "add ", "create ")
        )
        if not has_concrete:
            failures.append(f"{path}: Section 4 needs a concrete script, file, or workflow mechanism")

    return failures


def workflow_failures(path: Path, text: str) -> list[str]:
    lower = text.lower()
    mutates_state = any(marker in lower for marker in STATE_MUTATION_MARKERS)
    if not mutates_state:
        return []

    has_monitor = any(marker in lower for marker in RUNTIME_MONITOR_MARKERS)
    if has_monitor:
        return []

    return [
        f"{path}: state-mutating workflow lacks runtime monitor / verified-SAGA gate marker"
    ]


def validate_file(path: Path) -> list[str]:
    norm = normalize_path(str(path))
    if not path.exists():
        return []
    text = path.read_text(encoding="utf-8")

    if PROPOSAL_PATH_RE.search(norm):
        return proposal_failures(path, text)
    if WORKFLOW_PATH_RE.search(norm):
        return workflow_failures(path, text)
    return []


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate governance-sensitive changed files")
    parser.add_argument("--files", help="Newline-delimited changed-files list")
    parser.add_argument("paths", nargs="*", help="Files to validate")
    args = parser.parse_args()

    paths = [Path(p) for p in args.paths]
    if args.files:
        paths.extend(read_changed_files(Path(args.files)))

    failures = []
    for path in paths:
        failures.extend(validate_file(path))

    if failures:
        print("Governance change validation failed:")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("Governance change validation PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())

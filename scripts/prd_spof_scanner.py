#!/usr/bin/env python3
"""
AGE PRD SPOF Scanner

Parses markdown PRDs and proposal files for Single Points of Failure (SPOFs).
Creates GitHub issues for each SPOF found. Called by age-prd-scan.yml.

Usage:
  python3 scripts/prd_spof_scanner.py \
    --files /tmp/changed_files.txt \
    --output /tmp/spof_issues.json

Exit codes: 0=scan complete, 1=error, 2=no files to scan
"""

import argparse
import json
import re
import sys
from pathlib import Path

CONFIG_PATH = Path(__file__).parent.parent / "fmea-agent.config.json"
REPO_ROOT = Path(__file__).parent.parent


def load_config() -> dict:
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH) as f:
            return json.load(f)
    return {}


def get_spof_patterns(config: dict) -> list[str]:
    default_patterns = [
        r"depends? only on",
        r"only.*webhook",
        r"no fallback",
        r"no backup",
        r"required before anything",
        r"single.*point",
        r"must.*complete.*before",
        r"blocks? all",
        r"cannot proceed without",
        r"entire.*depends",
        r"only one.*can",
        r"if.*fails.*everything",
    ]
    configured = config.get("prd_scan", {}).get("spof_patterns", [])
    return list(set(default_patterns + configured))


def scan_file_for_spofs(filepath: Path, patterns: list[str]) -> list[dict]:
    """
    Scan a markdown file for SPOF patterns.
    Returns list of findings: {line_number, line_text, pattern, context}
    """
    if not filepath.exists():
        return []

    try:
        text = filepath.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return []

    lines = text.splitlines()
    findings = []

    for line_num, line in enumerate(lines, start=1):
        stripped = line.strip()
        if stripped.startswith("```") or stripped.startswith("#") or stripped.startswith("<!--"):
            continue

        for pattern in patterns:
            if re.search(pattern, line, re.IGNORECASE):
                start = max(0, line_num - 3)
                end = min(len(lines), line_num + 2)
                context_lines = lines[start:end]
                context = "\n".join(
                    f"  {'>' if i + start + 1 == line_num else ' '} {ln}"
                    for i, ln in enumerate(context_lines)
                )
                findings.append({
                    "line_number": line_num,
                    "line_text": line.strip()[:120],
                    "pattern": pattern,
                    "context": context,
                })
                break  # one finding per line max

    return findings


def build_issue(filepath: Path, findings: list[dict]) -> dict:
    try:
        rel_path = str(filepath.relative_to(REPO_ROOT))
    except ValueError:
        rel_path = str(filepath)

    finding_blocks = []
    for i, f in enumerate(findings, start=1):
        finding_blocks.append(
            f"### Finding {i}\n"
            f"**Line {f['line_number']}:** `{f['line_text']}`\n"
            f"Matched pattern: `{f['pattern']}`\n"
            f"```\n{f['context']}\n```"
        )

    body = (
        "## [FMEA-Risk] Single Point of Failure Detection\n\n"
        f"**Source file:** `{rel_path}`  \n"
        f"**Findings:** {len(findings)} potential SPOF(s) detected  \n"
        "**Detected by:** AGE PRD SPOF Scanner (`scripts/prd_spof_scanner.py`)\n\n"
        "---\n\n"
        "## Findings\n\n"
        + "\n\n".join(finding_blocks)
        + "\n\n---\n\n"
        "## Recommended Action\n\n"
        "For each finding:\n"
        "1. **Assess:** Is this a genuine SPOF? Would the system halt if this dependency failed?\n"
        "2. **Design redundancy:** Add a fallback path, async queue, or manual override\n"
        "3. **Document:** If the SPOF is accepted by design, note why the risk is acceptable\n"
        "4. **Update FMEA:** Append a row via `scripts/pfmea_append.py` if the SPOF is accepted\n\n"
        "## Verification Checklist\n\n"
        "- [ ] Each finding reviewed and assessed\n"
        "- [ ] Redundancy or accepted-risk decision documented\n"
        "- [ ] PFMEA updated if SPOF is accepted\n"
        "- [ ] Way Through axiom confirmed: design empowers rather than creates external dependency\n\n"
        "**Add the `verified` label once checklist is confirmed.**"
    )

    return {
        "title": f"[FMEA-Risk] SPOF: {len(findings)} finding(s) in `{rel_path}`",
        "body": body,
        "labels": ["fmea-risk", "spof", "needs-verification"],
    }


def main():
    parser = argparse.ArgumentParser(description="AGE PRD SPOF Scanner")
    parser.add_argument("--files", required=True,
                        help="Path to file containing list of changed markdown files (one per line)")
    parser.add_argument("--output", required=True, help="Output JSON file for issue creation requests")
    args = parser.parse_args()

    files_list_path = Path(args.files)
    if not files_list_path.exists():
        print(f"ERROR: Files list not found: {args.files}", file=sys.stderr)
        return 1

    changed_files_raw = files_list_path.read_text(encoding="utf-8").splitlines()
    changed_files = [f.strip() for f in changed_files_raw if f.strip().endswith(".md")]

    if not changed_files:
        print("No markdown files to scan.")
        Path(args.output).parent.mkdir(parents=True, exist_ok=True)
        Path(args.output).write_text("[]")
        return 2

    config = load_config()
    scan_paths = config.get("prd_scan", {}).get("scan_paths", ["proposals/", "cape-able-heroes/"])
    patterns = get_spof_patterns(config)

    files_to_scan = []
    for f in changed_files:
        f_path = REPO_ROOT / f
        should_scan = any(f.startswith(sp) for sp in scan_paths)
        if not should_scan and "/" not in f:
            should_scan = any(
                kw in f.lower()
                for kw in ["proposal", "prd", "spec", "plan", "strategy", "model", "roadmap"]
            )
        if should_scan:
            files_to_scan.append(f_path)

    if not files_to_scan:
        print("No files in configured scan paths.")
        Path(args.output).parent.mkdir(parents=True, exist_ok=True)
        Path(args.output).write_text("[]")
        return 0

    all_issues = []
    seen_titles: set[str] = set()
    for filepath in files_to_scan:
        findings = scan_file_for_spofs(filepath, patterns)
        if findings:
            issue = build_issue(filepath, findings)
            if issue["title"] not in seen_titles:
                seen_titles.add(issue["title"])
                all_issues.append(issue)
                print(f"  {len(findings)} SPOF(s) found in {filepath.name}")
        else:
            print(f"  Clean: {filepath.name}")

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(all_issues, indent=2))

    print(f"\nScan complete: {len(all_issues)} issue(s) to create.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

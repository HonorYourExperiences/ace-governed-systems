#!/usr/bin/env python3
"""
AGE Dependency & Compliance Scanner

Scans changed workflow YAML and Python script files for compliance violations:
- Hardcoded secrets / credentials
- Missing permissions blocks in workflows
- Error suppression on audit-sensitive steps
- Shell injection patterns
- Unauthorized writes to constitution files

Called by age-pr-analysis.yml as part of the PR analysis pipeline.

Usage:
  python3 scripts/dependency_compliance.py \
    --files /tmp/changed_files.txt \
    --output /tmp/compliance_findings.json

Exit codes: 0=clean, 1=error, 2=high-severity finding
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


# Each rule: (pattern, severity, description, mitigation)
WORKFLOW_RULES = [
    (
        r'(?i)(password|api_key|secret_key|private_key|access_token)\s*:\s*["\'][^$][^"\']{4,}',
        9,
        "Potential hardcoded credential in workflow",
        "Use GitHub Secrets (${{ secrets.NAME }}) instead of inline values.",
    ),
    (
        r"continue-on-error:\s*true",
        7,
        "Error suppression active — audit-sensitive steps may fail silently",
        "Remove continue-on-error or add explicit error-path audit logging.",
    ),
    (
        r"shell:\s*true",
        8,
        "shell: true enables shell injection via untrusted input",
        "Avoid shell: true. Use explicit shell commands with quoted variables.",
    ),
    (
        r"permissions:\s*\n\s*contents:\s*write",
        4,
        "Workflow requests write permissions — verify this is intentional",
        "Confirm write access is required. Use read permissions where possible.",
    ),
]

PYTHON_RULES = [
    (
        r'subprocess\.(run|call|Popen)\s*\([^)]*shell\s*=\s*True',
        9,
        "Shell injection risk: subprocess with shell=True and dynamic input",
        "Pass commands as a list, not a string. Never pass f-strings to shell=True.",
    ),
    (
        r'os\.system\s*\(',
        7,
        "os.system() is vulnerable to shell injection",
        "Replace with subprocess.run(cmd_list, check=True).",
    ),
    (
        r'eval\s*\(',
        9,
        "eval() can execute arbitrary code",
        "Replace eval() with json.loads(), ast.literal_eval(), or explicit parsing.",
    ),
    (
        r'open\s*\([^)]*\+[^)]*\)',
        5,
        "Potential path traversal: string concatenation in file open()",
        "Use pathlib.Path and .resolve() to validate paths before opening.",
    ),
]

CONSTITUTION_WRITE_RULE = (
    r"(write_text|write|open.*['\"]w['\"])",
    10,
    "Potential write to constitution/critical file",
    "Constitution files require explicit human escalation before modification.",
)


def check_file(filepath: Path, config: dict) -> list[dict]:
    findings = []
    if not filepath.exists():
        return findings

    text = filepath.read_text(encoding="utf-8", errors="replace")
    lines = text.splitlines()
    suffix = filepath.suffix.lower()
    constitution_files = config.get("dependency_scan", {}).get("constitution_files", [])

    rules = []
    if suffix in (".yml", ".yaml"):
        rules = WORKFLOW_RULES
    elif suffix == ".py":
        rules = PYTHON_RULES
        # Check for writes to constitution files
        for const_file in constitution_files:
            if const_file in text:
                pattern, s, desc, fix = CONSTITUTION_WRITE_RULE
                for line_num, line in enumerate(lines, 1):
                    if re.search(pattern, line) and const_file in text[max(0, text.find(line) - 200):text.find(line) + 200]:
                        findings.append({
                            "file": str(filepath.relative_to(REPO_ROOT)),
                            "line_number": line_num,
                            "line_text": line.strip()[:100],
                            "description": f"{desc}: `{const_file}`",
                            "severity": s,
                            "mitigation": fix,
                            "action_priority": "HIGH",
                        })

    for pattern, severity, description, mitigation in rules:
        for line_num, line in enumerate(lines, 1):
            if re.search(pattern, line):
                ap = "HIGH" if severity >= 8 else ("MEDIUM" if severity >= 5 else "LOW")
                findings.append({
                    "file": str(filepath.relative_to(REPO_ROOT)),
                    "line_number": line_num,
                    "line_text": line.strip()[:100],
                    "description": description,
                    "severity": severity,
                    "mitigation": mitigation,
                    "action_priority": ap,
                })

    return findings


def main():
    parser = argparse.ArgumentParser(description="AGE Dependency & Compliance Scanner")
    parser.add_argument("--files", required=True,
                        help="Path to file with list of changed files (one per line)")
    parser.add_argument("--output", required=True, help="Output JSON path for findings")
    args = parser.parse_args()

    files_list_path = Path(args.files)
    if not files_list_path.exists():
        print(f"ERROR: Files list not found: {args.files}", file=sys.stderr)
        return 1

    config = load_config()
    watch_patterns = config.get("dependency_scan", {}).get("watch_files", [
        ".github/workflows/*.yml",
        "scripts/*.py",
    ])

    changed_raw = files_list_path.read_text(encoding="utf-8").splitlines()
    changed_files = [f.strip() for f in changed_raw if f.strip()]

    import fnmatch
    files_to_scan = []
    for f in changed_files:
        if any(fnmatch.fnmatch(f, pat) for pat in watch_patterns):
            files_to_scan.append(REPO_ROOT / f)

    if not files_to_scan:
        print("No watched files changed.")
        Path(args.output).parent.mkdir(parents=True, exist_ok=True)
        Path(args.output).write_text("[]")
        return 0

    all_findings = []
    for filepath in files_to_scan:
        file_findings = check_file(filepath, config)
        all_findings.extend(file_findings)
        if file_findings:
            print(f"  {len(file_findings)} finding(s) in {filepath.name}")
        else:
            print(f"  Clean: {filepath.name}")

    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    Path(args.output).write_text(json.dumps(all_findings, indent=2))

    high_findings = [f for f in all_findings if f["action_priority"] == "HIGH"]
    print(f"\nCompliance scan: {len(all_findings)} finding(s), {len(high_findings)} HIGH priority.")

    return 2 if high_findings else 0


if __name__ == "__main__":
    sys.exit(main())

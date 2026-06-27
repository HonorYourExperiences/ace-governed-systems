#!/usr/bin/env python3
"""
scan_content_antipatterns.py — AGE Way Through Anti-Pattern Scanner

Scans markdown files for rescue-modeling and aspiration-theater anti-patterns
that violate the Way Through axiom (Axiom 2) and Evidence & Capability axiom
(Axiom 4).

HIGH-severity hits in hero/parent sections exit 1 to block CI merges.
MEDIUM hits are reported but do not block.

Usage:
    python3 scripts/scan_content_antipatterns.py --path cape-able-heroes/
    python3 scripts/scan_content_antipatterns.py --path cape-able-heroes/BUSINESS-MODEL.md
    python3 scripts/scan_content_antipatterns.py --path cape-able-heroes/ --output /tmp/scan.json

Exit codes:
    0 — Scan complete, no HIGH-severity hits (CI safe)
    1 — One or more HIGH-severity hits found (CI blocks merge)
    2 — Error (missing path, parse failure)
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import NamedTuple

# ---------------------------------------------------------------------------
# HIGH-severity sections: patterns found here trigger exit 1
# These are the highest-visibility surfaces per the FMEA row
# ---------------------------------------------------------------------------
HIGH_SEVERITY_SECTION_PATTERNS = [
    r"^#\s",              # H1 headings
    r"^##\s",             # H2 headings
    r"^\*\*.*\*\*\s*$",  # bold-only lines (CTA/emphasis)
    r"hero",              # any section labeled hero
    r"parent",            # parent-facing sections
    r"mission",           # mission statements
    r"vision",            # vision statements
    r"about",             # about sections
]

# ---------------------------------------------------------------------------
# Rescue-modeling anti-patterns (Way Through Axiom 2 violations)
# Each entry: (regex_pattern, severity_floor, short_label, way_through_alternative)
# severity_floor: "HIGH" = always HIGH; "MEDIUM" = HIGH only if in high-vis section
# ---------------------------------------------------------------------------
RESCUE_PATTERNS = [
    # "we help [someone]" — agent is BYDT, not the child
    (r"\bwe help\b", "HIGH", "rescue-agent",
     "Reframe: name the child as agent. e.g., 'children discover' not 'we help children'"),

    # "we build / we develop / we grow [capability in someone]"
    (r"\bwe (build|develop|grow|create|give|provide|offer|deliver)\b.{0,40}\b(children|child|kids?|families|parents?|students?)\b",
     "HIGH", "rescue-capability-transfer",
     "Reframe: child builds/grows their own capability. BYDT creates conditions."),

    # "done for you / handled for you"
    (r"\b(done|handled|taken care of)\b.{0,20}\bfor you\b", "HIGH", "done-for-you",
     "Reframe: describe what the participant does, not what is done to them."),

    # "you don't have to / you won't have to"
    (r"\byou (don'?t|won'?t|do not|will not) have to\b", "MEDIUM", "outsource-invitation",
     "Reframe: affirm capability. e.g., 'you already know how to begin' not 'you don't have to worry'"),

    # "let us / leave it to us"
    (r"\b(let us|leave it to us|we'?ll (do|handle|take care of|manage))\b", "HIGH", "rescue-delegation",
     "Reframe: describe conditions BYDT creates, not work BYDT does for the participant."),

    # "stress-free / worry-free / burden-free"
    (r"\b(stress[- ]free|worry[- ]free|burden[- ]free|hassle[- ]free|pressure[- ]free)\b",
     "MEDIUM", "rescue-relief",
     "Reframe: name the child's own resilience rather than removing the stress."),

    # "we fix / we solve / we address your [problem]"
    (r"\bwe (fix|solve|address|resolve|eliminate)\b.{0,40}\b(your|their|the child'?s?)\b",
     "HIGH", "rescue-problem-solver",
     "Reframe: the child moves through their challenge; BYDT does not solve it for them."),

    # "transform your child" — child is object, not agent
    (r"\btransform (your child|children|kids?|your (child|family))\b", "HIGH", "aspiration-theater-transform",
     "Reframe: 'witness your child as they grow' — child is agent of their own transformation."),

    # "unlock their potential / unlock your potential"
    (r"\bunlock (their|your|the child'?s?) potential\b", "HIGH", "aspiration-theater-unlock",
     "Reframe: 'recognize the potential already present' — potential is not locked."),

    # "give your child [capability noun]" — implies child lacks it
    (r"\bgive (your child|children|kids?).{0,30}\b(confidence|courage|resilience|tools|skills|strength)\b",
     "HIGH", "rescue-capability-gift",
     "Reframe: the child already has this; BYDT creates conditions to practice it."),

    # "help your child overcome / become / succeed"
    (r"\bhelp (your child|children|kids?) (overcome|become|succeed|achieve|develop|build)\b",
     "MEDIUM", "rescue-parent-agent",
     "Reframe: 'watch your child move through' — parent is witness, not fixer."),

    # "best version of themselves" — conditional worth
    (r"\bbest version of (themselves?|yourself|your child)\b", "MEDIUM", "conditional-worth",
     "Reframe: 'more of who they already are' — no 'best version' hierarchy."),
]

# ---------------------------------------------------------------------------
# Aspiration-theater patterns (Evidence & Capability Axiom 4 violations)
# ---------------------------------------------------------------------------
ASPIRATION_PATTERNS = [
    # "watch your child become extraordinary / amazing / unstoppable"
    (r"\b(extraordinary|unstoppable|limitless|amazing|incredible|remarkable)\b.{0,20}\b(child|children|kids?|potential)\b",
     "MEDIUM", "aspiration-theater-superlative",
     "Reframe: name an observable behavior or logged evidence rather than a superlative."),

    # "transform / change everything"
    (r"\b(transform|change) everything\b", "MEDIUM", "aspiration-theater-totality",
     "Reframe: name the specific, observable change."),

    # Vague transformation language without observable evidence
    (r"\b(transform|awaken|ignite|unleash|supercharge)\b.{0,30}\b(child|children|kids?|potential|confidence|power)\b",
     "MEDIUM", "aspiration-theater-vague",
     "Reframe: tie outcome to a specific, observable action the child takes."),
]

ALL_PATTERNS = RESCUE_PATTERNS + ASPIRATION_PATTERNS


class Hit(NamedTuple):
    file: str
    line_number: int
    line_text: str
    pattern_label: str
    severity: str          # HIGH or MEDIUM
    alternative: str


def is_high_visibility_context(line: str, surrounding_lines: list[str]) -> bool:
    """Return True if this line is in a high-visibility section."""
    context = [line] + surrounding_lines[:3]
    for ctx_line in context:
        for pat in HIGH_SEVERITY_SECTION_PATTERNS:
            if re.search(pat, ctx_line, re.IGNORECASE):
                return True
    return False


def scan_file(filepath: str) -> list[Hit]:
    hits = []
    try:
        with open(filepath, encoding="utf-8") as f:
            lines = f.readlines()
    except (OSError, UnicodeDecodeError) as e:
        print(f"WARN: Could not read {filepath}: {e}", file=sys.stderr)
        return hits

    for i, raw_line in enumerate(lines):
        line = raw_line.rstrip()
        if not line.strip():
            continue
        # Surrounding context lines for high-vis section detection
        surrounding = [l.rstrip() for l in lines[max(0, i - 3):i]]

        for pattern, severity_floor, label, alternative in ALL_PATTERNS:
            if re.search(pattern, line, re.IGNORECASE):
                # Determine effective severity
                if severity_floor == "HIGH":
                    effective_severity = "HIGH"
                else:  # MEDIUM floor — escalate if in high-vis context
                    effective_severity = (
                        "HIGH" if is_high_visibility_context(line, surrounding) else "MEDIUM"
                    )
                hits.append(Hit(
                    file=filepath,
                    line_number=i + 1,
                    line_text=line,
                    pattern_label=label,
                    severity=effective_severity,
                    alternative=alternative,
                ))
    return hits


def scan_path(path: str) -> list[Hit]:
    p = Path(path)
    if not p.exists():
        print(f"ERROR: Path does not exist: {path}", file=sys.stderr)
        sys.exit(2)

    all_hits: list[Hit] = []
    if p.is_file():
        if p.suffix == ".md":
            all_hits.extend(scan_file(str(p)))
    else:
        for md_file in sorted(p.rglob("*.md")):
            # Skip the checklist itself and proposal files (meta-documents)
            if md_file.name == "WAY-THROUGH-CONTENT-CHECKLIST.md":
                continue
            if "proposals/" in str(md_file):
                continue
            all_hits.extend(scan_file(str(md_file)))
    return all_hits


def format_report(hits: list[Hit], verbose: bool = True) -> str:
    if not hits:
        return "✅  No rescue-modeling or aspiration-theater anti-patterns found."

    high_hits = [h for h in hits if h.severity == "HIGH"]
    medium_hits = [h for h in hits if h.severity == "MEDIUM"]

    lines = [
        f"Anti-pattern scan results: {len(hits)} hit(s) — {len(high_hits)} HIGH, {len(medium_hits)} MEDIUM",
        "",
    ]

    for severity_label, group in [("HIGH", high_hits), ("MEDIUM", medium_hits)]:
        if not group:
            continue
        lines.append(f"## {severity_label} severity")
        for h in group:
            lines.append(f"  {h.file}:{h.line_number} [{h.pattern_label}]")
            if verbose:
                lines.append(f"    Line: {h.line_text.strip()}")
                lines.append(f"    Way Through: {h.alternative}")
            lines.append("")

    if high_hits:
        lines.append("❌  CI BLOCKED — resolve HIGH-severity hits before merging.")
        lines.append("    Run this script after revisions to confirm exit 0.")
    else:
        lines.append("⚠️   MEDIUM hits present — review recommended before publish.")
        lines.append("    MEDIUM hits do not block CI.")

    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Scan markdown files for Way Through anti-patterns."
    )
    parser.add_argument(
        "--path", required=True,
        help="File or directory to scan (scans *.md recursively)."
    )
    parser.add_argument(
        "--output", default=None,
        help="Optional: write JSON results to this file path."
    )
    parser.add_argument(
        "--quiet", action="store_true",
        help="Suppress per-hit detail in stdout report."
    )
    args = parser.parse_args()

    hits = scan_path(args.path)

    report = format_report(hits, verbose=not args.quiet)
    print(report)

    if args.output:
        out_data = [
            {
                "file": h.file,
                "line": h.line_number,
                "text": h.line_text,
                "pattern": h.pattern_label,
                "severity": h.severity,
                "way_through_alternative": h.alternative,
            }
            for h in hits
        ]
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(out_data, f, indent=2)
        print(f"\nJSON results written to {args.output}")

    high_count = sum(1 for h in hits if h.severity == "HIGH")
    return 1 if high_count > 0 else 0


if __name__ == "__main__":
    sys.exit(main())

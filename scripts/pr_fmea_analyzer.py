#!/usr/bin/env python3
"""
AGE PR FMEA Analyzer

Analyzes a Pull Request diff against the governance framework and posts
a structured FMEA risk assessment comment. Called by age-pr-analysis.yml.

Usage:
  python3 scripts/pr_fmea_analyzer.py \
    --diff /tmp/pr_diff.txt \
    --pr-number 42 \
    --pr-title "feat: update SAGA loop" \
    --output /tmp/fmea_comment.md

Exit codes: 0=analysis complete, 1=error, 2=high-severity finding (blocks PR)
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path

CONFIG_PATH = Path(__file__).parent.parent / "fmea-agent.config.json"

SYSTEM_PROMPT = """You are an FMEA (Failure Mode and Effects Analysis) risk analyst embedded in a governance framework.

The project uses five immutable core axioms:
1. Inherent Sufficiency — value before performance
2. Way Through — capability and discernment over rescue or outsourcing
3. Witnessing & Mature Presence — relational maturity first
4. Evidence & Capability — real capability over aspiration theater
5. Audit Integrity — full lineage and accountability

FMEA Scoring:
- S (Severity 1-10): Business/governance impact. 10=constitution violation or full system failure. 1=cosmetic.
- O (Occurrence 1-10): Probability given code complexity, missing tests, no reviewer. 10=very likely. 1=extremely rare.
- D (Detection 1-10): How detectable is this before it causes harm? 10=undetectable. 1=immediately obvious.
- RPN = S × O × D. RPN ≥ 100 triggers SAGA. S ≥ 9 requires human sign-off.
- Action Priority: HIGH if RPN ≥ 100 or S ≥ 8. MEDIUM if RPN 50-99. LOW if < 50.

For EACH significant change in the diff:
1. Identify the component/function being changed
2. Name the potential failure mode (what could go wrong)
3. Score S, O, D with brief justification
4. Assign Action Priority
5. Suggest a specific mitigation

Respond ONLY with valid JSON in this exact format:
{
  "summary": "One sentence describing the overall risk profile of this PR",
  "findings": [
    {
      "component": "File or system component",
      "function": "What this component is supposed to do",
      "failure_mode": "What could go wrong",
      "s": 7,
      "s_reason": "Brief justification",
      "o": 4,
      "o_reason": "Brief justification",
      "d": 5,
      "d_reason": "Brief justification",
      "rpn": 140,
      "action_priority": "HIGH",
      "mitigation": "Specific action to take before merging"
    }
  ],
  "axiom_risks": ["List any axiom violations or near-misses found"],
  "recommended_next_steps": ["Bullet list of next steps"]
}

If the diff is very small or clearly low-risk, return an empty findings array with a summary explaining why.
"""


def load_config() -> dict:
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH) as f:
            return json.load(f)
    return {}


def load_diff(diff_path: str) -> str:
    path = Path(diff_path)
    if not path.exists():
        return ""
    text = path.read_text(encoding="utf-8", errors="replace")
    # Truncate to max_diff_lines from config
    config = load_config()
    max_lines = config.get("pr_analysis", {}).get("max_diff_lines", 500)
    lines = text.splitlines()
    if len(lines) > max_lines:
        lines = lines[:max_lines]
        lines.append(f"\n[...diff truncated at {max_lines} lines...]")
    return "\n".join(lines)


def get_critical_system_warnings(diff_text: str) -> list[str]:
    config = load_config()
    critical = config.get("critical_systems", {})
    warnings = []
    for name, path in critical.items():
        if path.rstrip("/") in diff_text or path in diff_text:
            warnings.append(f"⚠️ **Critical system touched:** `{path}` ({name})")
    return warnings


def call_claude_api(diff_text: str, pr_title: str) -> dict:
    try:
        import urllib.request
        import urllib.error
    except ImportError:
        return None

    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        return None

    config = load_config()
    model = config.get("pr_analysis", {}).get("model", "claude-haiku-4-5-20251001")

    user_content = f"PR Title: {pr_title}\n\nDiff:\n{diff_text}"

    payload = {
        "model": model,
        "max_tokens": 2000,
        "system": SYSTEM_PROMPT,
        "messages": [{"role": "user", "content": user_content}],
    }

    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=data,
        headers={
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
    )

    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            body = json.loads(resp.read().decode("utf-8"))
            content = body["content"][0]["text"]
            # Extract JSON from response (may have surrounding text)
            match = re.search(r"\{.*\}", content, re.DOTALL)
            if match:
                return json.loads(match.group())
    except Exception as e:
        print(f"Warning: Claude API call failed: {e}", file=sys.stderr)

    return None


def call_openai_api(diff_text: str, pr_title: str) -> dict:
    try:
        import urllib.request
    except ImportError:
        return None

    api_key = os.environ.get("OPENAI_API_KEY", "")
    if not api_key:
        return None

    config = load_config()
    model = config.get("pr_analysis", {}).get("fallback_model", "gpt-4o-mini")

    user_content = f"PR Title: {pr_title}\n\nDiff:\n{diff_text}"

    payload = {
        "model": model,
        "max_tokens": 2000,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
        ],
    }

    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        "https://api.openai.com/v1/chat/completions",
        data=data,
        headers={
            "Authorization": f"Bearer {api_key}",
            "content-type": "application/json",
        },
    )

    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            body = json.loads(resp.read().decode("utf-8"))
            content = body["choices"][0]["message"]["content"]
            match = re.search(r"\{.*\}", content, re.DOTALL)
            if match:
                return json.loads(match.group())
    except Exception as e:
        print(f"Warning: OpenAI API fallback failed: {e}", file=sys.stderr)

    return None


def fallback_rule_based_analysis(diff_text: str) -> dict:
    """Rule-based analysis when Claude API is unavailable."""
    findings = []
    config = load_config()
    critical = config.get("critical_systems", {})

    # Check for constitution file changes
    for name, path in critical.items():
        if path.rstrip("/") in diff_text:
            s = 9 if name == "constitution" else 7
            findings.append({
                "component": path,
                "function": f"Governance: {name}",
                "failure_mode": f"Unreviewed change to critical system '{name}'",
                "s": s,
                "s_reason": "Critical governance file — changes can affect all downstream behavior",
                "o": 4,
                "o_reason": "PR-based changes are moderately likely to introduce unintended effects",
                "d": 6,
                "d_reason": "Governance changes are hard to test automatically",
                "rpn": s * 4 * 6,
                "action_priority": "HIGH" if s >= 8 else "MEDIUM",
                "mitigation": f"Review change against five core axioms. Confirm no axiom definitions are modified.",
            })

    # Check for hardcoded secrets
    secret_patterns = [
        (r'(?i)(password|api_key|secret|token)\s*[:=]\s*["\'][^"\']{8,}', "Potential hardcoded credential"),
        (r'continue-on-error:\s*true', "Error suppression on potentially audit-sensitive step"),
        (r'shell:\s*true', "Shell injection risk — avoid shell: true in workflows"),
    ]
    for pattern, description in secret_patterns:
        if re.search(pattern, diff_text):
            findings.append({
                "component": "Workflow / Script",
                "function": "Automation security",
                "failure_mode": description,
                "s": 8,
                "s_reason": "Security or audit integrity violation",
                "o": 3,
                "o_reason": "Pattern detected in diff",
                "d": 7,
                "d_reason": "May not be caught by standard review",
                "rpn": 168,
                "action_priority": "HIGH",
                "mitigation": f"Review and remediate: {description}",
            })

    return {
        "summary": f"Rule-based analysis found {len(findings)} potential issue(s). Claude API was unavailable for deeper analysis.",
        "findings": findings,
        "axiom_risks": [],
        "recommended_next_steps": ["Review findings above", "Enable Claude API for deeper analysis"],
    }


def render_comment(analysis: dict, pr_number: str, pr_title: str, critical_warnings: list[str]) -> str:
    findings = analysis.get("findings", [])
    has_high = any(f.get("action_priority") == "HIGH" for f in findings)
    config = load_config()
    auto_block_s = config.get("pr_analysis", {}).get("auto_block_severity", 9)
    has_blocker = any(f.get("s", 0) >= auto_block_s for f in findings)

    lines = [
        f"## 🤖 AGE Risk Assessment: PR #{pr_number}",
        "",
        f"*Analyzing changes to: `{pr_title}`*",
        "",
    ]

    if critical_warnings:
        lines += critical_warnings
        lines.append("")

    if not findings:
        lines += [
            f"**{analysis.get('summary', 'No significant risk findings.')}**",
            "",
            "✅ No high-priority failure modes detected. This PR appears low-risk.",
        ]
    else:
        lines += [
            analysis.get("summary", ""),
            "",
            "| Component / Function | Failure Mode | S | O | D | RPN | AP | Mitigation Required |",
            "|---|---|---|---|---|---|---|---|",
        ]
        for f in findings:
            ap = f.get("action_priority", "LOW")
            ap_icon = "🔴 HIGH" if ap == "HIGH" else ("🟡 MED" if ap == "MEDIUM" else "🟢 LOW")
            lines.append(
                f"| {f.get('component', '')} / {f.get('function', '')} "
                f"| {f.get('failure_mode', '')} "
                f"| {f.get('s', '?')} | {f.get('o', '?')} | {f.get('d', '?')} "
                f"| {f.get('rpn', '?')} | {ap_icon} | {f.get('mitigation', '')} |"
            )

        axiom_risks = analysis.get("axiom_risks", [])
        if axiom_risks:
            lines += ["", "**Axiom Risk Flags:**"]
            for risk in axiom_risks:
                lines.append(f"- {risk}")

        next_steps = analysis.get("recommended_next_steps", [])
        if next_steps:
            lines += ["", "**Recommended Next Steps:**"]
            for step in next_steps:
                lines.append(f"- {step}")

    lines += [
        "",
        "---",
        "*Action Priority Legend: 🔴 HIGH = RPN ≥ 100 or S ≥ 8 | 🟡 MED = RPN 50–99 | 🟢 LOW = RPN < 50*  ",
        "*S ≥ 9 requires human sign-off before merge.*  ",
        f"*Generated by AGE Engineer — [fmea-agent.config.json](fmea-agent.config.json)*",
    ]

    if has_blocker:
        lines.insert(3, "")
        lines.insert(3, f"> ⛔ **This PR is blocked.** One or more findings have Severity ≥ {auto_block_s}. Human sign-off required before merge.")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="AGE PR FMEA Analyzer")
    parser.add_argument("--diff", required=True, help="Path to PR diff file")
    parser.add_argument("--pr-number", required=True, help="PR number")
    parser.add_argument("--pr-title", required=True, help="PR title")
    parser.add_argument("--output", required=True, help="Output path for comment markdown")
    args = parser.parse_args()

    diff_text = load_diff(args.diff)
    if not diff_text:
        print("Warning: diff file is empty or not found. Generating minimal assessment.", file=sys.stderr)

    critical_warnings = get_critical_system_warnings(diff_text)

    # Try Claude API first, then OpenAI fallback, then rule-based
    analysis = call_claude_api(diff_text, args.pr_title)
    if analysis is None:
        analysis = call_openai_api(diff_text, args.pr_title)
    if analysis is None:
        analysis = fallback_rule_based_analysis(diff_text)

    comment = render_comment(analysis, args.pr_number, args.pr_title, critical_warnings)

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(comment, encoding="utf-8")

    print(f"FMEA comment written to {args.output}")

    # Exit 2 if any finding has severity at auto-block threshold
    config = load_config()
    auto_block_s = config.get("pr_analysis", {}).get("auto_block_severity", 9)
    if any(f.get("s", 0) >= auto_block_s for f in analysis.get("findings", [])):
        print(f"BLOCKING: Finding with S ≥ {auto_block_s} detected.", file=sys.stderr)
        return 2

    return 0


if __name__ == "__main__":
    sys.exit(main())

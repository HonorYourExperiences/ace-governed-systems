"""
saga_analyze.py — SAGA Analyze engine for Phase 2 Issue-Driven Continuous Update.

Reads AUDIT-LOG.md and governed_systems_SOP_PFMEA_DFMEA.md to assess the
Current State, compare it to the Target State anchored in the five core axioms,
identify deltas, and write a structured gap-closing proposal body to stdout
(or a file) for the saga-analyze workflow to post as a GitHub Issue.

Exit codes:
    0  — Analysis complete, proposal output produced.
    1  — Error (missing files, parse failure).
    2  — No significant delta found; no proposal needed.
"""

import json
import os
import re
import sys
from collections import Counter
from datetime import datetime, timezone

# ---------------------------------------------------------------------------
# Paths (relative to repo root, resolved from this script's location)
# ---------------------------------------------------------------------------
REPO_ROOT = os.path.join(os.path.dirname(__file__), "..")
AUDIT_LOG_PATH = os.path.join(REPO_ROOT, "AUDIT-LOG.md")
SOP_PATH = os.path.join(REPO_ROOT, "governed_systems_SOP_PFMEA_DFMEA.md")
OUTPUT_PATH = os.path.join(REPO_ROOT, "docs", "saga-proposal-draft.json")

# ---------------------------------------------------------------------------
# Target State thresholds (anchored in the five core axioms)
# ---------------------------------------------------------------------------
TARGET_REFUSAL_RATE = 10.0          # % — below this is healthy
TARGET_MAX_RPN = 100                # any PFMEA/DFMEA row above triggers delta
TARGET_TOP_REASON_COUNT = 3         # same top reason appearing > N times = gap


def parse_audit_log(path: str) -> dict:
    """Return basic metrics from AUDIT-LOG.md."""
    if not os.path.exists(path):
        return {"total": 0, "refusals": 0, "approvals": 0, "refusal_rate": 0.0, "top_reasons": []}

    with open(path, "r", encoding="utf-8") as fh:
        content = fh.read()

    total = len(re.findall(r"^## Audit:", content, re.MULTILINE))
    refusals = content.count("Allowed: false")
    approvals = content.count("Allowed: true")
    reasons = re.findall(r"Reason: (.+)", content)
    top_reasons = Counter(reasons).most_common(5)

    return {
        "total": total,
        "refusals": refusals,
        "approvals": approvals,
        "refusal_rate": round((refusals / total * 100) if total > 0 else 0.0, 1),
        "top_reasons": [{"reason": r[0], "count": r[1]} for r in top_reasons],
    }


def parse_fmea_rpns(path: str) -> list[dict]:
    """
    Extract rows from the PFMEA and DFMEA tables in the SOP.
    Returns list of dicts with keys: table, step_or_element, failure_mode, rpn, status.
    """
    if not os.path.exists(path):
        return []

    with open(path, "r", encoding="utf-8") as fh:
        content = fh.read()

    rows = []
    # Match markdown table rows that contain a numeric RPN column (9th column)
    pattern = re.compile(
        r"^\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|[^|]*\|[^|]*\|[^|]*\|[^|]*\|[^|]*\|[^|]*\|\s*(\d+)\s*\|[^|]*\|\s*([^|]+?)\s*\|",
        re.MULTILINE,
    )
    for m in pattern.finditer(content):
        step_or_element, failure_mode, rpn_str, status = (
            m.group(1).strip(),
            m.group(2).strip(),
            m.group(3).strip(),
            m.group(4).strip(),
        )
        try:
            rpn = int(rpn_str)
        except ValueError:
            continue  # skip header rows
        if rpn == 0:
            continue  # skip header sentinel
        rows.append(
            {
                "step_or_element": step_or_element,
                "failure_mode": failure_mode,
                "rpn": rpn,
                "status": status,
            }
        )

    return rows


def identify_deltas(audit: dict, fmea_rows: list[dict]) -> list[dict]:
    """
    Compare current state to target state. Return list of delta dicts.
    Each delta has: area, current, target, distance, priority.
    """
    deltas = []

    # Delta 1: Refusal rate
    if audit["total"] > 0:
        rr = audit["refusal_rate"]
        if rr > TARGET_REFUSAL_RATE:
            distance = "High" if rr > 30 else "Medium"
            deltas.append(
                {
                    "area": "Refusal Rate",
                    "current": f"{rr}% ({audit['refusals']} refusals of {audit['total']} total)",
                    "target": f"≤ {TARGET_REFUSAL_RATE}%",
                    "distance": distance,
                    "priority": 1 if rr > 30 else 2,
                }
            )

    # Delta 2: Recurring top reasons
    for item in audit["top_reasons"]:
        if item["count"] > TARGET_TOP_REASON_COUNT:
            deltas.append(
                {
                    "area": "Recurring Refusal Pattern",
                    "current": f"'{item['reason']}' — {item['count']} occurrences",
                    "target": "≤ 3 occurrences of any single reason before gap-closing action",
                    "distance": "Medium-High",
                    "priority": 2,
                }
            )

    # Delta 3: High-RPN FMEA rows still Open
    high_rpn_open = [
        r for r in fmea_rows if r["rpn"] >= TARGET_MAX_RPN and r["status"].lower() == "open"
    ]
    for r in high_rpn_open:
        deltas.append(
            {
                "area": "High-RPN FMEA Row",
                "current": (
                    f"RPN {r['rpn']} — '{r['failure_mode']}' "
                    f"(Step/Element: {r['step_or_element']}) — Status: Open"
                ),
                "target": f"RPN < {TARGET_MAX_RPN} or Status = Closed",
                "distance": "High" if r["rpn"] >= 200 else "Medium",
                "priority": 1 if r["rpn"] >= 200 else 2,
            }
        )

    return sorted(deltas, key=lambda d: d["priority"])


def render_proposal_body(audit: dict, fmea_rows: list[dict], deltas: list[dict]) -> str:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    # Current State section
    current_state_lines = [
        f"- Total audits logged: **{audit['total']}**",
        f"- Refusals: **{audit['refusals']}** ({audit['refusal_rate']}%)",
        f"- Approvals: **{audit['approvals']}**",
    ]
    if audit["top_reasons"]:
        current_state_lines.append("- Top refusal reasons:")
        for item in audit["top_reasons"][:3]:
            current_state_lines.append(f"  - \"{item['reason']}\" × {item['count']}")

    high_rpn = [r for r in fmea_rows if r["rpn"] >= TARGET_MAX_RPN and r["status"].lower() == "open"]
    if high_rpn:
        current_state_lines.append(f"- Open FMEA rows with RPN ≥ {TARGET_MAX_RPN}: **{len(high_rpn)}**")
        for r in high_rpn[:5]:
            current_state_lines.append(f"  - RPN {r['rpn']}: {r['failure_mode']}")

    # Target State section
    target_state = (
        f"- Refusal rate ≤ {TARGET_REFUSAL_RATE}%\n"
        f"- No recurring refusal reason exceeds {TARGET_TOP_REASON_COUNT} occurrences without a closed gap-closing proposal\n"
        f"- All FMEA rows with RPN ≥ {TARGET_MAX_RPN} have a verified gap-closing proposal in progress or are closed\n"
        "- All five core axioms actively evidenced in outputs (especially bydt.org)"
    )

    # Delta section
    delta_lines = []
    for i, d in enumerate(deltas, 1):
        delta_lines.append(
            f"{i}. **{d['area']}**  \n"
            f"   Current: {d['current']}  \n"
            f"   Target: {d['target']}  \n"
            f"   Distance: **{d['distance']}**"
        )

    # Gap-Closing Proposals section
    proposal_lines = []
    for i, d in enumerate(deltas, 1):
        proposal_lines.append(
            f"**Proposal {i} — Close Delta: {d['area']}**\n"
            f"- Which delta: #{i} — {d['area']}\n"
            f"- Preserves all core axioms: Yes\n"
            f"- Success metric (evidence-based): {d['target']} confirmed in next SAGA cycle\n"
            f"- Proposed action: Review FMEA/DFMEA for rows matching this pattern, "
            f"assign owner, update status, and verify closure within 2 cycles."
        )

    body = f"""# SAGA Analyze — Auto-Generated Gap-Closing Proposal ({now})

**Proposal ID:** saga-{now}-auto
**Source:** Scheduled SAGA Analyze (Phase 2 Issue-Driven Continuous Update)
**Preserves Core Axioms:** true

---

## A. Current State Assessment

{chr(10).join(current_state_lines)}

---

## B. Target State Definition

Anchored in the five immutable core axioms (Inherent Sufficiency, Way Through, Witnessing & Mature Presence, Evidence & Capability, Audit Integrity):

{target_state}

---

## C. Delta Identification & Measurement

{chr(10).join(delta_lines) if delta_lines else "_No significant deltas found above threshold._"}

---

## D. Gap-Closing Proposals

{chr(10).join(proposal_lines) if proposal_lines else "_No gap-closing proposals required at this time._"}

---

## Verification Checklist

- [ ] Preserves all five core axioms
- [ ] Does not match any known anti-pattern
- [ ] Explicit success metrics defined above
- [ ] Full audit and lineage will be produced on approval

**Add the `verified` label to this issue once the above checklist is confirmed.**
"""
    return body


def main():
    audit = parse_audit_log(AUDIT_LOG_PATH)
    fmea_rows = parse_fmea_rpns(SOP_PATH)
    deltas = identify_deltas(audit, fmea_rows)

    if not deltas:
        print("No significant deltas found. No proposal needed.", file=sys.stderr)
        # Write an empty output so the workflow step can detect this.
        result = {"has_deltas": False, "proposal_body": "", "delta_count": 0}
        os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
        with open(OUTPUT_PATH, "w", encoding="utf-8") as fh:
            json.dump(result, fh, indent=2)
        sys.exit(2)

    body = render_proposal_body(audit, fmea_rows, deltas)
    result = {
        "has_deltas": True,
        "delta_count": len(deltas),
        "proposal_body": body,
        "refusal_rate": audit["refusal_rate"],
        "high_rpn_open": len(
            [r for r in fmea_rows if r["rpn"] >= TARGET_MAX_RPN and r["status"].lower() == "open"]
        ),
    }

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as fh:
        json.dump(result, fh, indent=2)

    print(f"Analysis complete. {len(deltas)} delta(s) identified. Proposal draft written.")
    sys.exit(0)


if __name__ == "__main__":
    main()

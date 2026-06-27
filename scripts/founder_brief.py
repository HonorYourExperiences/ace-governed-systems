#!/usr/bin/env python3
"""
AGE Founder Decision Brief

Surfaces exactly what requires human attention — nothing more — in plain language
with direct action links and estimated effort per item.

Three tiers:
  🔴 BLOCKING  — AGE is stopped waiting for you. Act to unblock.
  🟡 PENDING   — AGE has done the work. Your review or decision needed.
  🟢 RUNNING   — AGE is handling. No action needed.

Creates or updates a single GitHub issue labeled `founder-brief`. Running it again
always updates the same issue — never creates duplicates.

Usage:
  python3 scripts/founder_brief.py [--dry-run] [--output FILE]

Required env vars (when posting to GitHub):
  GITHUB_TOKEN       — repo token with issues:write and actions:read scope
  GITHUB_REPOSITORY  — "owner/repo" (auto-set in GitHub Actions)
"""

import argparse
import json
import os
import re
import sys
import urllib.request
import urllib.error
import urllib.parse
from datetime import datetime, timezone
from pathlib import Path

CONFIG_PATH = Path(__file__).parent.parent / "fmea-agent.config.json"
SOP_PATH = Path(__file__).parent.parent / "governed_systems_SOP_PFMEA_DFMEA.md"
PROPOSALS_DIR = Path(__file__).parent.parent / "proposals"
BRIEF_LABEL = "founder-brief"
BRIEF_TITLE = "🧭 Founder Decision Brief"


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

def load_config() -> dict:
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH) as f:
            return json.load(f)
    return {}


# ---------------------------------------------------------------------------
# Time utilities
# ---------------------------------------------------------------------------

def days_since(iso_str: str) -> int:
    if not iso_str:
        return 0
    try:
        dt = datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
        return (datetime.now(timezone.utc) - dt).days
    except Exception:
        return 0


def age_label(days: int) -> str:
    if days == 0:
        return ""
    if days == 1:
        return " · *1 day open*"
    return f" · *{days} days open*"


# ---------------------------------------------------------------------------
# FMEA table parser
# ---------------------------------------------------------------------------

def clean_status(raw: str) -> str:
    return raw.split("<!--")[0].strip().rstrip("|").strip()


def safe_int(s: str) -> int:
    try:
        return int(s.split("<!--")[0].strip())
    except Exception:
        return 0


def parse_fmea_rows() -> list[dict]:
    """
    Parse PFMEA and DFMEA rows from the SOP file.
    Handles Status cells that embed | inside HTML comments (evidence notes).
    """
    if not SOP_PATH.exists():
        return []

    text = SOP_PATH.read_text(encoding="utf-8", errors="replace")
    rows: list[dict] = []
    in_pfmea = False
    in_dfmea = False

    for line in text.splitlines():
        stripped = line.strip()

        # Exit table mode on any new section heading
        if stripped.startswith("## "):
            in_pfmea = False
            in_dfmea = False

        # Detect PFMEA/DFMEA table headers (presence of RPN + Status is the reliable key)
        if "Process Step" in stripped and "RPN" in stripped and "Status" in stripped:
            in_pfmea = True
            in_dfmea = False
            continue
        if "Design Element" in stripped and "RPN" in stripped and "Status" in stripped:
            in_dfmea = True
            in_pfmea = False
            continue

        if not (in_pfmea or in_dfmea):
            continue
        if not stripped.startswith("|"):
            continue
        if "|---" in stripped or "| ---" in stripped:
            continue

        # Split on | and remove leading/trailing empty parts
        parts = [p.strip() for p in stripped.split("|")]
        if parts and parts[0] == "":
            parts = parts[1:]
        if parts and parts[-1] == "":
            parts = parts[:-1]

        # PFMEA/DFMEA data rows have 11 columns (0-10); Status may have embedded |
        if len(parts) < 11:
            continue

        # Skip header repetitions
        if parts[0] in ("Process Step", "Design Element"):
            continue

        # Column layout (0-indexed):
        # 0: step/element  1: failure_mode  2: effect  3: S  4: cause
        # 5: O  6: controls  7: D  8: RPN  9: action  10+: Status (may span multiple | )
        rpn = safe_int(parts[8])
        if rpn == 0:
            continue

        status_raw = "|".join(parts[10:]).strip()
        status = clean_status(status_raw)
        if not status or status == "Status":
            continue

        row = {
            "table": "pfmea" if in_pfmea else "dfmea",
            "step_or_element": parts[0],
            "failure_mode": parts[1],
            "effect": parts[2],
            "s": safe_int(parts[3]),
            "o": safe_int(parts[5]),
            "d": safe_int(parts[7]),
            "rpn": rpn,
            "action": parts[9],
            "status": status,
        }
        row["tier"] = (
            "CRITICAL" if rpn >= 150 else
            "HIGH" if rpn >= 100 else
            "MONITOR"
        )
        rows.append(row)

    return sorted(rows, key=lambda r: -r["rpn"])


# ---------------------------------------------------------------------------
# Proposal scanner
# ---------------------------------------------------------------------------

def scan_proposals() -> list[dict]:
    if not PROPOSALS_DIR.exists():
        return []

    proposals = []
    for f in sorted(PROPOSALS_DIR.glob("prop-AGE-*.md")):
        try:
            text = f.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue

        prop: dict = {"file": f.name}

        m = re.search(r"\*\*Proposal ID:\*\*\s*(\S+)", text)
        if m:
            prop["id"] = m.group(1)

        m = re.search(r"\*\*Source:\*\*.*?FMEA row:\s*(.+?)$", text, re.MULTILINE)
        if m:
            prop["source_row"] = m.group(1).strip()

        triggers = re.findall(r"- \[( |x|X)\]", text)
        checked = sum(1 for t in triggers if t.lower() == "x")
        prop["triggers_total"] = len(triggers)
        prop["triggers_checked"] = checked
        prop["complete"] = (checked == len(triggers) and len(triggers) > 0)

        proposals.append(prop)

    return proposals


# ---------------------------------------------------------------------------
# GitHub API helpers
# ---------------------------------------------------------------------------

def gh_get(path: str, token: str) -> list | dict | None:
    if not token:
        return None
    try:
        req = urllib.request.Request(
            f"https://api.github.com{path}",
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
            },
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        print(f"  GitHub GET {path}: {e}", file=sys.stderr)
        return None


def gh_post(path: str, payload: dict, token: str, method: str = "POST") -> dict | None:
    if not token:
        return None
    try:
        req = urllib.request.Request(
            f"https://api.github.com{path}",
            data=json.dumps(payload).encode("utf-8"),
            method=method,
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
                "Content-Type": "application/json",
            },
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        print(f"  GitHub {method} {path}: {e}", file=sys.stderr)
        return None


def get_open_prs(owner: str, repo: str, token: str) -> list:
    result = gh_get(f"/repos/{owner}/{repo}/pulls?state=open&per_page=50", token)
    return result if isinstance(result, list) else []


def get_issues_by_label(label: str, owner: str, repo: str, token: str) -> list:
    result = gh_get(
        f"/repos/{owner}/{repo}/issues?labels={label}&state=open&per_page=50", token
    )
    return result if isinstance(result, list) else []


def get_workflow_runs(owner: str, repo: str, token: str) -> list:
    result = gh_get(f"/repos/{owner}/{repo}/actions/runs?per_page=30", token)
    if isinstance(result, dict):
        return result.get("workflow_runs", [])
    return []


def ensure_label(name: str, color: str, description: str, owner: str, repo: str, token: str):
    encoded = urllib.parse.quote(name, safe="")
    existing = gh_get(f"/repos/{owner}/{repo}/labels/{encoded}", token)
    if existing and isinstance(existing, dict) and "name" in existing:
        return
    gh_post(
        f"/repos/{owner}/{repo}/labels",
        {"name": name, "color": color, "description": description},
        token,
    )


def find_existing_brief(owner: str, repo: str, token: str) -> dict | None:
    issues = gh_get(
        f"/repos/{owner}/{repo}/issues?labels={BRIEF_LABEL}&state=open&per_page=5",
        token,
    )
    if isinstance(issues, list) and issues:
        return issues[0]
    return None


def create_or_update_brief(body: str, owner: str, repo: str, token: str) -> str:
    ensure_label(
        BRIEF_LABEL, "0075ca",
        "Auto-updated Founder Decision Brief — check here for what needs your attention",
        owner, repo, token,
    )
    existing = find_existing_brief(owner, repo, token)
    if existing:
        result = gh_post(
            f"/repos/{owner}/{repo}/issues/{existing['number']}",
            {"title": BRIEF_TITLE, "body": body},
            token,
            method="PATCH",
        )
        return (result or {}).get("html_url", existing["html_url"])
    else:
        result = gh_post(
            f"/repos/{owner}/{repo}/issues",
            {"title": BRIEF_TITLE, "body": body, "labels": [BRIEF_LABEL]},
            token,
        )
        return (result or {}).get("html_url", "")


# ---------------------------------------------------------------------------
# Analysis helpers
# ---------------------------------------------------------------------------

def classify_pr(pr: dict) -> dict:
    title = (pr.get("title") or "").lower()
    is_draft = pr.get("draft", False)
    is_bot = (pr.get("user") or {}).get("type") == "Bot"

    if any(k in title for k in ("policy", "sop", "fmea", "axiom", "governance")):
        return {"kind": "policy", "est": "~3 min",
                "guidance": "Adds or changes a governance rule — check it matches intent"}
    if any(k in title for k in ("chore", "workbench", "report")):
        return {"kind": "bookkeeping", "est": "~1 min",
                "guidance": "Bookkeeping update — verify counts look right"}
    if is_bot and is_draft:
        return {"kind": "copilot-draft", "est": "~2 min",
                "guidance": "Copilot is working on this — may still be in progress"}
    return {"kind": "general", "est": "~2 min",
            "guidance": "Review diff for correctness before merging"}


def workflow_health(runs: list) -> list[dict]:
    seen: dict[str, dict] = {}
    for run in runs:
        name = run.get("name", "Unknown")
        if name not in seen:
            conclusion = run.get("conclusion") or run.get("status") or "unknown"
            seen[name] = {
                "name": name,
                "conclusion": conclusion,
                "icon": "✅" if conclusion == "success" else
                        "❌" if conclusion == "failure" else "⏳",
                "age": days_since(run.get("updated_at", "")),
                "url": run.get("html_url", ""),
            }
    return list(seen.values())


def rpn_stats(rows: list[dict]) -> dict:
    open_rows = [r for r in rows if r["status"] not in ("Closed", "Superseded")]
    return {
        "total": sum(r["rpn"] for r in open_rows),
        "open": len(open_rows),
        "critical": sum(1 for r in open_rows if r["tier"] == "CRITICAL"),
        "high": sum(1 for r in open_rows if r["tier"] == "HIGH"),
        "monitor": sum(1 for r in open_rows if r["tier"] == "MONITOR"),
        "open_rows": open_rows,
    }


def heat_bar(filled: int, total: int, width: int = 10) -> str:
    if total == 0:
        return "░" * width
    n = round((filled / total) * width)
    return "█" * n + "░" * (width - n)


# ---------------------------------------------------------------------------
# Brief renderer
# ---------------------------------------------------------------------------

def render_brief(
    fmea_rows: list[dict],
    proposals: list[dict],
    open_prs: list[dict],
    escalation_issues: list[dict],
    needs_verification: list[dict],
    overdue_issues: list[dict],
    wf_runs: list[dict],
    repo_url: str,
    today: str,
) -> str:
    stats = rpn_stats(fmea_rows)
    open_rows = stats["open_rows"]
    config = load_config()
    critical_floor = config.get("risk_thresholds", {}).get("critical_rpn_floor", 150)

    blocking: list[dict] = []
    pending: list[dict] = []
    running: list[dict] = []

    # --- BLOCKING: escalation issues (AGE is stopped) ---
    for issue in escalation_issues:
        blocking.append({
            "icon": "🚨", "est": "~5 min",
            "title": issue["title"],
            "context": (issue.get("body") or "")[:180].replace("\n", " ").strip() + "…",
            "why": "AGE raised a hard escalation and cannot proceed until you respond.",
            "consequence": "AGE is paused on the affected row until this is resolved.",
            "actions": [("Read escalation and respond →", issue["html_url"])],
            "age": days_since(issue.get("created_at", "")),
        })

    # --- BLOCKING: overdue-critical issues ---
    for issue in overdue_issues:
        blocking.append({
            "icon": "⏰", "est": "~3 min",
            "title": issue["title"],
            "context": f"A Critical FMEA row has been open >14 days without triage.",
            "why": "AGE rule: Critical rows open >14 days require human triage before AGE can design solutions.",
            "consequence": "AGE cannot design a solution for this row until you triage it.",
            "actions": [
                ('Post "AGE: proceed" on the issue to assign it →', issue["html_url"]),
                ('Post "AGE: accept risk — [reason]" to acknowledge and close →', issue["html_url"]),
            ],
            "age": days_since(issue.get("created_at", "")),
        })

    # --- BLOCKING: Critical rows still Open/Triaged with no overdue issue yet ---
    overdue_failure_modes = {
        re.sub(r".*Critical FMEA row:\s*", "", i["title"]).strip()
        for i in overdue_issues
    }
    for row in open_rows:
        if row["tier"] == "CRITICAL" and row["status"] in ("Open", "Triaged"):
            if row["failure_mode"] not in overdue_failure_modes:
                blocking.append({
                    "icon": "🔴", "est": "~2 min",
                    "title": f"Critical row needs triage: {row['failure_mode']}",
                    "context": (
                        f"RPN {row['rpn']} | {row['table'].upper()} | "
                        f"{row['step_or_element']} | Status: {row['status']}"
                    ),
                    "why": (
                        f"RPN {row['rpn']} — top severity tier. "
                        "If open >14 days AGE will auto-escalate."
                    ),
                    "consequence": (
                        "Nothing blocks AGE yet, but this row is accumulating staleness."
                    ),
                    "actions": [
                        ("View FMEA table →",
                         f"{repo_url}/blob/main/governed_systems_SOP_PFMEA_DFMEA.md"),
                    ],
                    "age": 0,
                })

    # --- PENDING: open PRs ---
    for pr in open_prs:
        # Skip the founder-brief PR if it somehow appears
        if BRIEF_LABEL in [l.get("name", "") for l in (pr.get("labels") or [])]:
            continue
        meta = classify_pr(pr)
        note = " *(draft)*" if pr.get("draft") else ""
        changed = pr.get("changed_files", 0)
        additions = pr.get("additions", 0)
        pending.append({
            "icon": "🔀", "est": meta["est"],
            "title": f"PR #{pr['number']}{note} — {pr['title']}",
            "context": meta["guidance"],
            "why": f"{additions} line(s) added across {changed} file(s).",
            "actions": [
                ("Review →", pr["html_url"]),
                ("Merge →", pr["html_url"]),
            ],
            "age": days_since(pr.get("created_at", "")),
        })

    # --- PENDING: needs-verification issues ---
    for issue in needs_verification:
        is_spof = "[FMEA-Risk]" in issue["title"]
        if is_spof:
            pending.append({
                "icon": "⚠️", "est": "~3 min",
                "title": issue["title"],
                "context": "AGE SPOF scanner found a potential single-point-of-failure.",
                "why": "Review findings, add redundancy or document risk acceptance.",
                "actions": [
                    ("Review findings →", issue["html_url"]),
                    ("Add `verified` label once resolved →", issue["html_url"]),
                ],
                "age": days_since(issue.get("created_at", "")),
            })
        else:
            pending.append({
                "icon": "✅", "est": "~5 min",
                "title": issue["title"],
                "context": "A solution was proposed and implemented. Needs your sign-off.",
                "why": "AGE cannot mark a row Closed without human verification.",
                "actions": [
                    ("Review checklist →", issue["html_url"]),
                    ("Add `verified` label to approve →", issue["html_url"]),
                ],
                "age": days_since(issue.get("created_at", "")),
            })

    # --- RUNNING: In Progress or Solution Designed rows ---
    for row in open_rows:
        status = row["status"]
        if "In Progress" in status:
            running.append({
                "icon": "🔧",
                "text": (
                    f"**{row['failure_mode']}** "
                    f"(RPN {row['rpn']}) — AGE actively designing solution"
                ),
            })
        elif "Solution Designed" in status:
            running.append({
                "icon": "📋",
                "text": (
                    f"**{row['failure_mode']}** "
                    f"(RPN {row['rpn']}) — Solution designed, pending your verification"
                ),
            })

    wf_health = workflow_health(wf_runs)

    # -----------------------------------------------------------------------
    # Render markdown
    # -----------------------------------------------------------------------
    lines: list[str] = []

    # Header
    trigger_url = f"{repo_url}/actions/workflows/founder-brief.yml"
    lines += [
        f"# 🧭 Founder Decision Brief",
        f"",
        (
            f"*{today} · Generated by AGE · "
            f"[Trigger a refresh]({trigger_url}) (Actions → founder-brief → Run workflow)*"
        ),
        f"",
        "---",
        "",
    ]

    # System snapshot
    bar = heat_bar(stats["critical"], stats["open"])
    lines += [
        "## System at a Glance",
        "",
        f"| | |",
        f"|---|---|",
        f"| Open FMEA rows | "
        f"**{stats['open']}** total "
        f"({stats['critical']} Critical · {stats['high']} High · {stats['monitor']} Monitor) |",
        f"| Total RPN heat | **{stats['total']}** |",
        f"| Critical coverage | `{bar}` {stats['critical']} of {stats['open']} rows are Critical |",
        f"| Proposals filed | {len(proposals)} |",
        "",
        "---",
        "",
    ]

    # 🔴 BLOCKING
    if blocking:
        lines += [
            "## 🔴 Action Required — AGE Is Waiting",
            "",
            "*AGE cannot proceed on these items until you act.*",
            "",
        ]
        for i, item in enumerate(blocking, 1):
            lines += [
                f"### {i}. {item['icon']} [{item['est']}]{age_label(item['age'])} &nbsp; {item['title']}",
                "",
                item["context"],
                "",
                f"**Why it matters:** {item['why']}",
                "",
            ]
            if item.get("consequence"):
                lines += [f"> {item['consequence']}", ""]
            lines += ["**Your options:**", ""]
            for label, url in item["actions"]:
                lines.append(f"- **[{label}]({url})**")
            lines.append("")
    else:
        lines += [
            "## 🔴 Action Required",
            "",
            "✅ Nothing blocking AGE right now.",
            "",
        ]

    lines += ["---", ""]

    # 🟡 PENDING
    if pending:
        lines += [
            "## 🟡 Ready for Your Decision",
            "",
            "*AGE or Copilot has done the work. You just need to say yes or no.*",
            "",
        ]
        for i, item in enumerate(pending, 1):
            lines += [
                f"### {i}. {item['icon']} [{item['est']}]{age_label(item['age'])} &nbsp; {item['title']}",
                "",
                item["context"],
                "",
                f"*{item['why']}*",
                "",
            ]
            for label, url in item["actions"]:
                lines.append(f"- **[{label}]({url})**")
            lines.append("")
    else:
        lines += [
            "## 🟡 Ready for Your Decision",
            "",
            "✅ Nothing waiting for your review right now.",
            "",
        ]

    lines += ["---", ""]

    # 🟢 RUNNING
    lines += [
        "## 🟢 AGE Is Handling — No Action Needed",
        "",
    ]
    if running:
        for item in running:
            lines.append(f"- {item['icon']} {item['text']}")
        lines.append("")
    else:
        open_count = len([r for r in open_rows
                          if r["status"] not in ("In Progress", "Solution Designed",
                                                  "Verified", "Closed", "Superseded")])
        lines += [
            f"*{open_count} row(s) in Open/Triaged state — AGE will pick these up in the next session.*",
            "",
        ]

    # Workflow health
    if wf_health:
        lines += ["**Recent workflow runs:**", ""]
        for wf in wf_health[:6]:
            age_s = f" ({wf['age']}d ago)" if wf["age"] else ""
            lines.append(
                f"- {wf['icon']} [{wf['name']}]({wf['url']}){age_s} — `{wf['conclusion']}`"
            )
        lines.append("")

    lines += ["---", ""]

    # Quick reference
    fmea_url = f"{repo_url}/blob/main/governed_systems_SOP_PFMEA_DFMEA.md"
    workbench_url = f"{repo_url}/blob/main/AGE-WORKBENCH.md"
    proposals_url = f"{repo_url}/tree/main/proposals"
    all_issues_url = f"{repo_url}/issues"

    lines += [
        "## 📋 Quick Reference",
        "",
        "| Label | What it means | Your action |",
        "|---|---|---|",
        "| `needs-verification` | Solution was proposed and built | Review → add `verified` label |",
        "| `age-escalation` | AGE hit a hard stop | Read the issue → respond to unblock |",
        "| `overdue-critical` | Critical row open >14 days | Triage: tell AGE to proceed or accept risk |",
        "| `fmea-risk` | AGE found a risk in a PR or doc | Review the findings |",
        "| `spof` | Single point of failure detected | Add redundancy or document risk acceptance |",
        "| `founder-brief` | This issue | No action — informational |",
        "",
        f"**Navigate:** "
        f"[FMEA Table]({fmea_url}) · "
        f"[AGE Workbench]({workbench_url}) · "
        f"[Proposals]({proposals_url}) · "
        f"[All Issues]({all_issues_url})",
        "",
        "---",
        "",
        f"*This issue is updated automatically each Monday at 09:00 UTC, or on demand via "
        f"[Actions → founder-brief → Run workflow]({trigger_url}).*",
    ]

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(description="AGE Founder Decision Brief")
    parser.add_argument("--dry-run", action="store_true",
                        help="Print to stdout; do not post to GitHub")
    parser.add_argument("--output", metavar="FILE",
                        help="Write brief to FILE instead of posting")
    args = parser.parse_args()

    token = os.environ.get("GITHUB_TOKEN", "")
    github_repo = os.environ.get("GITHUB_REPOSITORY", "")
    if "/" in github_repo:
        owner, repo = github_repo.split("/", 1)
    else:
        owner = repo = ""

    repo_url = (f"https://github.com/{owner}/{repo}" if owner
                else "https://github.com")
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    print("Parsing FMEA rows…", file=sys.stderr)
    fmea_rows = parse_fmea_rows()
    proposals = scan_proposals()
    print(f"  {len(fmea_rows)} rows · {len(proposals)} proposals", file=sys.stderr)

    open_prs: list = []
    escalation_issues: list = []
    needs_verification: list = []
    overdue_issues: list = []
    wf_runs: list = []

    if token and owner and repo:
        print(f"Fetching GitHub data for {owner}/{repo}…", file=sys.stderr)
        open_prs = get_open_prs(owner, repo, token)
        escalation_issues = get_issues_by_label("age-escalation", owner, repo, token)
        needs_verification = get_issues_by_label("needs-verification", owner, repo, token)
        overdue_issues = get_issues_by_label("overdue-critical", owner, repo, token)
        wf_runs = get_workflow_runs(owner, repo, token)
        print(
            f"  {len(open_prs)} open PRs · "
            f"{len(escalation_issues)} escalations · "
            f"{len(needs_verification)} needs-verification",
            file=sys.stderr,
        )
    else:
        print(
            "No GITHUB_TOKEN / GITHUB_REPOSITORY — skipping GitHub API (dry-run data only).",
            file=sys.stderr,
        )

    brief = render_brief(
        fmea_rows=fmea_rows,
        proposals=proposals,
        open_prs=open_prs,
        escalation_issues=escalation_issues,
        needs_verification=needs_verification,
        overdue_issues=overdue_issues,
        wf_runs=wf_runs,
        repo_url=repo_url,
        today=today,
    )

    if args.output:
        Path(args.output).write_text(brief, encoding="utf-8")
        print(f"Brief written to {args.output}", file=sys.stderr)
        return 0

    if args.dry_run or not (token and owner and repo):
        print(brief)
        return 0

    print("Posting to GitHub…", file=sys.stderr)
    url = create_or_update_brief(brief, owner, repo, token)
    print(f"Brief posted/updated: {url}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

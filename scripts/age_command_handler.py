#!/usr/bin/env python3
"""
AGE Issue Comment Command Handler

Listens for AGE commands posted as issue comments and executes them:

  age:proceed              — Triage row; signal AGE to design a solution
  age:accept risk [reason] — Accept the risk; document rationale; close escalation
  age:verified             — Confirm solution verified; mark row Verified

The @claude prefix is optional: "@claude age:proceed" works the same as "age:proceed".
Commands are case-insensitive.

Called by .github/workflows/age-command-handler.yml on issue_comment events.

Required env vars:
  GITHUB_TOKEN       — issues:write + contents:write scope
  GITHUB_REPOSITORY  — "owner/repo"
  ISSUE_NUMBER       — issue number the comment is on
  ISSUE_TITLE        — issue title
  ISSUE_BODY         — issue body
  COMMENT_BODY       — comment text
  COMMENTER          — GitHub login of commenter

Exit codes: 0=handled, 1=error, 2=no recognized command / not applicable
"""

import json
import os
import re
import subprocess
import sys
import urllib.request
import urllib.parse
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
SOP_PATH = REPO_ROOT / "governed_systems_SOP_PFMEA_DFMEA.md"
AGE_ENGINEER = REPO_ROOT / "scripts" / "age_engineer.py"

VALID_STATUSES = {"Open", "Triaged", "In Progress", "Solution Designed", "Verified"}


# ---------------------------------------------------------------------------
# Command parsing
# ---------------------------------------------------------------------------

def parse_command(body: str) -> dict | None:
    """
    Extract an AGE command from a comment body.
    Returns {cmd, reason} or None if no command found.
    """
    # Strip @mentions and normalize whitespace
    normalized = re.sub(r"@\w+\s*", "", body, flags=re.IGNORECASE).strip()

    # age:proceed
    if re.match(r"age\s*:\s*proceed", normalized, re.IGNORECASE):
        return {"cmd": "proceed", "reason": ""}

    # age:verified
    if re.match(r"age\s*:\s*verified", normalized, re.IGNORECASE):
        return {"cmd": "verified", "reason": ""}

    # age:accept risk [reason]
    m = re.match(r"age\s*:\s*accept[\s\-]+risk\s*[—\-]?\s*(.*)", normalized, re.IGNORECASE | re.DOTALL)
    if m:
        return {"cmd": "accept_risk", "reason": m.group(1).strip()[:300]}

    return None


# ---------------------------------------------------------------------------
# FMEA context extraction from issue
# ---------------------------------------------------------------------------

def parse_fmea_context(title: str, body: str) -> dict | None:
    """
    Extract FMEA row coordinates from an issue created by age-engineer.yml.

    Overdue-critical issues contain:
      **Table:** DFMEA
      **Process Step / Design Element:** Verification Pipeline
      **Failure Mode:** No automated gate…
      **RPN:** 160
    """
    ctx: dict = {}

    m = re.search(r"\*\*Table:\*\*\s*(\w+)", body)
    if m:
        ctx["table"] = m.group(1).lower()

    m = re.search(r"\*\*Process Step / Design Element:\*\*\s*(.+?)$", body, re.MULTILINE)
    if m:
        ctx["step"] = m.group(1).strip()

    m = re.search(r"\*\*Failure Mode:\*\*\s*(.+?)$", body, re.MULTILINE)
    if m:
        ctx["failure_mode"] = m.group(1).strip()

    m = re.search(r"\*\*RPN:\*\*\s*(\d+)", body)
    if m:
        ctx["rpn"] = int(m.group(1))

    m = re.search(r"\*\*Current Status:\*\*\s*(.+?)$", body, re.MULTILINE)
    if m:
        ctx["current_status"] = m.group(1).strip()

    # Fallback: extract failure mode from title pattern
    if "failure_mode" not in ctx:
        cleaned = re.sub(r"^\[AGE-OVERDUE\]\s*Critical FMEA row:\s*", "", title).strip()
        if cleaned != title:
            ctx["failure_mode"] = cleaned

    # Require at minimum a failure mode to act
    if "failure_mode" not in ctx:
        return None

    # Default table to pfmea if not found
    ctx.setdefault("table", "pfmea")
    ctx.setdefault("step", "")

    return ctx


# ---------------------------------------------------------------------------
# age_engineer.py wrapper
# ---------------------------------------------------------------------------

def update_fmea_status(table: str, step: str, failure: str, status: str, note: str) -> tuple[bool, str]:
    """
    Call age_engineer.py update-status. Returns (success, output).
    """
    cmd = [
        sys.executable, str(AGE_ENGINEER), "update-status",
        "--table", table,
        "--step", step,
        "--failure", failure,
        "--status", status,
        "--note", note,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=str(REPO_ROOT))
    output = (result.stdout + result.stderr).strip()
    return result.returncode == 0, output


# ---------------------------------------------------------------------------
# GitHub API helpers
# ---------------------------------------------------------------------------

def gh_post(path: str, payload: dict, token: str, method: str = "POST") -> dict | None:
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


def post_comment(issue_number: int, body: str, token: str, owner: str, repo: str):
    gh_post(f"/repos/{owner}/{repo}/issues/{issue_number}/comments", {"body": body}, token)


def close_issue(issue_number: int, token: str, owner: str, repo: str):
    gh_post(
        f"/repos/{owner}/{repo}/issues/{issue_number}",
        {"state": "closed", "state_reason": "completed"},
        token, method="PATCH",
    )


def add_label(issue_number: int, label: str, token: str, owner: str, repo: str):
    gh_post(f"/repos/{owner}/{repo}/issues/{issue_number}/labels", {"labels": [label]}, token)


def ensure_label_exists(name: str, color: str, desc: str, token: str, owner: str, repo: str):
    encoded = urllib.parse.quote(name, safe="")
    try:
        req = urllib.request.Request(
            f"https://api.github.com/repos/{owner}/{repo}/labels/{encoded}",
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
            },
        )
        with urllib.request.urlopen(req, timeout=10):
            return  # already exists
    except Exception:
        pass
    gh_post(f"/repos/{owner}/{repo}/labels", {"name": name, "color": color, "description": desc}, token)


# ---------------------------------------------------------------------------
# Command handlers
# ---------------------------------------------------------------------------

REPO_URL_TEMPLATE = "https://github.com/{owner}/{repo}"


def handle_proceed(ctx: dict, commenter: str, issue_number: int,
                   token: str, owner: str, repo: str) -> int:
    failure = ctx["failure_mode"]
    table = ctx["table"]
    step = ctx.get("step", "")
    rpn = ctx.get("rpn", "?")
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    repo_url = REPO_URL_TEMPLATE.format(owner=owner, repo=repo)

    note = f"Triaged by @{commenter} via issue #{issue_number} comment (age:proceed) on {today}"
    ok, output = update_fmea_status(table, step, failure, "Triaged", note)

    if ok:
        reply = (
            f"✅ **AGE: Triage signal received.**\n\n"
            f"Row **{failure}** (RPN {rpn}) has been moved to `Triaged`.\n\n"
            f"**What happens next:**\n"
            f"- AGE will design a solution in the next session\n"
            f"- A proposal file will appear in `proposals/` when solution is designed\n"
            f"- The row moves `In Progress → Solution Designed → Verified`\n"
            f"- You confirm Verified with `age:verified` or by adding the `verified` label\n\n"
            f"**Track progress:** "
            f"[AGE Workbench]({repo_url}/blob/main/AGE-WORKBENCH.md) · "
            f"[FMEA Table]({repo_url}/blob/main/governed_systems_SOP_PFMEA_DFMEA.md)"
        )
    else:
        reply = (
            f"⚠️ **AGE: Triage signal received, but FMEA update failed.**\n\n"
            f"Could not update row **{failure}** automatically.\n\n"
            f"```\n{output}\n```\n\n"
            f"The row may need to be updated manually in "
            f"[governed_systems_SOP_PFMEA_DFMEA.md]({repo_url}/blob/main/governed_systems_SOP_PFMEA_DFMEA.md)."
        )

    post_comment(issue_number, reply, token, owner, repo)
    return 0 if ok else 1


def handle_accept_risk(ctx: dict, reason: str, commenter: str, issue_number: int,
                       token: str, owner: str, repo: str) -> int:
    failure = ctx["failure_mode"]
    table = ctx["table"]
    step = ctx.get("step", "")
    rpn = ctx.get("rpn", "?")
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    repo_url = REPO_URL_TEMPLATE.format(owner=owner, repo=repo)

    reason_text = reason if reason else "no reason provided"
    note = (
        f"Risk accepted by @{commenter} on {today} via issue #{issue_number}. "
        f"Rationale: {reason_text}. No mitigation planned."
    )
    ok, output = update_fmea_status(table, step, failure, "Open", note)

    if ok:
        reply = (
            f"📋 **AGE: Risk acceptance recorded.**\n\n"
            f"Row **{failure}** (RPN {rpn}) — risk accepted by @{commenter}.\n\n"
            f"**Rationale:** {reason_text}\n\n"
            f"The FMEA row remains in the table with an evidence note. "
            f"This escalation issue will be closed.\n\n"
            f"> If circumstances change and mitigation becomes necessary, "
            f"reopen this issue or create a new escalation."
        )
        close_issue(issue_number, token, owner, repo)
    else:
        reply = (
            f"⚠️ **AGE: Risk acceptance noted, but FMEA update failed.**\n\n"
            f"Could not update row **{failure}** automatically.\n\n"
            f"```\n{output}\n```"
        )

    post_comment(issue_number, reply, token, owner, repo)
    return 0 if ok else 1


def handle_verified(ctx: dict, commenter: str, issue_number: int,
                    token: str, owner: str, repo: str) -> int:
    failure = ctx["failure_mode"]
    table = ctx["table"]
    step = ctx.get("step", "")
    rpn = ctx.get("rpn", "?")
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    repo_url = REPO_URL_TEMPLATE.format(owner=owner, repo=repo)

    note = (
        f"Verified by @{commenter} on {today} via issue #{issue_number} comment (age:verified). "
        f"Human confirmation of solution implementation."
    )
    ok, output = update_fmea_status(table, step, failure, "Verified", note)

    if ok:
        ensure_label_exists("verified", "0e8a16", "Human-confirmed solution", token, owner, repo)
        add_label(issue_number, "verified", token, owner, repo)

        reply = (
            f"✅ **AGE: Row marked Verified.**\n\n"
            f"Row **{failure}** (RPN {rpn}) is now `Verified`.\n\n"
            f"**Final step — Closed transition (human-only):**\n"
            f"1. Confirm the solution is working as expected\n"
            f"2. Append a closure row via `pfmea_append.py` with reduced S/O/D values\n"
            f"3. Update the original row status to `Closed` in the FMEA table\n\n"
            f"The `verified` label has been added to this issue. "
            f"AGE will handle the Closed transition in the next session once the label is present.\n\n"
            f"[View FMEA Table]({repo_url}/blob/main/governed_systems_SOP_PFMEA_DFMEA.md)"
        )
    else:
        reply = (
            f"⚠️ **AGE: Verification noted, but FMEA update failed.**\n\n"
            f"Could not update row **{failure}** to Verified automatically.\n\n"
            f"```\n{output}\n```"
        )

    post_comment(issue_number, reply, token, owner, repo)
    return 0 if ok else 1


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    token = os.environ.get("GITHUB_TOKEN", "")
    github_repo = os.environ.get("GITHUB_REPOSITORY", "")
    issue_number = int(os.environ.get("ISSUE_NUMBER", "0"))
    issue_title = os.environ.get("ISSUE_TITLE", "")
    issue_body = os.environ.get("ISSUE_BODY", "")
    comment_body = os.environ.get("COMMENT_BODY", "")
    commenter = os.environ.get("COMMENTER", "unknown")

    if not all([token, github_repo, issue_number, comment_body]):
        print("ERROR: Missing required env vars.", file=sys.stderr)
        return 1

    owner, repo = github_repo.split("/", 1) if "/" in github_repo else ("", "")

    # Parse command
    command = parse_command(comment_body)
    if command is None:
        print(f"No AGE command found in comment: {comment_body[:80]!r}", file=sys.stderr)
        return 2

    print(f"Command: {command['cmd']} | Issue #{issue_number} | Commenter: @{commenter}")

    # Parse FMEA context from issue
    ctx = parse_fmea_context(issue_title, issue_body)
    if ctx is None:
        msg = (
            f"⚠️ **AGE: Command `{command['cmd']}` received but could not identify FMEA row.**\n\n"
            f"This issue does not contain the expected FMEA row fields "
            f"(Table / Process Step / Failure Mode).\n\n"
            f"To act on a specific row, open a Claude Code session and reference this issue directly."
        )
        post_comment(issue_number, msg, token, owner, repo)
        return 1

    print(f"FMEA context: [{ctx['table'].upper()}] {ctx.get('step', '?')} / {ctx['failure_mode']}")

    # Dispatch
    cmd = command["cmd"]
    if cmd == "proceed":
        return handle_proceed(ctx, commenter, issue_number, token, owner, repo)
    elif cmd == "accept_risk":
        return handle_accept_risk(ctx, command["reason"], commenter, issue_number, token, owner, repo)
    elif cmd == "verified":
        return handle_verified(ctx, commenter, issue_number, token, owner, repo)

    return 1


if __name__ == "__main__":
    sys.exit(main())

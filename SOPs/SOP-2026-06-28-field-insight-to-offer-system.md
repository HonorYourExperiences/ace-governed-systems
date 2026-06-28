# SOP: Field Insight to Offer System

**SOP ID:** SOP-2026-06-28-field-insight-to-offer-system
**Related FMEA Row:** General
**Author:** AGE session 2026-06-28
**Status:** Active

---

## Context

This SOP governs how a live-session observation, founder debrief, customer quote, partner signal, or spontaneous experience-design insight enters the repository.

The purpose is to prevent field learning from staying as memory only. Every meaningful insight should become one of five things:

- source evidence
- session evidence
- decision record
- offer-system update
- future verification target

This protects Evidence & Capability and Audit Integrity while preserving the Way Through principle: the next build comes from what actually happened, not from abstract planning.

---

## Prerequisites

- [ ] The insight has an identifiable source: field session, founder debrief, partner post, customer quote, observation sheet, or artifact.
- [ ] Permission status is known or explicitly marked `pending`.
- [ ] Claims are separated from hypotheses. Do not mark an untested design idea as proven.
- [ ] The working tree has been inspected with `git status --short --branch`.

---

## Steps

1. **Create or update the source card**
   ```bash
   # No command required; edit the relevant source card under:
   # cape-able-heroes/field-evidence/session-[date]-[theme]/
   ```
   Expected output: a source card that names the source URL/file/person, capture date, permission status, evidence signals, and follow-up needed.

2. **Update the session evidence**
   ```bash
   # Edit:
   # cape-able-heroes/SESSION-LOG.md
   ```
   Expected output: the session log includes the observation, what is confirmed, what is still TBD, and supporting file location.

3. **Log decisions, not just events**
   ```bash
   # Edit:
   # cape-able-heroes/DECISION-LOG.md
   ```
   Expected output: any choice that changes the offer, facilitation model, pricing, channel, or product architecture has a date, reason, alternatives considered, and revisit signal.

4. **Route the insight into the right artifact**
   ```bash
   # Examples:
   # cape-able-heroes/AVIATION-WONDERLAB-METHOD.md
   # cape-able-heroes/OUTREACH-TEMPLATES.md
   # cape-able-heroes/TESTIMONIAL-CASE-STUDY.md
   # FOUNDER-WEEKLY-REFLECTION.md
   ```
   Expected output: the insight changes a living system surface, not only a note.

5. **Mark evidence status**
   ```bash
   # No command required; add one of:
   # observed, source-backed, founder-debrief, hypothesis, validated, rejected
   ```
   Expected output: readers can tell what has happened in the field versus what still needs testing.

6. **Run content and governance checks**
   ```bash
   $env:PYTHONIOENCODING='utf-8'; python scripts/scan_content_antipatterns.py --path cape-able-heroes
   $env:PYTHONIOENCODING='utf-8'; python scripts/age_engineer.py preflight
   git diff --check
   ```
   Expected output: scanner passes; preflight has 0 FAIL; `git diff --check` has no whitespace errors.

7. **Commit with evidence language**
   ```bash
   git add [changed-files]
   git commit -m "docs(cape-able): capture [specific field insight]"
   ```
   Expected output: the commit message names the real insight, not a generic docs update.

---

## Verification

Run:

```bash
$env:PYTHONIOENCODING='utf-8'; python scripts/scan_content_antipatterns.py --path cape-able-heroes
$env:PYTHONIOENCODING='utf-8'; python scripts/age_engineer.py preflight
git status --short --branch
```

Expected:

- `scan_content_antipatterns.py` reports no rescue-modeling or aspiration-theater anti-patterns.
- `age_engineer.py preflight` reports `0 FAIL`.
- `git status` shows only intentional files changed before commit, and clean state after commit except local tool state such as `.claude/`.

---

## Turnback Criteria

- If a quote does not have permission, do not place it in public-facing copy. Mark it `permission pending`.
- If the insight changes a core axiom or `IMMUTABLE_VS_MUTABLE_LAYERS.md`, stop and escalate.
- If the insight implies a new paid offer, log a decision before updating outreach or pricing.
- If a field observation is ambiguous, record it as `hypothesis` and add a verification target.
- If preflight returns any FAIL, resolve that failure before pushing.

**Escalation label:** `age-escalation`


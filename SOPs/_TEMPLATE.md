# SOP: [Short Title]

**SOP ID:** SOP-YYYY-MM-DD-[slug]
**Related FMEA Row:** [table] / [step_or_element] / [failure_mode] (or "General")
**Author:** AGE session [date]
**Status:** Active

---

## Context

What problem this SOP addresses. Which FMEA row it relates to, and why this procedure was worth formalizing (e.g., encountered a retry loop, a workaround was required, or a non-obvious sequence was discovered).

---

## Prerequisites

Exact state conditions required before starting this procedure:

- [ ] Condition 1 (e.g., `fmea-agent.config.json` exists and is valid JSON)
- [ ] Condition 2 (e.g., `governed_systems_SOP_PFMEA_DFMEA.md` is readable)
- [ ] Condition 3 (e.g., working on branch `claude/...`, not `main`)

---

## Steps

Each step lists the exact command and its expected output. Do not skip steps.

1. **[Action name]**
   ```bash
   exact command here
   ```
   Expected output: `...`

2. **[Action name]**
   ```bash
   exact command here
   ```
   Expected output: `...`

3. **[Action name]**
   ```bash
   exact command here
   ```
   Expected output: `...`

---

## Verification

How to confirm the SOP completed successfully:

```bash
# Verification command
python3 scripts/age_engineer.py preflight
```

Expected: `Preflight: all checks PASS — system clear`

---

## Turnback Criteria

Conditions that mean STOP and escalate rather than continue:

- If step N produces output containing `[ERROR_STRING]` → stop, create `age-escalation` issue
- If verification command exits with code 2 → stop, diagnose before retrying
- If the FMEA table is left in a partial state (row updated but not committed) → commit or revert before ending session

**Escalation label:** `age-escalation`

# AGE Workbench

**Last Updated:** 2026-06-27T00:00:00Z (initial seed)
**AGE Status:** Active — awaiting first session
**Session Count:** 0

---

## RPN Heat Map — All Open Items

| Priority | Table | RPN | Status | Process Step / Design Element | Failure Mode |
|----------|-------|-----|--------|-------------------------------|--------------|
| [CRITICAL] | PFMEA | 240 | Open | Content Creation | Rescue modeling in hero / parent copy |
| [CRITICAL] | DFMEA | 210 | Open | SAGA Proposal Structure | Proposals missing explicit Current State → Target State → Delta → Gap-Closing structure |
| [CRITICAL] | PFMEA | 175 | Open | Content Creation | Aspiration theater framing |
| [HIGH]     | DFMEA | 180 | Open | Runtime Monitor | Monitor not wired to all policy/content modification points |
| [HIGH]     | DFMEA | 160 | Open | Verification Pipeline | No automated gate preventing un-verified proposals from applying policy changes |
| [HIGH]     | DFMEA | 144 | Open | Audit Log Parser | Regex-based parser fragile to format variations |
| [HIGH]     | PFMEA | 108 | Open | SAGA Loop Operation | Proposal bypasses verification pipeline |
| [MONITOR]  | PFMEA | 96  | Open | Audit System | Incomplete or missing audit trail on refusal |
| [MONITOR]  | PFMEA | 60  | Open | Runtime Monitor | Core axiom check skipped or mis-keyed |

**Total Open:** 9 | **Critical (RPN ≥ 150):** 3 | **High (100–149):** 4 | **Monitor (< 100):** 2

---

## Work Queue

### Critical (RPN ≥ 150) — Requires Active Work

- **RPN 240** [PFMEA] Content Creation / Rescue modeling in hero / parent copy
  - Status: Open
  - Recommended Action: Enforce Way Through checklist before publish; run anti-pattern scan on key pages
  - Root Cause: Implicit framing defaults in copywriting without explicit guidelines
  - First session priority: Design SAGA proposal to add Way Through content checklist to SOP

- **RPN 210** [DFMEA] SAGA Proposal Structure / Proposals missing explicit Current→Target→Delta→Gap-Closing format
  - Status: Open
  - Recommended Action: Update proposal template; validate structure in audit-processor before accepting
  - Root Cause: Original proposal templates did not mandate this structure
  - Note: Some existing proposals already follow this structure — verify and update template to enforce universally

- **RPN 175** [PFMEA] Content Creation / Aspiration theater framing
  - Status: Open
  - Recommended Action: Add evidence-first framing rules to operational policies
  - Root Cause: Lack of explicit evidence-first framing rules

### High (RPN 100–149) — SAGA Trigger Threshold

- **RPN 180** [DFMEA] Runtime Monitor / Monitor not wired to all policy/content modification points
  - Status: Open
  - Recommended Action: Enforce monitor wiring check in all new workflow PRs

- **RPN 160** [DFMEA] Verification Pipeline / No automated gate preventing un-verified proposals
  - Status: Open
  - Recommended Action: Implement `needs-verification` → `verified` label gate with automated check

- **RPN 144** [DFMEA] Audit Log Parser / Regex-based parser fragile to format variations
  - Status: Open
  - Recommended Action: Add schema validation to `generate_dashboard.py`; write unit tests

- **RPN 108** [PFMEA] SAGA Loop Operation / Proposal bypasses verification pipeline
  - Status: Open
  - Recommended Action: Wire runtime monitor as mandatory first step in all update workflows

### Monitor (RPN < 100) — Track, No Immediate Action

- **RPN 96** [PFMEA] Audit System / Incomplete or missing audit trail on refusal
  - Status: Open
  - Recommended Action: Add explicit error-path audit logging; test refusal path end-to-end

- **RPN 60** [PFMEA] Runtime Monitor / Core axiom check skipped or mis-keyed
  - Status: Open
  - Recommended Action: Enumerate all entry points; verify monitor is called at each

---

## In-Progress Items

*(No rows currently In Progress — awaiting first AGE session)*

---

## System Health Pulse

- **Open rows:** 9
- **Critical unaddressed (Open/Triaged):** 3
- **Refusal rate (AUDIT-LOG.md):** 0.0% (1 total audit event logged — system just initialized)
- **Last SAGA cycle:** see `saga-analyze.yml` run history in GitHub Actions
- **Last workbench update:** 2026-06-27 (initial seed by AGE deployment)

---

## Session Pulse Log

| Session | Date | Actions Taken | Rows Moved | Notes |
|---------|------|---------------|------------|-------|
| 0 | 2026-06-27 | Initial AGE deployment — CLAUDE.md, scripts, workflows created | — | All 9 rows seeded; awaiting first live session |

---

## Recently Closed Items

*(No closed items yet — updated as rows reach Verified/Closed status)*

---

## AGE Deployment Notes

**Deployed:** 2026-06-27

**Files created this session:**
- `CLAUDE.md` — AGE persistent identity and operating instructions
- `fmea-agent.config.json` — Project config (thresholds, critical systems, compliance targets)
- `AGE-ENGINEER-ROLE.md` — Formal role charter
- `AGE-WORKBENCH.md` — This file (live work surface)
- `scripts/age_engineer.py` — Core FMEA lifecycle engine
- `scripts/pr_fmea_analyzer.py` — PR risk analysis (calls Claude API)
- `scripts/prd_spof_scanner.py` — PRD SPOF detection
- `scripts/dependency_compliance.py` — Compliance monitoring
- `.github/workflows/age-engineer.yml` — Bi-weekly maintenance scan
- `.github/workflows/age-pr-analysis.yml` — PR protection
- `.github/workflows/age-prd-scan.yml` — PRD SPOF scan on markdown push

**First session instructions:**
1. Run `python3 scripts/age_engineer.py scan` to verify all 9 rows appear
2. Run `python3 scripts/age_engineer.py queue` to see prioritized buckets
3. Focus on RPN 240 (Content Creation / Rescue modeling) — highest priority
4. Follow FMEA lifecycle: Triage → In Progress → Solution Designed → Verified
5. Use `python3 scripts/age_engineer.py update-status` for every state transition

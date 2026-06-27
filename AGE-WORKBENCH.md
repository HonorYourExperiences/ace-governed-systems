# AGE Workbench
**Last Updated:** 2026-06-27T16:22:13Z  
**AGE Status:** Active  

---

## RPN Heat Map — All Open Items

| Priority | Table | RPN | Status | Process Step / Design Element | Failure Mode |
|----------|-------|-----|--------|-------------------------------|--------------|
| [CRITICAL] | PFMEA | 240 | In Progress | Content Creation | Rescue modeling in hero / parent copy |
| [CRITICAL] | DFMEA | 210 | Open | SAGA Proposal Structure | Proposals missing explicit Current State → Ta |
| [CRITICAL] | DFMEA | 180 | Open | Runtime Monitor | Monitor not wired to all policy/content modif |
| [CRITICAL] | PFMEA | 175 | Open | Content Creation | Aspiration theater framing |
| [CRITICAL] | DFMEA | 160 | Open | Verification Pipeline | No automated gate preventing un-verified prop |
| [HIGH]     | DFMEA | 144 | Open | Audit Log Parser | Regex-based parser fragile to format variatio |
| [HIGH]     | PFMEA | 108 | Open | SAGA Loop Operation | Proposal bypasses verification pipeline |
| [MONITOR]  | PFMEA | 96 | Open | Audit System | Incomplete or missing audit trail on refusal |
| [MONITOR]  | PFMEA | 60 | Open | Runtime Monitor | Core axiom check skipped or mis-keyed |

**Total Open:** 9 | **Critical:** 5 | **High:** 2 | **Monitor:** 2

---

## Work Queue

### Critical (RPN ≥ 150) — Requires Active Work
- **RPN 240** [PFMEA] Content Creation / Rescue modeling in hero / parent copy
  - Status: In Progress
  - Recommended Action: Enforce Way Through checklist before publish; run anti-pattern scan on key pages
- **RPN 210** [DFMEA] SAGA Proposal Structure / Proposals missing explicit Current State → Target State → Delta → Gap-Closing structure
  - Status: Open
  - Recommended Action: Update proposal template; validate structure in audit-processor before accepting
- **RPN 180** [DFMEA] Runtime Monitor / Monitor not wired to all policy/content modification points
  - Status: Open
  - Recommended Action: Enforce monitor wiring check in all new workflow PRs
- **RPN 175** [PFMEA] Content Creation / Aspiration theater framing
  - Status: Open
  - Recommended Action: Add evidence-first framing rules to operational policies
- **RPN 160** [DFMEA] Verification Pipeline / No automated gate preventing un-verified proposals from applying policy changes
  - Status: Open
  - Recommended Action: Implement `needs-verification` → `verified` label gate with automated check

### High (RPN 100–149) — SAGA Trigger Threshold
- **RPN 144** [DFMEA] Audit Log Parser / Regex-based parser fragile to format variations
  - Status: Open
- **RPN 108** [PFMEA] SAGA Loop Operation / Proposal bypasses verification pipeline
  - Status: Open

### Monitor (RPN < 100) — Track, No Immediate Action
- **RPN 96** [PFMEA] Audit System / Incomplete or missing audit trail on refusal
  - Status: Open
- **RPN 60** [PFMEA] Runtime Monitor / Core axiom check skipped or mis-keyed
  - Status: Open

---

## In-Progress Items

- [PFMEA] RPN 240 — Content Creation / Rescue modeling in hero / parent copy
  - Status: In Progress <!-- AGE: 2026-06-27 | Issue #6 assigned AGE proceed; active implementation in this branch -->

---

## System Health Pulse

- **Open rows:** 9
- **Critical unaddressed (Open/Triaged):** 4
- **Refusal rate (AUDIT-LOG.md):** 0.0%
- **Last SAGA cycle:** see `saga-analyze.yml` run history
- **Workbench last updated:** 2026-06-27T16:22:13Z
- **Git branch:** `copilot/age-overdue-critical-fmea-row` @ `9a96424`
- **Proposal pipeline:** 0 Solution Designed | 1 In Progress | 0 Triaged

---

## Session Pulse Log

| Session | Date | Actions Taken | Rows Moved | Notes |
|---------|------|---------------|------------|-------|
| *(Updated by AGE at each session end)* | | | | |

---

## Recently Closed Items

*(No closed items yet — updated as rows reach Closed status)*

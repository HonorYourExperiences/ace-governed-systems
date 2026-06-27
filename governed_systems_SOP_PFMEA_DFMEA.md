# Governed Systems Implementation: SOP, PFMEA, and DFMEA

**Scope:** Everything axiomatically required to instantiate, run, and continuously improve the BYDT Brand Governor (or any governed self-improving agent system) using the constitution, SAGA loop, verification pipeline, runtime monitor, TLA+ model, and anti-pattern catalog.

**Governing Principle (from Core Axioms):**  
All procedures, risk analyses, and updates must preserve Inherent Sufficiency, Way Through, Witnessing & Mature Presence, Evidence & Capability, and Audit Integrity. No change to this document or the underlying system may weaken these without explicit escalation and refusal of the proposal.

These documents are living artifacts. They are automatically populated and updated through the governed SAGA process.

---

## 1. Standard Operating Procedure (SOP)

### Phase 0: Initial Setup (One-Time)
1. Clone or initialize the `ace-governed-systems` repository.
2. Load the latest constitution YAML.
3. Instantiate the runtime monitor / consultation hook.
4. Add the anti-pattern catalog as a reference.
5. (Optional) Confirm the TLA+ spec passes with chosen bounds and scheduling constraints.

### Phase 1: Daily / Periodic Operation (SAGA Cycle)
1. **Sense** — Trigger on schedule or new signals. Scan traces.
2. **Analyze** — Map patterns to core axioms and anti-pattern catalog. **Explicitly perform Current State Assessment vs Target State.**
3. **Generate** — Draft precise gap-closing proposal.
4. **Act / Verify** — Submit to verification pipeline.
5. Apply or refuse with full audit.

### Phase 2: Issue-Driven Continuous Update (Automatic)
- Refusals, anti-pattern matches, and near-misses auto-append to PFMEA/DFMEA.
- SAGA Analyze generates verified proposals to close identified gaps.
- Updates to SOP, FMEAs, and operational policies happen only through the verification pipeline.

**Implementation (Active):**
- `audit-processor.yml` — On every `audit`-labeled refusal issue: appends a PFMEA row via `scripts/pfmea_append.py` and creates a structured SAGA gap-closing proposal issue labeled `needs-verification`.
- `saga-analyze.yml` — Weekly (Monday 07:00 UTC) scheduled run: executes `scripts/saga_analyze.py` which reads AUDIT-LOG.md and PFMEA/DFMEA tables, identifies deltas (refusal rate > 10%, recurring reasons, RPN ≥ 100), and posts a structured gap-closing proposal issue labeled `needs-verification`.
- **Verification gate:** Proposals are blocked from triggering policy changes until a human reviewer adds the `verified` label. The `needs-verification` label is the indicator that a proposal requires human review.
- **AGE Engineer Role (Active):** An AGE agent manages the complete FMEA row lifecycle via Claude Code sessions. The AGE triages open rows, designs solutions, generates SAGA proposals, and transitions rows through Open → Verified. Only humans may transition rows from Verified → Closed. See `CLAUDE.md` for session operating instructions and `AGE-ENGINEER-ROLE.md` for the role charter. Live status: `AGE-WORKBENCH.md`.

### Explicit Capability Gap-Closing Structure (Added for Self-Building)

**In SAGA Analyze, the system must now explicitly do:**

**A. Current State Assessment**  
Pull key signals from the last period: refusal rate, top anti-patterns triggered, FMEA RPN trends, audit completeness, evidence of axiom alignment in outputs (especially on bydt.org), engagement depth, etc.

**B. Target State Definition**  
Anchor in the five immutable core axioms + desired maturity level: zero critical anti-pattern exposure + measurable evidence of capability building + strong "way through" modeling on bydt.org and all outputs.

**C. Delta Identification & Measurement**  
Produce a structured gap statement. Example:  
"Current: High occurrence of rescue modeling on bydt.org homepage and WonderCard descriptions (anti-pattern). RPN on that row: 168.  
Target: RPN < 80 and clear 'way through' framing within 3 cycles.  
Distance: Significant misalignment with Way Through axiom + weak evidence of capability."

**D. Gap-Closing Proposal Generation**  
Every proposal generated in this phase must explicitly state:  
- Which delta it is closing  
- How success will be measured (evidence-based, axiom-respecting metric)  
- That it preserves all core axioms

This turns SAGA into a deliberate capability-building engine that repeatedly measures distance to the target and closes it through verified action.

**Key Guardrails:**
- Core axioms remain immutable except via explicit human escalation.
- All updates to SOP, FMEAs, or operational policies must pass verification.

---

## 2. Process Failure Mode and Effects Analysis (PFMEA)

> **Columns:** Process Step | Failure Mode | Effect of Failure | S (1–10) | Cause / Mechanism | O (1–10) | Current Controls | D (1–10) | RPN (S×O×D) | Recommended Action | Status
>
> Rows are automatically appended by the audit-processor workflow when a refusal or anti-pattern match is detected. RPN ≥ 100 triggers automatic SAGA Analyze.

| Process Step | Failure Mode | Effect of Failure | S | Cause / Mechanism | O | Current Controls | D | RPN | Recommended Action | Status |
|---|---|---|---|---|---|---|---|---|---|---|
| Content Creation | Rescue modeling in hero / parent copy | Way Through axiom erosion; models outsourcing over capability | 8 | Implicit framing defaults in copywriting without explicit guidelines | 6 | Way Through content guidelines (Proposal B) | 5 | 240 | Enforce Way Through checklist before publish; run anti-pattern scan on key pages | Verified <!-- AGE: 2026-06-27 | verify-closure PASS commit:c8dcb24. Artifacts: (1) cape-able-heroes/WAY-THROUGH-CONTENT-CHECKLIST.md 10-item gate, (2) scripts/scan_content_antipatterns.py exits 0 on full cape-able-heroes/ scan, (3) CI gate wired in age-prd-scan.yml way-through-scan job, (4) 3 HIGH-severity content hits resolved (BUSINESS-MODEL.md:28, BUSINESS-MODEL.md:38, SESSION-FORMAT.md:40), (5) closure row appended S=8 O=3 D=2 RPN=48. Awaiting human Closed confirmation. --> | 7-section SAGA proposal created and linted PASS: proposals/prop-AGE-2026-06-27-rescue-modeling-checklist.md. Solution: (A) WAY-THROUGH-CONTENT-CHECKLIST.md ≥8 items, (B) scan_content_antipatterns.py script + CI gate. Target RPN 48 (S=8, O=3, D=2). Human approval not required — operational only. --> | Beginning SAGA proposal design. Solution targets O reduction (6→3) via explicit publish checklist and framing guidelines, and D reduction (5→2) via automated anti-pattern scan script wired to review workflow. Target RPN: 8×3×2=48. --> | Root cause confirmed: no enforceable Way Through checklist at publish time; no automated anti-pattern scan. Prop B (prop-2026-06-26-bydt-002) is partial control only — not implemented. O=6 driven by implicit copywriting defaults. D=5 because no scan is wired to CI or review gates. --> |
| Content Creation | Aspiration theater framing | Evidence & Capability axiom erosion; builds false confidence | 7 | Lack of explicit evidence-first framing rules | 5 | SAGA proposal review | 5 | 175 | Add evidence-first framing rules to operational policies | Open |
| SAGA Loop Operation | Proposal bypasses verification pipeline | Unverified change enters production; governance gap | 9 | Missing enforcement gate on proposal application step | 3 | Runtime monitor check (partial) | 4 | 108 | Wire runtime monitor as mandatory first step in all update workflows | Open |
| Audit System | Incomplete or missing audit trail on refusal | Audit Integrity axiom violation; lineage gap | 8 | Workflow error handling not propagating failure to audit log | 3 | `continue-on-error` + commit step in audit-processor | 4 | 96 | Add explicit error-path audit logging; test refusal path end-to-end | Open |
| Runtime Monitor | Core axiom check skipped or mis-keyed | Core drift; axiom silently modified | 10 | Monitor not wired to all modification entry points | 2 | Constitution YAML loaded per run | 3 | 60 | Enumerate all entry points; verify monitor is called at each | Open |

| Content Creation | Rescue modeling in hero / parent copy | Way Through axiom preserved; models child agency over outsourcing | 8 | Explicit publish checklist + automated anti-pattern scan eliminates implicit framing defaults | 3 | WAY-THROUGH-CONTENT-CHECKLIST.md (10-item gate) + scan_content_antipatterns.py (CI exit 1 on HIGH) | 2 | 48 | Enforce Way Through checklist before publish; scan_content_antipatterns.py wired to CI on cape-able-heroes push (Issue #AGE-2026-06-27) | Closed |

<!-- PFMEA_AUTO_APPEND_MARKER -->
<!-- AGE-LIFECYCLE-MANAGED: Rows above are managed by the AGE agent (scripts/age_engineer.py). Status transitions require evidence notes embedded in the Status cell. -->

---

## 3. Design Failure Mode and Effects Analysis (DFMEA)

> **Columns:** Design Element | Failure Mode | Effect of Failure | S (1–10) | Cause / Mechanism | O (1–10) | Current Controls | D (1–10) | RPN (S×O×D) | Recommended Action | Status
>
> Rows are appended when a refusal or near-miss reveals a structural design issue.

| Design Element | Failure Mode | Effect of Failure | S | Cause / Mechanism | O | Current Controls | D | RPN | Recommended Action | Status |
|---|---|---|---|---|---|---|---|---|---|---|
| Runtime Monitor | Monitor not wired to all policy/content modification points | Constitution enforcement bypassed on unwired paths | 9 | Incremental wiring; new workflows added without monitor hook | 4 | RUNTIME-MONITOR-WIRING.md reference doc | 5 | 180 | Enforce monitor wiring check in all new workflow PRs | Open |
| SAGA Proposal Structure | Proposals missing explicit Current State → Target State → Delta → Gap-Closing structure | SAGA Theater (process without measurable substance) | 7 | Original proposal templates did not mandate this structure | 5 | Explicit capability gap-closing structure section in SOP | 6 | 210 | Update proposal template; validate structure in audit-processor before accepting | Open |
| Verification Pipeline | No automated gate preventing un-verified proposals from applying policy changes | Manual oversight failure; drift risk in high-volume cycles | 8 | Gate not yet implemented as code; relies on human review | 4 | Proposal label workflow (partial) | 5 | 160 | Implement `needs-verification` → `verified` label gate with automated check | Open |
| Audit Log Parser | Regex-based parser fragile to format variations | Dashboard data corrupted; metrics incorrect | 6 | Hand-crafted regex without schema validation | 4 | Manual review of generated dashboard | 6 | 144 | Add schema validation to `generate_dashboard.py`; write unit tests | Open |

<!-- DFMEA_AUTO_APPEND_MARKER -->
<!-- AGE-LIFECYCLE-MANAGED: Rows above are managed by the AGE agent (scripts/age_engineer.py). Status transitions require evidence notes embedded in the Status cell. -->

---

**Integration & Automatic Update Mechanism**  
The loop (Detection → Population of FMEAs → Gap-Closing Proposal → Verified Update) ensures the mutable layer builds capability while the immutable core stays protected.

**Initial Next Actions**  
1. Instantiate runtime monitor with core predicate checks.
2. Wire SAGA with the explicit gap-closing structure.
3. Seed initial FMEA rows or run first cycle on real traces (including bydt.org).
4. Confirm TLA+ model with scheduling constraints.
5. Let the first real proposal run through the full loop.

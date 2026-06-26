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

(The table structure remains the same as previously defined. It is automatically appended to when issues are detected.)

---

## 3. Design Failure Mode and Effects Analysis (DFMEA)

(The table structure remains the same. It is automatically updated on modeling gaps or real refusals that reveal design issues.)

---

**Integration & Automatic Update Mechanism**  
The loop (Detection → Population of FMEAs → Gap-Closing Proposal → Verified Update) ensures the mutable layer builds capability while the immutable core stays protected.

**Initial Next Actions**  
1. Instantiate runtime monitor with core predicate checks.
2. Wire SAGA with the explicit gap-closing structure.
3. Seed initial FMEA rows or run first cycle on real traces (including bydt.org).
4. Confirm TLA+ model with scheduling constraints.
5. Let the first real proposal run through the full loop.
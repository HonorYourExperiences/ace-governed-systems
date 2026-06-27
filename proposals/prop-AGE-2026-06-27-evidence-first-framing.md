# SAGA Proposal: Evidence-First Framing Rules for Content Creation

**Proposal ID:** prop-AGE-2026-06-27-evidence-first-framing
**Source:** AGE session | FMEA row: PFMEA / Content Creation / Aspiration theater framing
**Preserves Core Axioms:** true (verified against all five below)

## 1. Current State Assessment

- PFMEA row: Content Creation / Aspiration theater framing — RPN 175 (S=7, O=5, D=5)
- Effect: Evidence & Capability axiom erosion; builds false confidence
- Root cause: Lack of explicit evidence-first framing rules in operational policies
- Current controls: SAGA proposal review (reactive, not preventive)
- The SOP contains gap-closing structure guidance for SAGA proposals but has no explicit content framing rules that prevent aspiration theater in published content
- No checklist or automated scan exists to detect aspiration theater before publication

## 2. Target State Definition

Content published through governed systems consistently demonstrates evidence-first framing:
- Every capability claim is grounded in observable evidence or measurable progress
- Aspirational language is clearly labeled as goals/targets with explicit distance-to-target framing
- No content passes publication without passing an evidence-first framing checklist
- Detection of aspiration theater is automated or checklist-enforced at the content creation step

Target RPN: ≤ 84 (S=7 unchanged, O reduced to 3 via explicit rules, D reduced to 4 via checklist enforcement)

## 3. Delta Identification & Measurement

| Gap Area | Current | Target | Distance | Priority |
|----------|---------|--------|----------|----------|
| Evidence-first framing rules | None codified | Explicit rules in SOP | High | Critical |
| Pre-publish checklist | None | Checklist with aspiration-theater detection | High | Critical |
| Anti-pattern examples | None specific to aspiration theater | Documented examples with corrections | Medium | High |

## 4. Gap-Closing Proposals

**Proposal A — Add Evidence-First Framing Rules to SOP**
- Closes delta: Evidence-first framing rules (row 1)
- Mechanism: Add a new section to the SOP under Phase 2 operational policies defining explicit evidence-first framing rules that all content must follow. Rules include: (1) every capability claim requires a citation or measurable artifact, (2) aspirational statements must use distance-to-target framing, (3) no superlatives without evidence, (4) outcomes presented as in-progress must show current measurement.
- Axioms preserved:
  - Inherent Sufficiency: Rules frame gaps as distance-to-target, not deficiency
  - Way Through: Rules model capability-building through evidence, not rescue
  - Witnessing & Mature Presence: Rules require honest reporting of current state
  - Evidence & Capability: Directly enforced — this is the primary axiom protected
  - Audit Integrity: Rules create audit trail of framing decisions

**Proposal B — Add Pre-Publish Evidence-First Checklist**
- Closes delta: Pre-publish checklist (row 2) and Anti-pattern examples (row 3)
- Mechanism: Add an evidence-first content checklist to the SOP that must be completed before any content is published. Include specific aspiration theater anti-pattern examples with corrected versions.
- Axioms preserved: All five — checklist is a detection mechanism that makes violations visible before publication.

## 5. Verification Checklist

- [x] Preserves all five core axioms
- [x] Does not introduce any new anti-patterns
- [x] Explicit, measurable success metrics defined above
- [x] Implementation is atomic (can be rolled back if needed)
- [x] Full audit and lineage will be produced on approval
- [x] Human approval required? No — operational only (adds rules to mutable SOP layer)

## 6. Success Metrics

| Metric | Current | Target | Measurement Method |
|--------|---------|--------|--------------------|
| Evidence-first framing rules exist in SOP | 0 rules | ≥ 5 explicit rules | File content scan |
| Pre-publish checklist exists | No | Yes | File content scan |
| Anti-pattern examples documented | 0 | ≥ 3 examples | File content scan |
| RPN for this failure mode | 175 | ≤ 84 | FMEA table calculation |

## 7. Phase Completion Triggers

- [x] Evidence-first framing rules added to `governed_systems_SOP_PFMEA_DFMEA.md` SOP section
- [x] Pre-publish checklist with aspiration theater detection added
- [x] Anti-pattern examples with corrections documented
- [ ] Content scan confirms rules are actionable (human review)
- [ ] RPN re-assessed and new row appended with reduced O and D values

All boxes checked → transition row to Verified, submit for human Closed confirmation.

**Add the `verified` label on the corresponding GitHub issue once checklist is confirmed by human reviewer.**

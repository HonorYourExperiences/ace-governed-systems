# SAGA Proposal: Close Rescue Modeling Gap in Cape-Able Heroes Outreach Content

**Proposal ID:** prop-AGE-2026-06-27-rescue-modeling-outreach
**Source:** AGE triage of PFMEA row RPN 240 (Content Creation / Rescue modeling in hero / parent copy)
**Preserves Core Axioms:** true — directly strengthens Way Through and Evidence & Capability; creates audit trail that did not exist.

## 1. Current State Assessment
OUTREACH-TEMPLATES.md (cape-able-heroes/) contains framing that attributes primary agency to the external program:
- “designed to move a child from hesitation to participation”
- “for children who are still figuring out how to trust themselves”
- “what changes when a child starts to believe that is remarkable to watch”

No Way Through checklist exists. No anti-pattern scan has been executed against brand copy. This is the exact open PFMEA row (S8 / O6 / D5 = RPN 240). Existing files in proposals/ also lack required SAGA structure, confirming the related DFMEA row RPN 210 is active in the same workstream.

## 2. Target State Definition
Every piece of brand-facing copy (outreach, parent materials, session language) passes an explicit Way Through Content Checklist before it is published or sent. Rescue/savior framing is replaced with language that centers the child’s enactment, the architecture supplied, and the witnessed evidence produced. Anti-pattern scan is part of the content SOP. Re-audit of templates shows zero instances of the three flagged patterns. RPN on this row drops below 100 on verified re-evaluation.

## 3. Delta Identification & Measurement

| Gap Area                  | Current                                      | Target                                              | Delta                                      |
|---------------------------|----------------------------------------------|-----------------------------------------------------|--------------------------------------------|
| Framing in outreach       | Savior/mover language present in 3+ phrases  | Child-enactment + structure + witness language only | Remove or re-author flagged phrases        |
| Pre-publish control       | None explicit                                | Way Through Checklist enforced before any send/publish | Checklist artifact + SOP integration       |
| Scan / audit trail        | Ad hoc or absent                             | Documented anti-pattern scan + evidence log         | Scan report committed as verification      |

## 4. Gap-Closing Proposals
1. Create `SOPs/SOP-2026-06-27-way-through-content-checklist.md` using the existing `_TEMPLATE.md`. The checklist will name the three forbidden patterns above, require replacement language that centers “the child enacts… supported by… witnessed by… recorded in…”, and mandate the “I tried. I kept going. I have proof.” primacy already present in strong sections of the templates.
2. Revise OUTREACH-TEMPLATES.md: replace the three flagged phrases with axiom-aligned alternatives while preserving all functional and relational value (shared language for parents/teachers, visible evidence, badge-at-start, etc.).
3. Add a mandatory “Way Through Content Checklist — passed” gate to the content creation section of `governed_systems_SOP_PFMEA_DFMEA.md` and to any future bydt.org content SOP.
4. Execute the anti-pattern scan against the revised templates and commit the scan log as evidence.

## 5. Verification Checklist
- [ ] Revised OUTREACH-TEMPLATES.md committed with before/after diff.
- [ ] New checklist file present in SOPs/ and referenced from the FMEA row.
- [ ] Anti-pattern scan report committed showing zero remaining instances of the three patterns.
- [ ] FMEA row status updated to Verified with evidence note containing proposal ID and commit SHA.
- [ ] Re-audit of templates by founder or next AGE session confirms alignment.
- [ ] Way Through is preserved: language centers child enactment over external rescue.
- [ ] Evidence & Capability is preserved: every publish requires observable checklist passage and scan artifact.
- [ ] Audit Integrity is preserved: full lineage from proposal through checklist to revised templates is created and committed.
- [ ] Inherent Sufficiency and Witnessing & Mature Presence remain untouched and are enacted by the checklist itself.

## 6. Success Metrics
| Metric | Current | Target | Measurement Method |
|--------|---------|--------|--------------------|
| Flagged rescue-modeling phrases | 3+ phrases in outreach templates | 0 flagged phrases | Anti-pattern scan plus before/after diff |
| Pre-publish Way Through control | No explicit checklist | Checklist artifact referenced by SOP/FMEA row | File exists and row evidence note cites it |
| RPN for rescue-modeling row | 240 | Below 100 after verification | Updated S/O/D closure row with evidence |

## 7. Phase Completion Triggers
- [ ] OUTREACH-TEMPLATES.md or successor content surface is revised without changing the core offer.
- [ ] Way Through checklist artifact is committed and referenced from the FMEA row.
- [ ] Anti-pattern scan produces zero remaining instances of the flagged patterns.
- [ ] Verification evidence is embedded in the FMEA status cell.
- [ ] Founder or next AGE session confirms the row can move from Verified toward human Closed confirmation.

Change is scoped to one file (templates) plus one new SOP artifact. No constitution files or immutable layers are touched. Rollback is single-file revert of templates plus deletion of checklist if verification fails. No production systems or external sends are altered until verification is complete.

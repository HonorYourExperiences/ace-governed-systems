# SAGA Proposal: Way Through Publish Checklist & Anti-Pattern Scan for Rescue Modeling

**Proposal ID:** prop-AGE-2026-06-27-rescue-modeling-checklist  
**Source:** AGE session 2026-06-27 | FMEA row: PFMEA / Content Creation / Rescue modeling in hero / parent copy  
**Preserves Core Axioms:** true (verified against all five below)

---

## 1. Current State Assessment

**Row:** PFMEA / Content Creation / Rescue modeling in hero / parent copy  
**Current RPN:** 240 (S=8, O=6, D=5)  
**Status at session start:** Open → Triaged → In Progress (this session)

Observable evidence grounding each S/O/D value:
- **S=8:** Rescue modeling directly erodes Way Through (Axiom 2), the most operationally active axiom. If hero/parent copy frames the program as the rescuer, users receive a model of outsourcing capability rather than building it — the core purpose is contradicted at the highest-visibility surface of the site.
- **O=6 (HIGH):** No enforceable checklist exists at publish time. Copywriting defaults toward rescue framing because it is the cultural norm in marketing copy. `proposals/2026-06-26-bydt-org-way-through-content.md` (Proposal B) identifies this gap but has not been implemented. Zero of the key bydt.org pages have been scanned against the anti-pattern catalog (evidence: scan of `cape-able-heroes/` shows no `/content-scan/` artifact).
- **D=5 (MODERATE-HIGH):** Detection relies entirely on human reviewer awareness. No automated scan is wired to the content review workflow, CI, or any PR gate. The runtime monitor (`RUNTIME-MONITOR-WIRING.md`) does not cover content framing at publish time.

**Existing partial control:** `proposals/2026-06-26-bydt-org-way-through-content.md` describes the right direction but does not constitute an enforceable gate. It is a gap-analysis document, not an implementation artifact.

---

## 2. Target State Definition

**Axiom threatened:** Way Through (Axiom 2) — *never recommend waiting or outsourcing when a path forward using existing capabilities exists.*

"Resolved" means, measurably:

1. A `WAY-THROUGH-CONTENT-CHECKLIST.md` exists in `cape-able-heroes/` with ≥8 specific, observable checklist items covering rescue vs. capability framing for hero, navigation, and parent copy sections.
2. A `scripts/scan_content_antipatterns.py` script exists and, when run against the key pages in `cape-able-heroes/`, returns ≤0 HIGH-severity rescue-modeling hits.
3. The scan script is wired into `.github/workflows/age-prd-scan.yml` (or a new `content-antipattern-scan.yml` workflow) so it runs on every markdown push to `cape-able-heroes/`.
4. The FMEA table has a new closure row appended via `pfmea_append.py` with updated S=8, O=3, D=2 (RPN=48), and status `Closed` (pending human approval).
5. `python3 scripts/age_engineer.py verify-closure` returns `PASS` for this row.

---

## 3. Delta Identification & Measurement

| Gap Area | Current | Target | Distance | Priority |
|----------|---------|--------|----------|----------|
| Way Through publish checklist | None exists | `WAY-THROUGH-CONTENT-CHECKLIST.md` with ≥8 items, enforced pre-publish | High | Critical |
| Anti-pattern scan coverage | 0 of key pages scanned | 100% of `cape-able-heroes/` content scanned on every push | High | Critical |
| Framing guidelines in operational policy | Partial (Proposal B text only) | Explicit rescue-vs-capability examples documented with observable pass/fail criteria | Medium | High |
| CI gate for content framing | None | Scan runs on every markdown push; fails PR if HIGH-severity hit found | High | Critical |

---

## 4. Gap-Closing Proposals

**Proposal A — Way Through Content Checklist (Operational Policy Artifact)**
- Closes delta: "Way Through publish checklist"
- Mechanism: Create `cape-able-heroes/WAY-THROUGH-CONTENT-CHECKLIST.md` containing:
  - ≥8 observable checklist items (each must be answerable Yes/No without interpretation)
  - A "rescue signal" pattern list (phrases like "we help you," "you don't have to," "let us handle," "take the burden off") with a corresponding "Way Through alternative" for each
  - A "capability signal" positive pattern list (phrases that demonstrate the subject's own agency, discernment, imaginative power)
  - A decision rule: if any rescue signal appears in hero, H1, nav labels, CTA buttons, or parent copy — the item fails and copy must be revised before publish
- Reduces O from 6→3: checklist makes the failure unlikely when followed; it is specific enough to use at draft stage
- Axioms preserved: Way Through (directly closes the gap), Witnessing & Mature Presence (language is precise, not theatrical), Evidence & Capability (checklist items are observable), Inherent Sufficiency (frames users as capable, not deficient), Audit Integrity (checklist completion is logged)

**Proposal B — Anti-Pattern Scan Script**
- Closes delta: "Anti-pattern scan coverage" and "CI gate for content framing"
- Mechanism: Create `scripts/scan_content_antipatterns.py` that:
  - Accepts a `--path` argument (directory or file)
  - Loads rescue-modeling patterns from a config section (at minimum: rescue signal phrases from the checklist above)
  - Scans all `.md` files under the path
  - Outputs: file path, line number, matched pattern, severity (HIGH = rescue signal in hero/parent sections; MEDIUM = elsewhere), and a suggested Way Through reframe
  - Exits 1 if any HIGH-severity hit is found (enables CI blocking)
- Wire into `.github/workflows/age-prd-scan.yml` (extend `scan_paths` to include `cape-able-heroes/`) OR create `content-antipattern-scan.yml` that triggers on `push` to `cape-able-heroes/**/*.md`
- Reduces D from 5→2: every markdown push is automatically scanned; HIGH hits block merge
- Axioms preserved: same as Proposal A, plus Audit Integrity (scan results are committed as artifacts or logged)

**Proposal C — Framing Guidelines Document (Evidence-Grounded)**
- Closes delta: "Framing guidelines in operational policy"
- Mechanism: Add a `## Way Through Content Framing` section to `AUDIT-LOG.md` or a new `CONTENT-FRAMING-GUIDE.md` in `cape-able-heroes/` that includes:
  - 3+ before/after rewrite examples drawn from actual bydt.org content (hero copy, parent-facing copy, CTA text)
  - Observable criteria: "Does this sentence model the user doing something, or the program doing something for the user?"
  - Reference to checklist and scan script
- Reduces O from 6→3 (in combination with Proposal A)
- This is lower priority than A and B; implement after A and B are verified

---

## 5. Verification Checklist

- [ ] Preserves all five core axioms
- [ ] Does not introduce any new anti-patterns
- [ ] Explicit, measurable success metrics defined above
- [ ] Implementation is atomic (each proposal A/B/C can be rolled back independently)
- [ ] Full audit and lineage will be produced on approval
- [ ] Human approval required? **No — operational only** (no axiom definitions modified, no IMMUTABLE_VS_MUTABLE_LAYERS.md touched)

---

## 6. Success Metrics

| Metric | Current | Target | Measurement Method |
|--------|---------|--------|--------------------|
| Checklist items covering rescue signals | 0 | ≥8, each answerable Yes/No | Manual count of `WAY-THROUGH-CONTENT-CHECKLIST.md` items |
| Key pages scanned against anti-pattern catalog | 0 | 100% of `.md` files in `cape-able-heroes/` | `python3 scripts/scan_content_antipatterns.py --path cape-able-heroes/` exit 0 |
| HIGH-severity rescue-modeling hits in current content | Unknown (not yet scanned) | 0 after revisions | Scan output shows 0 HIGH hits |
| CI gate active on `cape-able-heroes/**` push | No | Yes | Workflow run visible in GitHub Actions on next markdown push |
| New FMEA closure row RPN | 240 | 48 (S=8, O=3, D=2) | `pfmea_append.py` output + `verify-closure` PASS |

---

## 7. Phase Completion Triggers

- [ ] `cape-able-heroes/WAY-THROUGH-CONTENT-CHECKLIST.md` exists with ≥8 observable items (Proposal A)
- [ ] `scripts/scan_content_antipatterns.py` exists, runs without error, and exits 0 on current content after any needed revisions (Proposal B)
- [ ] CI workflow wired: next push to `cape-able-heroes/**/*.md` triggers scan and result is visible in GitHub Actions (Proposal B)
- [ ] `python3 scripts/scan_content_antipatterns.py --path cape-able-heroes/` returns 0 HIGH-severity rescue-modeling hits
- [ ] New FMEA row appended via `pfmea_append.py` with S=8, O=3, D=2, status=Closed
- [ ] `python3 scripts/age_engineer.py verify-closure --table pfmea --step "Content Creation" --failure "Rescue modeling in hero / parent copy" --evidence "commit:[hash]"` returns PASS

All boxes checked → transition row to Verified, submit for human Closed confirmation.

**Add the `verified` label on the corresponding GitHub issue once checklist is confirmed by human reviewer.**

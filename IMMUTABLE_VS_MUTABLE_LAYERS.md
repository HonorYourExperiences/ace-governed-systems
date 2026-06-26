# Immutable vs Mutable Layers (Sources of Truth)

This document defines the strict separation that protects the system from drift while allowing safe evolution.

## 1. Immutable Core Layer (Never Changes Without Explicit Human Approval)

These sources of truth are protected by the constitution and cannot be altered by SAGA, the runtime monitor, or any automated process:

- The five Core Axioms:
  1. Inherent Sufficiency ("Born Enoughness")
  2. Way Through Over Way Out
  3. Witnessing & Mature Presence
  4. Evidence & Capability Over Aspiration Theater
  5. Audit Integrity & Lineage

- The rule that these core axioms are marked `immutable: true` in the constitution.
- The fundamental architectural separation between "core" and "operational" layers (this separation itself is immutable).
- The non-negotiable requirement that every significant action produces a complete, queryable audit with full lineage.

**Protection mechanisms:**
- TLA+ invariants make core erosion unreachable.
- Runtime monitor refuses any action that would touch core axioms.
- Verification pipeline requires explicit escalation + human approval for any core change.

## 2. Mutable Operational Layer (Constantly Evolves via Verified SAGA Results)

These sources of truth are designed to improve safely through SAGA cycles:

- Operational policies (content review checklist, measurement criteria, logging levels, cadence rules, specific proposal templates, etc.)
- Detailed steps and preventive actions in the SOP
- Rows and recommended actions in PFMEA and DFMEA tables
- Specific scheduling constraints and bounds in the TLA+ model (within the overall framework)
- Exact wording of operational checks and refusal thresholds (as long as they continue to enforce the core axioms)

**Update mechanism:**
- SAGA Sense/Analyze detects issues, anti-patterns, refusals, or improvement opportunities.
- Generate creates a precise proposal with explicit `preserves_core_axioms: true` declaration.
- Act routes it through the full verification pipeline.
- Only approved changes are applied atomically with audit and lineage.

## 3. The Constraints That Enforce the Separation

- Constitutional separation (core vs operational) is itself protected.
- Verification gate (Act) is non-bypassable.
- TLA+ invariants + scheduling constraints (SequentialProposals, BoundedInterleaving, PhaseConsistency) make unsafe states unreachable.
- Anti-pattern catalog acts as living negative constraints.
- Runtime monitor enforces rules at execution time.
- Full audit + lineage on every change or refusal.

This is exactly how SAGA is designed to work: it safely evolves the mutable layer while the immutable core remains stable and protected.
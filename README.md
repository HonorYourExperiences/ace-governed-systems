# ace-governed-systems

Axiomatic Context Engineering — Governed self-improving agent and brand systems.

This repository contains the core artifacts for building and operating axiomatically governed, self-improving systems, including:

- TLA+ specifications with safety invariants, liveness properties, strong fairness, and scheduling constraints
- SAGA loop implementation details
- Anti-pattern catalog
- BYDT Brand Governor constitution and operating procedures
- Automated audit logging and visualization

## Audit Dashboard

Live visual dashboard for the audit trail:

**https://honoryourexperiences.github.io/ace-governed-systems/**

The dashboard shows refusal rates, top reasons for refusals, and other key metrics. It is automatically updated by GitHub Actions.

## Key Components

- `proposals/` — Active SAGA gap-closing proposals
- `.github/workflows/` — Automation for audit processing and dashboard generation
- `governed_systems_SOP_PFMEA_DFMEA.md` — Living Standard Operating Procedures and Failure Mode analyses
- `IMMUTABLE_VS_MUTABLE_LAYERS.md` — Defines protected core axioms vs. evolvable operational layer

## Getting Started

See the documentation files in the root and `proposals/` directory for implementation guidance.
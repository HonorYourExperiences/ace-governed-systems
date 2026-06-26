# ace-governed-systems

**Axiomatic Context Engineering** — Building governed, self-improving systems that stay aligned with their founding principles over time.

This repository contains the core artifacts, workflows, and documentation for a complete governed self-improvement system, originally developed for the BYDT (Build Your Dreaming Things) brand and projects.

## Core Philosophy

The system is built around five immutable core axioms:

- **Inherent Sufficiency** — Value exists before performance
- **Way Through** — Focus on capability, discernment, and imaginative power rather than rescue or outsourcing
- **Witnessing & Mature Presence** — Prioritize presence and relational maturity
- **Evidence & Capability** — Favor real capability over aspiration theater
- **Audit Integrity** — Maintain full lineage and accountability

These axioms are protected. Everything else in the system is designed to evolve safely around them.

## Architecture Overview

The system follows a protected self-improvement loop with verification and feedback:

```mermaid
graph TD
    A[Constitution<br/>Immutable Core Axioms] -->|Protects| B[SAGA Loop<br/>Sense → Analyze → Generate → Act]
    B --> C[Runtime Monitor<br/>Enforces Rules at Runtime]
    C -->|Action Approved| D[System / BYDT Operations]
    C -->|Refused / Issue| E[Audit System<br/>GitHub Issues + Logging]
    E --> F[Dashboard & Analytics]
    E -->|Patterns & Gaps| B
    F -->|Insights| B

    classDef core fill:#BFA16B,stroke:#0A162F,stroke-width:2px,color:#0A162F;
    class A core;
```

### Key Components

| Component                    | Purpose                                                                 | Key Files / Workflows                          |
|-----------------------------|-------------------------------------------------------------------------|------------------------------------------------|
| **Constitution**            | Defines immutable core axioms and mutable operational layer            | `IMMUTABLE_VS_MUTABLE_LAYERS.md`              |
| **SAGA Loop**               | The self-improvement engine (Sense, Analyze, Generate, Act)            | `governed_systems_SOP_PFMEA_DFMEA.md`         |
| **Runtime Monitor**         | Enforces rules at execution time                                        | `RUNTIME-MONITOR-WIRING.md`                   |
| **Audit System**            | Logs all significant actions and refusals                               | GitHub Issues + `audit-processor.yml`         |
| **Dashboard**               | Visual overview of system health and refusal patterns                   | `docs/index.html` + `generate-audit-dashboard.yml` |
| **Cleanup Automation**      | Automatically removes old artifacts and workflow runs                   | `cleanup-old-artifacts-and-runs.yml`          |
| **Formal Verification**     | Mathematical proofs that certain failures are impossible                | TLA+ specs (earlier work)                     |

### Data Flow

1. The **Runtime Monitor** checks actions against the constitution.
2. Significant events are logged as structured **GitHub Issues** (labeled `audit`).
3. The **Audit Processor** workflow processes new issues and can auto-generate gap-closing proposals.
4. The **Dashboard Generator** maintains `AUDIT-DASHBOARD.md` and `dashboard-data.json`.
5. The visual dashboard shows live metrics and trends.
6. Old data is cleaned up automatically.

## Live Dashboard

**https://honoryourexperiences.github.io/ace-governed-systems/**

Shows real-time(ish) audit metrics including refusal rates and top reasons.

## Key Files & Folders

- `proposals/` — Active and historical SAGA gap-closing proposals
- `governed_systems_SOP_PFMEA_DFMEA.md` — Living procedures and risk analyses
- `IMMUTABLE_VS_MUTABLE_LAYERS.md` — Core governance rules
- `AUDIT-DASHBOARD.md` — Auto-generated human-readable dashboard
- `docs/` — GitHub Pages dashboard source
- `.github/workflows/` — All automation (audit processing, dashboard generation, cleanup)

## Status

The core governance system is functional and includes:
- Protected core axioms
- Automated audit logging
- Self-updating dashboard
- Scheduled cleanup
- Formal error handling in workflows

The system is designed to reduce manual oversight while making misalignment visible and actionable.
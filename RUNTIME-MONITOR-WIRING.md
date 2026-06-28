# Runtime Monitor Wiring Guide

This document shows how to wire the core enforcement check that protects the immutable vs mutable layers.

## Core Check (Copy into your workflow)

```javascript
// Runtime Monitor - Core Enforcement Check
const actionType = inputData.action_type || inputData.type;
const proposedChange = inputData.proposed_change || inputData.change;
const constitution = inputData.constitution || inputData.current_constitution;

if (!constitution) {
  return { allowed: false, reason: "No constitution loaded", action: "block" };
}

const coreIds = (constitution.core_axioms || []).map(a => a.id);
const operationalIds = (constitution.operational_policies || []).map(p => p.id);

if (actionType === "update_policy" || actionType === "update_content" || actionType === "site_change") {
  const policyId = proposedChange.policy_id || proposedChange.id || "unknown";

  // Block any attempt to touch core axioms
  if (coreIds.includes(policyId)) {
    return {
      allowed: false,
      reason: "Core axiom modification requires explicit human escalation",
      action: "refuse_and_escalate",
      axiom_violated: policyId
    };
  }

  // Only allow operational changes that came through verified SAGA
  if (operationalIds.includes(policyId)) {
    if (proposedChange.source === "verified_saga_proposal" || proposedChange.verified === true) {
      return { allowed: true, action: "proceed" };
    } else {
      return {
        allowed: false,
        reason: "Operational changes must come through verified SAGA",
        action: "refuse"
      };
    }
  }
}

// Default allow for read-only or non-policy actions
return { allowed: true, action: "proceed" };
```

## Recommended Integration Points

1. **Zapier / Make.com**: Add as the very first Code step in any workflow that can modify policies, content guidelines, or site decisions.
2. **Python / SiteForge**: Add as the first function call in any governance or update endpoint.
3. **Trigger Condition**: Run on any `update_policy`, `update_content`, or `site_change` action.
4. **GitHub workflow changes**: Pull requests that change `.github/workflows/*.yml` are checked by `scripts/validate_governance_change.py` through `age-pr-analysis.yml`. Any state-mutating workflow must include a runtime monitor, verified-SAGA gate, `needs-verification` / `verified` label gate, or AGE preflight control before it can pass.
5. **Entrypoint inventory**: `scripts/validate_runtime_monitor_entrypoints.py` enumerates every GitHub workflow and fails if any state-mutating workflow lacks a runtime monitor / verified-SAGA gate marker. `scripts/age_engineer.py preflight` runs this validator automatically.

## What This Achieves
- Enforces the immutable core (five axioms) at runtime.
- Ensures all changes to the mutable layer come through verified SAGA.
- Creates the foundation for automatic FMEA population and gap-closing loops.
- Prevents new repository-mutating workflows from entering without an explicit governance gate.

## Next
Once wired, every refusal or blocked change will automatically feed the PFMEA and trigger SAGA Analyze for gap-closing proposals.

# Governance Endpoint Ownership Decision (Screen)

- Target families:
  - `/api/capabilities/*`
  - `/api/ops/*`
  - `/api/packs/*`
- Decision Stage: `screen`
- Inputs:
  - `docs/audit/boundary/http_route_classification.md`
  - `docs/audit/boundary/runtime_priority_matrix.md`
  - `docs/audit/boundary/platform_entry_occupation.md`

## Family Decisions

### `/api/capabilities/*`

- priority: **P1 first** (user-facing capability catalog/search chain)
- ownership target: **smart_core route shell**
- fact provider: **scenario capability models/services**
- migration mode: compatibility adapter first, then provider interface extraction.

### `/api/ops/*`

- priority: **P2 staged**
- ownership target: **platform governance layer route shell**
- fact/provider retention: scenario/governance services until dedicated platform governance module is introduced.
- migration mode: batch by subfamily (`tenants/subscription`, `packs batch`, `audit/job`).

### `/api/packs/*`

- priority: **P2 staged**
- ownership target: **platform release/governance route shell**
- fact/provider retention: current scenario pack services in transition period.
- migration mode: start with read-only/catalog endpoints before write/install/upgrade.

## Hard Constraints

1. Route-shell migration must not rewrite governance/business truth semantics.
2. No `security/**`, ACL, financial domains, or manifest changes in these batches.
3. Frontend must keep consuming stable contracts; no model-specific fallback injection.
4. Any uncertainty on authority leakage in governance endpoints triggers stop and re-screen.

## Next Implement Slice

- Implement `/api/capabilities/*` route-shell ownership migration in one bounded batch (adapter delegation), then verify.

# Contract Entry Ownership Decision (P1 Screen)

- Target APIs:
  - `/api/contract/capability_matrix`
  - `/api/contract/portal_dashboard`
- Decision Stage: `screen`
- Inputs:
  - `docs/audit/boundary/http_route_classification.md`
  - `docs/audit/boundary/runtime_priority_matrix.md`

## Decision

- Route ownership target: **smart_core runtime entry layer**.
- Backend sub-layer: **scene-orchestration** for entry envelope, with
  **scenario business-fact provider** retained behind adapter boundary.
- Migration strategy: **two-step**
  1. transfer route shell ownership to smart_core,
  2. keep fact assembly in scenario services via explicit provider adapter.

## Evidence

1. Both endpoints are classified as `B` (ui contract/runtime entry) in route classification.
2. Runtime priority matrix marks both as `P1` high-frequency contract fetch chain.
3. Current ownership in industry controller creates boundary ambiguity for platform runtime contract entry.

## Hard Constraints For Implement Batch

1. smart_core must own route shell and error envelope contract.
2. smart_core must not inline industry capability/dashboard business semantics.
3. scenario services remain fact provider until neutral provider interface is extracted.
4. no frontend fallback branch may be introduced to compensate migration.

## Stop Signals

- Moving provider business logic into smart_core handlers/controllers.
- Changing schema_version or payload semantics during ownership transfer.
- Merging two endpoint semantics into a single mixed contract surface.

## Next Slice Suggestion

- Implement ownership transfer for `/api/contract/capability_matrix` first, then `/api/contract/portal_dashboard` in same pattern if verification passes.

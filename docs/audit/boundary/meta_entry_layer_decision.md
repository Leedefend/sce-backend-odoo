# Meta Entry Layer Decision (P1 Gate Screen)

- Target API family: `/api/meta/*`
- Decision Stage: `screen`
- Inputs:
  - `docs/audit/boundary/http_route_inventory.md`
  - `docs/audit/boundary/http_route_classification.md`
  - `docs/audit/boundary/remediation_gate_answers.md`

## Decision

- `/api/meta/describe_model`
  - ownership target: **smart_core**
  - backend sub-layer: **scene-orchestration layer**
  - reason:
    1. route inventory labels domain as `app`, not immutable industry fact.
    2. route classification marks this endpoint as mixed runtime/meta surface (`F`).
    3. endpoint semantics align with runtime metadata envelope supply.

- `/api/meta/project_capabilities`
  - ownership target: **scenario-supplied (smart_construction_core service), not kernel-owned generic route**
  - backend sub-layer: **business-fact layer**
  - reason:
    1. route inventory domain is `capability` and directly reads business-side capability data.
    2. route classification labels it as industry business fact entry (`A`).
    3. forcing this endpoint into kernel route ownership would absorb industry semantics.

## Hard Constraints For Next Implement Batch

1. `smart_core` may own generic runtime metadata endpoint(s) only; no industry capability taxonomy hardcode.
2. Industry capability fact payload remains scenario/domain supplied; kernel only accepts extension/provider contract.
3. Do not merge `describe_model` and `project_capabilities` into one mixed endpoint during migration.
4. No frontend model-specific patch is allowed to compensate backend semantic boundary.

## Stop Signals

- Any plan to move industry capability fact semantics directly into `smart_core` kernel handlers.
- Any implementation that keeps `/api/meta/*` mixed ownership without explicit route-level split.
- Any route migration that changes capability fact meaning instead of ownership boundary.

## Next Implement Slice (P1)

- Slice 1: migrate `/api/meta/describe_model` ownership to `smart_core` with behavior compatibility.
- Slice 2: retain `/api/meta/project_capabilities` as scenario fact supply, and define extension boundary if needed.

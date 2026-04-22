# Meta Project Capabilities Provider Boundary (P1 Screen)

- Target API: `/api/meta/project_capabilities`
- Decision Stage: `screen`
- Inputs:
  - `docs/audit/boundary/http_route_inventory.md`
  - `docs/audit/boundary/http_route_classification.md`
  - `docs/audit/boundary/meta_entry_layer_decision.md`

## Decision

- Ownership stays in **scenario provider** (`smart_construction_core` domain/service path).
- Backend sub-layer target: **business-fact layer**.
- Kernel role: **consumer of provider contract only** (no business-fact embedding).

## Evidence-Based Classification

1. Route inventory marks domain as `capability` and includes project-specific fact lookup (`project_id`).
2. Route classification marks endpoint as `A` (industry business fact entry).
3. Endpoint invokes lifecycle capability service over project entity, which is domain truth, not generic runtime shell metadata.

## Provider Boundary Rules

1. Scenario provider is the single fact producer for project capability truth.
2. Kernel runtime may expose generic aggregation envelope but must not own capability fact derivation.
3. Any future migration must be provider-injection style (adapter/extension), not semantic relocation.
4. Frontend usability gaps must request backend semantic supply, not frontend model special-case.

## Stop Signals

- Moving capability derivation logic into `smart_core` controller/handler directly.
- Reclassifying endpoint as generic platform metadata without changing domain truth source.
- Introducing frontend hardcoded fallback for missing capability facts.

## Next Slice Suggestion

- Keep current route in scenario ownership.
- Add explicit provider-boundary doc reference in next implement batch if facade/adapter is introduced.

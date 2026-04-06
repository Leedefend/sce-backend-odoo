# Scenes.My Entry Layer Decision (P0 Screen)

- Target API: `/api/scenes/my`
- Decision Stage: `screen`
- Inputs:
  - `docs/audit/boundary/http_route_classification.md`
  - `docs/audit/boundary/platform_entry_occupation.md`
  - `docs/audit/boundary/runtime_priority_matrix.md`

## Decision

- Ownership target: **smart_core runtime entry** (final target).
- Backend sub-layer: **scene-orchestration layer**.
- Transition status: **staged migration required** (do not force direct kernel fact assembly in one step).

## Evidence

1. Runtime priority matrix marks `/api/scenes/my` as **P0** in scene-open main chain.
2. Platform entry occupation shows active frontend dependency on this route.
3. Current controller itself marks endpoint as legacy and points successor to `/api/v1/intent (app.init)`.

## Hard Constraints For Implement Batches

1. Kernel route migration must not absorb scenario business facts (`sc.scene` truth and permission decisions).
2. If `app.init` already supplies equivalent scene entry semantics, legacy endpoint should become platform-owned compatibility adapter.
3. If semantic equivalence is incomplete, keep fact assembly in scenario provider and migrate only ownership shell first.
4. No frontend model special-case fallback is allowed to hide backend semantic gap.

## Stop Signals

- Moving scene fact derivation logic directly into kernel with scenario-specific groups/rules.
- Disabling `/api/scenes/my` before confirming main-chain frontend compatibility.
- Implementing ownership migration without explicit compatibility path (`adapter` or `successor` mapping).

## Next Slice Suggestion

- Implement a compatibility adapter in `smart_core` for `/api/scenes/my` that prefers successor semantic supply and preserves legacy deprecation envelope.

Legacy compliance note: `/api/scenes/my` is deprecated; successor endpoint is `/api/v1/intent` with `intent=app.init`; sunset date `2026-04-30`.

# Menu Entry Layer Decision (P0 Gate Screen)

- Target API: `/api/menu/tree`
- Decision Stage: `screen`
- Inputs:
  - `docs/audit/boundary/http_route_inventory.md`
  - `docs/audit/boundary/http_route_classification.md`
  - `docs/audit/boundary/platform_entry_occupation.md`
  - `docs/audit/boundary/remediation_gate_answers.md`

## Decision

- Backend sub-layer target: **scene-orchestration layer**
- Decision reason:
  1. `/api/menu/tree` is runtime consumption semantic (navigation envelope), not immutable business truth.
  2. Current industry-root menu xmlid usage (`smart_construction_enterprise.menu_sc_root`) is industry semantic and must not be absorbed into platform kernel.
  3. Platform endpoint ownership should be restored by introducing generic orchestration contract in `smart_core`, while industry-specific root selection remains scenario-supplied.

## Hard Constraints For Next Implement Batch

1. `smart_core` must not hardcode industry xmlid/business taxonomy.
2. `smart_core` may define generic menu orchestration interface only.
3. Industry module should provide menu root semantic via extension/hook, not by owning platform route.
4. Before cutting over `/api/menu/tree`, keep compatibility behavior with explicit fallback path.

## Stop Signals

- Any proposal that directly embeds `smart_construction_enterprise.*` menu semantics into `smart_core`.
- Any implementation that changes platform route ownership without generic semantic supply path.
- Any attempt to patch frontend special-case first instead of backend semantic supply.

## Next Implement Slice (P0-2)

- Implement generic menu contract provider in `smart_core`.
- Move `/api/menu/tree` route ownership to `smart_core` controller.
- Convert industry module to provider/hook role for scenario menu root.

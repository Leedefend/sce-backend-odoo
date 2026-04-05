# ITER-2026-04-03-937

- status: PASS
- mode: screen
- layer_target: Product Release Usability Proof
- module: delivery policy guard drift screen
- risk: low
- publishability: screen_only

## Screening Classification (No Rescan)

- P0: strict equality between `policy.menu_keys` and runtime `nav_menu_keys` conflicts with native-preview extensions.
- P1: guard intent likely targets release-core policy integrity, not full nav materialization parity.
- P2: strict scene/capability parity remains valid candidates but currently unfailed.
- P3: this guard blocks release acceptance transitively (`verify.release.operator_surface.v1`).

## Selected Verify Path

- rerun only declared `verify.product.delivery_policy_guard` on `DB_NAME=sc_demo`.
- objective: confirm deterministic reproducibility before implementation.

## Decision

- PASS (screen stage complete)
- next: open `938(verify)`.

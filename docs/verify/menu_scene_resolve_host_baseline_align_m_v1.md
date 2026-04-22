# Menu Scene Resolve Host Baseline Align M v1

## Goal

Repair the menu scene resolve verification surface so the current dev runtime
can be verified without manual API base, password, or timeout overrides.

## Fixed Architecture Declaration

- Layer Target: Verification runtime surface
- Module: menu scene resolve verifier baseline
- Module Ownership: verification/runtime governance
- Kernel or Scenario: scenario
- Reason: the blocker sits in verifier baseline assumptions, not in scene
  business semantics

## Planned Change

### Verify Surface

- align host default API base to the current dev runtime entry
- align default admin password fallback with repository baseline
- increase default request timeout to match current login latency budget
- update the Makefile comment to reflect the current recommended runtime

## Result

- updated `fe_menu_scene_resolve_smoke.js` defaults to the current dev runtime
  baseline:
  - API base fallback now prefers `API_BASE` / `BASE_URL` / `E2E_BASE_URL`,
    then defaults to `http://127.0.0.1:8069`
  - default admin password fallback now uses repository baseline `admin`
  - default request timeout now uses `15000ms`
- updated the Makefile note on `verify.menu.scene_resolve` to reflect the
  current runtime baseline and to remove the stale `demo_pm/demo` guidance

## Verification

- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-20-VERIFY-MENU-SCENE-RESOLVE-HOST-BASELINE-ALIGN-M.yaml`
  - PASS
- `DB_NAME=sc_demo make verify.menu.scene_resolve`
  - PASS
  - artifacts: `artifacts/codex/portal-menu-scene-resolve/20260419T185757`
- `DB_NAME=sc_demo make verify.menu.scene_resolve.container`
  - PASS
  - artifacts: `/mnt/artifacts/codex/portal-menu-scene-resolve/20260419T185845`

## Decision

- PASS
- The remaining blocker was verified to be in the verification surface, not in
  menu scene business semantics.
- A parallel rerun briefly timed out under shared runtime pressure, but the
  acceptance path is sequential and now passes cleanly in both host and
  container modes.

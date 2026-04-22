# Menu Scene Resolve Host Repair K v1

## Goal

Repair the host `verify.menu.scene_resolve` verification surface so it can fall
back from `localhost:8070` to `localhost:8069` when the host proxy port is not
available in the current environment.

## Scope

- `scripts/verify/fe_menu_scene_resolve_smoke.js`

## Fixed Architecture Declaration

- Layer Target: Verification surface repair
- Module: menu scene resolve host verifier
- Module Ownership: scripts/verify
- Kernel or Scenario: scenario
- Reason: container mode proved menu-scene business assertions already pass, so
  the remaining host failure is connectivity-path mismatch, not menu semantics

## Implemented Changes

- host verifier now treats `localhost:8070` as the preferred API base but
  retries with `localhost:8069` when the first preflight path is unreachable
- business assertions, menu traversal, exemption handling, and scene coverage
  rules remain unchanged

## Result

- host `verify.menu.scene_resolve` can complete in environments that expose Odoo
  on `8069` but not the host proxy on `8070`
- verification-surface trust is improved without changing scene-resolution
  product behavior

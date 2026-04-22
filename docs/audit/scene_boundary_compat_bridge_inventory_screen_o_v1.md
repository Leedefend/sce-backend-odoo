# Scene Boundary Compatibility Bridge Inventory Screen O v1

## Goal

Classify the bounded compatibility-bridge candidates frozen by the scan after
the main scene-boundary alignment claim became trusted.

## Fixed Architecture Declaration

- Layer Target: Cross-layer governance screen
- Module: scene boundary compatibility bridge inventory
- Module Ownership: frontend/backend scene contract boundary
- Kernel or Scenario: scenario
- Reason: candidate collection is complete, so the next low-cost step is
  classification only

## Screen Result

- `Category A: still-real convergence targets`
  - `router registration surface`
  - `/m`, `/a`, `/f`, `/r` 仍然作为显式路由保留在
    `frontend/apps/web/src/router/index.ts`
  - although guards already redirect many ordinary entries back to scene-first,
    these route forms are still concrete compatibility authorities rather than
    purely internal mechanics
  - `entry-adjacent fallback surface`
  - `frontend/apps/web/src/pages/ModelListPage.vue`
  - `frontend/apps/web/src/views/MenuView.vue`
  - both files already prefer scene-first resolution, but still reopen native
    `action` routes when scene identity cannot be derived; this keeps them in
    the class of explicit convergence targets rather than purely internal shell
    mechanics
  - `frontend/apps/web/src/views/WorkbenchView.vue`
  - `openResolvedMenuTarget(...)` still pushes `/a/${actionId}` on unresolved
    action-only paths, so this remains adjacent to product navigation rather
    than a hidden internal-only bridge

- `Category B: acceptable internal runtime consumers for now`
  - `frontend/apps/web/src/views/ActionView.vue`
  - this file now acts as a compatibility shell that consumes carried
    `scene_key` and scene-ready identity; the scan did not show it as an
    ordinary public authority chooser, but as an internal consumer of already
    resolved compatibility traffic
  - `frontend/apps/web/src/pages/ContractFormPage.vue`
  - native/open-native fallback panels remain inside the compatibility form
    shell and are better treated as controlled internal bridges unless a later
    batch decides to retire the shell itself
  - `frontend/apps/web/src/views/RecordView.vue`
  - record reopen still contains `action` fallback, but the current role is
    inside record shell effect handling rather than ordinary top-level entry
    authority
  - `frontend/apps/web/src/layouts/AppShell.vue`
  - current action-path parsing is part of shell active-node tracking and HUD
    context matching, not a standalone navigation authority
  - `frontend/apps/web/src/app/resolvers/menuResolver.ts`
  - `resolveScenePathFromMenuResolve(...)` is already scene-first and should be
    treated as the normalization helper that compatibility callers depend on,
    not as a direct convergence blocker
  - `frontend/apps/web/src/app/resolvers/sceneRegistry.ts`
  - native route prefixes and semantic-route normalization are now frozen as
    compatibility-input handling within the scene registry runtime, not as
    independent product entry authorities

- `Category C: no current evidence of backend semantic-supply blocker`
  - based on the scan plus the already trusted live verification, the remaining
    inventory is dominated by frontend compatibility authorities and shell
    bridges
  - this screen did not surface a new action-only scene-identity gap that would
    force another backend semantic-supply batch before any further frontend
    convergence work

This screen classifies only the candidates frozen by Scan N. It does not claim
that all compatibility bridges are removed, and it does not reopen the
repository to search for more.

## Verification

- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-20-SCENE-BOUNDARY-COMPAT-BRIDGE-INVENTORY-SCREEN-O.yaml`
  - PASS
- `git diff --check -- agent_ops/tasks/ITER-2026-04-20-SCENE-BOUNDARY-COMPAT-BRIDGE-INVENTORY-SCREEN-O.yaml docs/audit/scene_boundary_compat_bridge_inventory_screen_o_v1.md docs/ops/iterations/delivery_context_switch_log_v1.md`
  - PASS

## Decision

- screen complete
- strongest bounded conclusion after trusted live verify:
  - main scene boundary alignment is trusted
  - compatibility bridges are not fully retired
  - the next optional convergence line, if opened, should stay frontend-led and
    target router/entry-adjacent/workbench authorities first

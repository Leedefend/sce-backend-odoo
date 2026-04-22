# Scene Boundary Compatibility Bridge Inventory Scan N v1

## Goal

Run a bounded inventory scan for remaining frontend compatibility bridges after
the main scene-boundary alignment claim has been upgraded to trusted.

## Fixed Architecture Declaration

- Layer Target: Cross-layer governance scan
- Module: scene boundary compatibility bridge inventory
- Module Ownership: frontend/backend scene contract boundary
- Kernel or Scenario: scenario
- Reason: the main alignment claim is already trusted, so the next low-cost step
  is to inventory residual bridge candidates without mixing scan and screen

## Scan Scope

- router registration surface
- entry-adjacent fallback surface
- compatibility-shell internal navigation surface
- session/router normalization surface

## Scan Result

- `router registration surface`
  - `frontend/apps/web/src/router/index.ts`
  - native/compat route entries still remain registered at `/m/:menuId`,
    `/a/:actionId`, `/f/:model/:id`, `/r/:model/:id`
  - `beforeEach` already applies scene-first redirection for `menu`, `action`,
    and `record`, but the compatibility route forms are still present as public
    runtime surfaces
- `entry-adjacent fallback surface`
  - `frontend/apps/web/src/pages/ModelListPage.vue`
  - resolves `scene-first` through `findSceneByEntryAuthority(...)`, then still
    falls back to `router.replace({ name: 'action', ... })` when no scene can be
    derived
  - `frontend/apps/web/src/views/MenuView.vue`
  - resolves carried/menu node scene key and action-derived scene first, but
    still retains `name: 'action'` fallbacks in both leaf and redirect branches
- `compatibility-shell internal navigation surface`
  - `frontend/apps/web/src/views/WorkbenchView.vue`
  - `openResolvedMenuTarget(...)` prefers `resolveScenePathFromMenuResolve(...)`
    but still pushes `/a/${actionId}` when no scene path resolves
  - `frontend/apps/web/src/views/RecordView.vue`
  - record/action reopen logic still contains `name: 'action'` fallback after
    `findSceneByEntryAuthority(...)`
  - `frontend/apps/web/src/views/ActionView.vue`
  - continues to consume `scene_key` / `scene` carried context and
    scene-ready-by-scene-key runtime inside the compatibility action shell
  - `frontend/apps/web/src/pages/ContractFormPage.vue`
  - still exposes native-fallback panels and form-native/open-native behavior in
    the compatibility form shell
- `session/router normalization surface`
  - `frontend/apps/web/src/app/resolvers/menuResolver.ts`
  - `resolveScenePathFromMenuResolve(...)` is now scene-first and only returns
    compatibility null when no scene can be derived from redirect/action
  - `frontend/apps/web/src/app/resolvers/sceneRegistry.ts`
  - semantic route normalization remains frozen around `/s/${sceneKey}` with
    native prefixes `/a/`, `/f/`, `/r/` still treated as canonical compatibility
    inputs
  - `frontend/apps/web/src/layouts/AppShell.vue`
  - active-node matching still parses current action path (`/a/...`) as one
    valid shell-context source alongside scene/menu context

This scan only records candidate surfaces. It does not classify whether these
remaining bridges are acceptable internals, true product-entry dependencies, or
future retirement targets.

## Verification

- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-20-SCENE-BOUNDARY-COMPAT-BRIDGE-INVENTORY-SCAN-N.yaml`
  - PASS
- bounded `rg` scan across router/pages/views/app/layouts
  - PASS
- `git diff --check -- agent_ops/tasks/ITER-2026-04-20-SCENE-BOUNDARY-COMPAT-BRIDGE-INVENTORY-SCAN-N.yaml docs/audit/scene_boundary_compat_bridge_inventory_scan_n_v1.md docs/ops/iterations/delivery_context_switch_log_v1.md`
  - PASS

## Decision

- scan complete
- next eligible low-cost step is a separate `screen` batch that classifies the
  recorded candidates without reopening repository-wide scan scope

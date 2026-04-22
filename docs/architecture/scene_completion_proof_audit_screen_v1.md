# Scene Completion Proof Audit Screen v1

## Goal

Classify scanned proof candidates into:

- acceptable scene-oriented internal mechanics
- remaining gaps that still block a strict repository-level completion claim

This screen uses only the bounded candidate set from
`scene_completion_proof_audit_scan_v1.md`.

## Fixed Architecture Declaration

- Layer Target: Cross-layer governance screen
- Module: scene completion-proof audit
- Module Ownership: scene contract proof boundary
- Kernel or Scenario: scenario
- Reason: decide whether scanned candidates still block a strict repository-wide
  completion statement

## Classification Rule

- acceptable internal mechanic:
  candidate still references action/model/menu/record details, but only as
  bounded transport or runtime mechanics inside a scene-oriented consumer chain
- blocking proof gap:
  candidate still leaves room for a page/load chain to be understood as not yet
  proven to consume only orchestrated scene output

## Screen Result

### Acceptable Scene-Oriented Internal Mechanics

- `[frontend/apps/web/src/api/contract.ts](/mnt/e/sc-backend-odoo/frontend/apps/web/src/api/contract.ts:52)` `op: 'action_open'`
- `[frontend/apps/web/src/api/contract.ts](/mnt/e/sc-backend-odoo/frontend/apps/web/src/api/contract.ts:91)` `op: 'model'`
  These are transport-level contract loader mechanics. By themselves they do not
  prove a boundary violation, because the current architecture still allows
  scene-oriented consumers to request contract slices by action/model while
  staying inside the governed contract pipeline.

- `[frontend/apps/web/src/app/init.ts](/mnt/e/sc-backend-odoo/frontend/apps/web/src/app/init.ts:68)` `session.loadAppInit()`
- `[frontend/apps/web/src/app/resolvers/sceneRegistry.ts](/mnt/e/sc-backend-odoo/frontend/apps/web/src/app/resolvers/sceneRegistry.ts:521)` `getSceneByKey(...)`
- `[frontend/apps/web/src/app/resolvers/sceneRegistry.ts](/mnt/e/sc-backend-odoo/frontend/apps/web/src/app/resolvers/sceneRegistry.ts:531)` `findSceneByEntryAuthority(...)`
  These are core scene boot/normalization mechanics and are part of the proof
  chain, not evidence against it.

### Remaining Blocking Proof Gaps

- `[frontend/apps/web/src/pages/ContractFormPage.vue](/mnt/e/sc-backend-odoo/frontend/apps/web/src/pages/ContractFormPage.vue:3963)` and `[frontend/apps/web/src/pages/ContractFormPage.vue](/mnt/e/sc-backend-odoo/frontend/apps/web/src/pages/ContractFormPage.vue:3981)`:
  ContractFormPage still loads by direct `actionId/model` contract requests.
  Even though it now carries `scene_key` and `record_id`, this bounded audit
  still cannot prove that every form-page entry is conceptually scene-first
  rather than "scene-compatible but still action/model-driven".

- `[frontend/apps/web/src/views/ActionView.vue](/mnt/e/sc-backend-odoo/frontend/apps/web/src/views/ActionView.vue:1068)` and `[frontend/apps/web/src/views/ActionView.vue](/mnt/e/sc-backend-odoo/frontend/apps/web/src/views/ActionView.vue:1087)`:
  ActionView still accepts native action identity as a primary runtime input and
  only then reconstructs scene context. That means the repository still contains
  a major consumer chain that is not yet proven to be scene-first by design.

- `[frontend/apps/web/src/stores/session.ts](/mnt/e/sc-backend-odoo/frontend/apps/web/src/stores/session.ts:1309)` compatibility landing fallback to `/a/${actionId}`:
  Even if bounded as fallback, this still prevents a strict statement that
  startup landing is fully proven scene-only for all cases.

- `[frontend/apps/web/src/router/index.ts](/mnt/e/sc-backend-odoo/frontend/apps/web/src/router/index.ts:56)` `[frontend/apps/web/src/views/WorkbenchView.vue](/mnt/e/sc-backend-odoo/frontend/apps/web/src/views/WorkbenchView.vue:375)` `[frontend/apps/web/src/views/MenuView.vue](/mnt/e/sc-backend-odoo/frontend/apps/web/src/views/MenuView.vue:73)`:
  These menu-entry reconstruction paths still rely on `resolveMenuAction(...)`.
  They may be compatible with scene-first behavior after normalization, but they
  still show that a repository-wide proof of "no remaining native menu/action
  dependence in ordinary entry reconstruction" has not been completed.

## Final Proof Decision

The strict statement:

> "scene-oriented convergence is fully complete across the repository"

is still **not proven**.

The blocking proof gaps are no longer the already-cleaned route guards
themselves. They are now concentrated in:

- ActionView / ContractFormPage contract-loading chains
- startup/landing action fallback
- menu-entry reconstruction paths that still begin from native menu/action facts

## Frozen Next-Step Direction

If the team wants a strict "all complete" statement, the next bounded audit/fix
line should focus on proving or eliminating these three proof-gap categories:

1. `ActionView` and `ContractFormPage` direct action/model loader dependence
2. `session.resolveCompatibilityMenuPath()` action fallback at landing
3. `resolveMenuAction(...)`-based entry reconstruction in router/workbench/menu

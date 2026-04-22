# Scene Completion Proof Recheck Screen v1

## Goal

Re-evaluate the remaining proof gaps after the ActionView/ContractFormPage
scene-proof fix.

This screen uses the existing completion-proof audit chain plus the latest
bounded fix. It does not reopen a broad repository scan.

## Fixed Architecture Declaration

- Layer Target: Cross-layer governance screen
- Module: scene completion proof recheck
- Module Ownership: scene contract proof boundary
- Kernel or Scenario: scenario
- Reason: re-evaluate whether the latest action/form proof-fix is enough to
  remove that category from the strict-completion blocker set

## Recheck Basis

This recheck uses only:

- `scene_completion_proof_audit_screen_v1.md`
- `scene_proof_fix_action_form_e_v1.md`
- latest code state of:
  - `frontend/apps/web/src/api/contract.ts`
  - `frontend/apps/web/src/views/ActionView.vue`
  - `frontend/apps/web/src/pages/ContractFormPage.vue`

## Recheck Result

### 1. Action/Form loader dependence is no longer the primary blocking proof gap

Observed updated state:

- `api/contract` action loader now accepts and forwards `sceneKey`
- `ContractFormPage` now passes `sceneKey` through both action and model
  contract reads
- `ActionView` now resolves `sceneReadyEntry` by `sceneKey` first and only then
  falls back to `actionId/menuId`

Recheck decision:

- this category still contains transport-level action/model mechanics
- but it no longer presents as a strong proof blocker for the strict completion
  statement in the same way as before
- it is now better classified as an acceptable scene-oriented internal mechanic
  with bounded legacy transport semantics

### 2. Remaining strict-completion blockers are now concentrated in two areas

#### A. landing fallback still allows `/a/${actionId}`

- `session.resolveCompatibilityMenuPath()` still falls back to `/a/${actionId}`
  when no scene key is available

Why it still blocks strict completion:

- startup and landing are still not fully proven scene-only for all cases

#### B. menu-entry reconstruction still begins from native menu/action facts

- router guard still reconstructs from `resolveMenuAction(...)`
- workbench still reconstructs from `resolveMenuAction(...)`
- menu page still reconstructs from `resolveMenuAction(...)`

Why it still blocks strict completion:

- even if the result often normalizes back into scene-first navigation, the
  proof chain still begins from native menu/action reconstruction rather than a
  fully frozen scene-only entry source

## Final Recheck Decision

After the latest proof-fix, the remaining strict-completion blockers are now
effectively narrowed to:

1. landing `/a` fallback
2. `resolveMenuAction(...)`-based menu-entry reconstruction paths

So the strongest current statement is:

> the main scene-first line is closed, action/form proof gaps are materially
> reduced, and the remaining strict-completion blockers are now narrowed to
> landing fallback plus menu-entry reconstruction.

## Frozen Next-Step Direction

If the team wants to keep pushing toward a strict "all complete" statement, the
next bounded fix line should target:

- `session.resolveCompatibilityMenuPath()` action fallback
- router/workbench/menu reconstruction paths rooted in `resolveMenuAction(...)`

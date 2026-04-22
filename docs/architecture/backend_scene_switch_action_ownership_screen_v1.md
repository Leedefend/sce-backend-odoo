# Backend Scene Switch Action Ownership Screen v1

Status: Governance Screen  
Scope: backend semantic supply for `projects.list`

## 1. Purpose

This screen answers two backend-side questions required by frontend
convergence:

1. Does backend already provide a canonical scene-switch semantic surface for
   `projects.list`?
2. Does backend already provide a canonical ownership surface for top-level
   scene actions so the frontend can legally merge or relocate them?

## 2. Inputs Checked

Sources screened:

- [scene_contract_spec_v1.md](/mnt/e/sc-backend-odoo/docs/architecture/scene_contract_spec_v1.md)
- [scene_contract_standard_v1.md](/mnt/e/sc-backend-odoo/docs/architecture/scene_contract_standard_v1.md)
- [scene_ready_contract_builder.py](/mnt/e/sc-backend-odoo/addons/smart_core/core/scene_ready_contract_builder.py)
- [sceneRegistry.ts](/mnt/e/sc-backend-odoo/frontend/apps/web/src/app/resolvers/sceneRegistry.ts)
- latest `projects.list` runtime evidence:
  [summary.json](/mnt/e/sc-backend-odoo/artifacts/playwright/high_frequency_pages_v2/20260419T074303Z/summary.json)

## 3. Current Backend Supply Facts

### 3.1 Search Surface

Backend clearly supplies:

- `search_surface`
- default sort
- filters
- group-by
- searchpanel

Conclusion:

- `projects.list` list toolbar search/filter/group/sort semantics already have
  a valid backend source.

### 3.2 Action Surface

Backend clearly supplies:

- `action_surface`
- `actions.primary_actions`
- `actions.recommended_actions`
- page-level `global_actions` through page contract assembly

Conclusion:

- scene-level actions are backend-backed semantics.
- the remaining problem is not "missing action semantics".
- the remaining problem is ownership placement between scene layer and list
  work-surface layer.

### 3.3 Scene Switch Surface

Screen result:

- current public scene/scene-ready specifications define `actions`,
  `search_surface`, `permission_surface`, `workflow_surface`, and related page
  rendering payloads
- current screened specs do **not** define a canonical `scene_switch_surface`,
  `switch_surface`, `available_sibling_scenes`, or equivalent released field
  for `projects.list`
- current frontend `SceneView` switch chips come from a hardcoded local map,
  not from backend supply

Conclusion:

- backend does **not** currently provide a canonical scene switch semantic
  surface for `projects.list`

## 4. Ownership Decision

### 4.1 Top Action Ownership

Decision:

- semantic supply exists
- no backend fact gap for basic action existence
- frontend convergence may merge or relocate those actions only after an owner
  rule is frozen

Interpretation:

- this is primarily a frontend ownership placement problem, not a backend
  existence problem

### 4.2 Scene Switch Ownership

Decision:

- semantic supply is missing
- frontend may not continue using local hardcoded scene-switch rules

Interpretation:

- if product still requires `projects.list <-> projects.ledger` switching as a
  first-class top control, backend must add a canonical switch surface in a
  dedicated batch
- if product does not require that control, frontend must remove the current
  hardcoded switch strip

## 5. Supply Gap Summary

| Semantic surface | Current backend supply | Gap status | Next action |
| --- | --- | --- | --- |
| list search/filter/group/sort | present | no gap | frontend may consume |
| top scene actions | present | no existence gap | freeze owner and merge policy |
| scene switch between sibling scenes | absent | real gap | backend decide supply or frontend remove |

## 6. Follow-Up Batch Input

### Batch C2A: Product Decision Screen

Question:

- Is scene switching between `projects.list` and `projects.ledger` still a
  required user-facing control?

Possible outcomes:

- `NO`: remove frontend hardcoded switch strip
- `YES`: continue to backend supply batch

### Batch C2B: Backend Semantic Supply Implement

Only if product decision is `YES`.

Goal:

- add a canonical scene switch surface for sibling scenes
- bind it to scene-ready / page-scene semantics
- keep it additive and generic

### Batch D1: Frontend Structural Convergence

Goal:

- merge backend-backed actions into the single list work-surface toolbar if
  owner rules allow
- delete any switch strip not backed by backend supply

## 7. One-Line Screen Result

Backend already supplies list toolbar semantics and scene action semantics, but
it does not currently supply a canonical scene switch semantic surface for
`projects.list`.

## 8. Implementation Closure Note

The follow-up implementation batch now closes this gap by:

- carrying `related_scenes` through scene-ready construction
- materializing an additive backend `switch_surface`
- keeping frontend switch rendering dependent on backend supply rather than
  local hardcoded maps

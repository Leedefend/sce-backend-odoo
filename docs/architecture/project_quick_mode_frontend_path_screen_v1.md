# Project Quick Mode Frontend Path Screen V1

## Problem

Quick mode is a real Odoo-side project creation mode, but the frontend still
keeps a residual `route.query.intake_mode === "quick"` fallback in
`ContractFormPage.vue`.

Before implementing backend semantic supply, we need to know which frontend
runtime path actually reaches quick mode.

## Current Frontend Fact

### `projects.intake` handoff is standard-only

`frontend/apps/web/src/views/ProjectsIntakeView.vue` currently always routes to:

- `/f/project.project/new`

with query containing:

- `scene_key = projects.intake`
- `menu_xmlid = smart_construction_core.menu_sc_project_initiation`
- `intake_mode = undefined`

Meaning:

- this handoff is explicitly wired to the standard project initiation menu
- quick mode is not represented in this scene handoff

### frontend baseline constants only expose the standard initiation menu

`frontend/apps/web/src/app/projectCreationBaseline.ts` defines:

- `PROJECT_INITIATION_MENU_XMLID = smart_construction_core.menu_sc_project_initiation`

It does not define:

- quick-create menu xmlid
- quick-create action identity

Meaning:

- the frontend project-creation baseline currently has no first-class quick
  mode identity carrier

### `MenuView` special-cases only the standard intake entry

`frontend/apps/web/src/views/MenuView.vue` identifies project intake through:

- `scene_key == projects.intake`
- or `menu_xmlid == smart_construction_core.menu_sc_project_initiation`

When that predicate matches, it redirects to:

- `/s/projects.intake`

Meaning:

- only the standard initiation menu is redirected into the intake scene handoff
- quick-create menu is not mapped into that scene path

## Current Odoo/Menu Fact

The repository still defines a real quick-create menu/action:

- `menu_sc_project_quick_create`
- `action_project_initiation_quick`
- action context includes `intake_mode = "quick"`

Meaning:

- quick mode exists in backend/menu truth
- but the frontend's scene handoff chain is not explicitly wired to it

## Runtime Path Decision

The most likely current path split is:

### Standard mode

- menu -> `MenuView` special-case -> `/s/projects.intake` -> `ProjectsIntakeView`
  -> `/f/project.project/new` with standard initiation identity

### Quick mode

- menu leaf -> action route/direct action handling
- not via `projects.intake` handoff

This matches the current code facts:

- quick menu/action exists
- but frontend handoff constants and intake scene redirect only know the
  standard initiation menu

## Classification

This means the remaining quick-mode issue is not:

- a missing standard intake scene feature

It is:

- a split entry-path problem

More precisely:

- standard mode currently uses the scene handoff chain
- quick mode appears to remain on the menu/action direct-open chain

## Implementation Consequence

The next quick-mode contract batch must attach semantics to the actual quick
entry path, not to the standard `projects.intake` handoff by assumption.

There are two valid strategies:

### Strategy A: make quick mode a first-class scene handoff

- introduce explicit quick menu/action identity into frontend scene handoff
- route quick creation through a scene-aware entry path
- let backend scene governance emit `create_flow_mode = "quick"`

### Strategy B: keep quick mode on direct action path

- preserve quick menu/action direct-open behavior
- make backend contract governance detect quick entry from action/menu identity
  on that path
- let `ContractFormPage` consume explicit quick semantics there

## Recommended Next Step

Prefer Strategy B first.

Reason:

- it matches the current split path with the smallest movement
- it avoids forcing quick mode into the standard intake scene before its
  semantics are carried cleanly

## Final Decision

The current frontend does not send quick mode through the same handoff chain as
standard intake.

So the next quick-mode implementation should target:

- the real quick menu/action direct entry path

not:

- the standard `projects.intake` handoff path by assumption

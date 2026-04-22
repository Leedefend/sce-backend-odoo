# Project Quick Mode Action Path Screen V1

## Problem

We already know quick mode does not currently travel through the same frontend
scene handoff as standard project intake.

The remaining question is:

- after quick-create menu/action is selected, which frontend consumer receives
  the request first?

This matters because backend quick semantics must be attached to the correct
consumer path.

## Current Route Fact

`frontend/apps/web/src/router/index.ts` defines:

- `/a/:actionId` -> `ActionViewShell`
- `/f/:model/:id` -> `ContractFormPage`

Meaning:

- direct action navigation lands on `ActionView` first
- direct form navigation lands on `ContractFormPage`

## Current Menu Resolution Fact

`frontend/apps/web/src/views/MenuView.vue` resolves ordinary leaf menus by:

- extracting `action_id`
- redirecting to `/a/:actionId`

The only explicit project-intake special-case is:

- `menu_xmlid == smart_construction_core.menu_sc_project_initiation`
- or `scene_key == projects.intake`

That special-case redirects to:

- `/s/projects.intake`

Quick-create menu is not included in that special-case.

Meaning:

- quick-create menu follows the normal leaf-menu action path
- it does not enter the standard intake scene handoff

## Current Quick Menu Fact

Backend menu configuration still defines:

- `menu_sc_project_quick_create`
- `action_project_initiation_quick`

Because MenuView does not special-case this menu into `/s/projects.intake`,
the expected frontend runtime path is:

```text
/m/<quick-menu-id>
  -> MenuView resolves leaf action
  -> /a/<quick-action-id>
  -> ActionViewShell / ActionView
```

## Action Resolution Fact

`frontend/apps/web/src/app/resolvers/actionResolver.ts` resolves action metadata
and action contract from:

- `loadActionContract(actionId)`

This confirms that the direct quick-create path is first treated as an action
contract consumer path, not as a direct form-route consumer path.

## Decision

The first frontend landing surface for quick mode is:

- `ActionView`

not:

- `ProjectsIntakeView`
- standard intake scene handoff
- direct `ContractFormPage` route by default

## Implementation Consequence

The next quick-mode semantic batch should first target:

- the action contract / action consumer path

Specifically:

- ensure the quick-create action contract or its downstream takeover path emits
  explicit quick-mode semantics

Only after that should we decide whether additional form-route cleanup is still
needed in `ContractFormPage`.

## Final Result

Quick mode is not just "another intake scene form".

In the current frontend runtime, it is primarily:

- a direct menu leaf -> action route -> `ActionView` path

So backend quick semantics must be attached to that path first.

# Main Entry Convergence v1

## Release Decision

`Main Entry Convergence v1` defines the released product entry as:
- primary: `project.management`
- auxiliary: `my_work.workspace`

## Released Rules

### Login

- project-bearing PM users should land on `project.management`
- users without a resolvable project may fall back to `my_work.workspace`

### Dashboard

The first screen must explain:
- where the project is
- why it is in the current state
- what should be done next
- whether a risk blocks or warns the mainline

### Action Return

Mainline actions launched from the cockpit should prefer returning to `project.management`, not `my_work.workspace`.

## Required Guards

- `make verify.product.main_entry_convergence_guard`
- `make verify.portal.project_dashboard_primary_entry_browser_smoke.host`
- `make verify.product.main_entry_convergence.v1`

## Non-Goals

- no platform-layer expansion
- no new business modules
- no release/operator/protocol redesign
- no large UI rewrite

# Project Task Form Route Recovery v1

## Goal

Recover the custom frontend `project.task` detail route so the converged
high-frequency walkthrough can open task detail with the normal detail shell.

## Scope

- `frontend/apps/web/src/pages/ContractFormPage.vue`
- `scripts/verify/high_frequency_pages_v2_walkthrough.mjs`
- walkthrough evidence and related frontend docs

## Fixed Architecture Declaration

- Layer Target: Frontend contract-consumer runtime
- Module: `project.task` form route consumer
- Module Ownership: Contract form page + walkthrough verifier
- Kernel or Scenario: scenario
- Reason: backend contract/action/data are already valid; remaining failure is
  in frontend route consumption/loading

## Initial Evidence

- `ui.contract(action_open=457, record=1)` returns `ok=true` with
  `model=project.task`, `view_type=form`
- `ui.contract(model=project.task, view_type=form, record=1)` returns `ok=true`
- `api.data(read project.task#1)` returns successfully within sub-second latency
- Browser route `/r/project.task/1?db=sc_demo&action_id=457` does not render the
  normal detail container or the back action

## Recovery Focus

1. Identify which frontend load stage hangs for `project.task`
2. Reduce or defer non-critical relation hydration if it blocks the initial form shell
3. Re-run the real walkthrough and update browser evidence

## Batch Result

- Implemented a narrow `ContractFormPage` consumer change:
  - relation option hydration no longer blocks the first detail shell render
  - relation hydration now runs in the background behind a route-local load token
- Frontend verification:
  - `pnpm -C frontend/apps/web typecheck:strict` PASS
  - `pnpm -C frontend/apps/web build` PASS
- Browser evidence after the change still does not reach task detail:
  - direct probe screenshot: `artifacts/playwright/high_frequency_pages_v2/direct-task-probe/task-route-probe.png`
  - route stayed at `/r/project.task/1?db=sc_demo&action_id=457`
  - page text stayed empty
  - `window.__scFormDebug` was still `null`
  - console showed `system.init` request diagnostics, but the app body remained an empty `#app` shell

## Current Stop Boundary

The earlier blank-shell blocker has now been recovered by a startup-layer batch:
direct routes no longer stay as an empty `#app` shell at short wait windows.
`project.task` detail can mount successfully after a long wait, so the
remaining issue is startup latency rather than `ContractFormPage` mount failure.

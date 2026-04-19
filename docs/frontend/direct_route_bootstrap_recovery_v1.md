# Direct Route Bootstrap Recovery v1

## Goal

Recover authenticated direct record routes that currently leave the app as an
empty `#app` shell before any route component mounts.

## Scope

- `frontend/apps/web/src/main.ts`
- `frontend/apps/web/src/app/init.ts`
- `frontend/apps/web/src/router/index.ts`
- `frontend/apps/web/src/stores/session.ts`

## Fixed Architecture Declaration

- Layer Target: Frontend contract-consumer runtime
- Module: startup/bootstrap direct-route recovery
- Module Ownership: main/init/router/session
- Kernel or Scenario: scenario
- Reason: browser evidence now shows the remaining blocker occurs before
  `ContractFormPage` mounts

## Entry Evidence

- `login` over `/api/v1/intent` succeeds for `wutao / demo`
- `system.init` over `/api/v1/intent` succeeds with authenticated bearer token
- Direct browser probe of `/r/project.task/1?db=sc_demo&action_id=457` still
  shows an empty app shell
- `window.__scFormDebug === null`, so the page component has not mounted

## Recovery Focus

1. Trace startup order among `main.ts`, `bootstrapApp()`, router guards, and
   session restore/init
2. Identify why authenticated direct routes do not progress from empty shell to
   mounted app/component
3. Recover generic bootstrap behavior without introducing model-specific logic

## Latest Findings

- Browser-side manual `system.init` fetch from the login page succeeds, but is
  slow:
  - authenticated `fetch('/api/v1/intent?db=sc_demo', system.init)` returned
    `200` after about `17.3s`
- Direct route no longer stays as a blank `#app` shell after the startup
  overlay recovery:
  - 8s probe state:
    - `hasOverlay=true`
    - `hasLoading=true`
    - `hasReturn=false`
    - screenshot:
      `artifacts/playwright/high_frequency_pages_v2/direct-task-probe/task-route-bootstrap-8s.png`
- Long-wait direct route probe confirms the route eventually mounts the task
  detail page:
  - total elapsed about `38.6s`
  - `hasReturn=true`
  - `loadStage=reload_done`
  - `status=ok`

## Current Residual Risk

The generic blank-shell failure has been recovered into a visible startup
loading state, but the startup chain remains slow for authenticated direct
routes. The next investigation line should focus on startup latency rather than
page-mount failure.

## Latency Attribution

Shell-side timing confirms the remaining delay is not mainly caused by the Vite
proxy hop:

- `proxy_5174 system.init`: about `18.1s`
- `backend_8069 system.init`: about `20.2s`
- response payload size: about `587 KB`

So the frontend startup recovery batch can stop here; remaining improvement
belongs to backend/runtime performance on `system.init`.

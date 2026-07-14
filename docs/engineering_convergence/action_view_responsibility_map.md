# Action View Responsibility Map

Date: 2026-07-14
Owner: Frontend owner
Target file: `frontend/apps/web/src/views/ActionView.vue`
Current size: 3,681 lines
Phase: Stage 6 business category create nav query split

## Purpose

`ActionView.vue` is the route-level shell for action, list, kanban, scene, and
activity surfaces. It consumes page/action/list contracts, route query state,
session menu state, and scene state, then renders action surfaces, runs list
preferences, executes batch/action commands, and keeps route state in sync.

It must remain an orchestration shell. It may coordinate contracts, route
updates, and user feedback, but it must not become the source of backend
permission truth, field order truth, action executability, Odoo model semantics,
or industry-owned business rules.

## Route Entry

| Entry point | Responsibility | Boundary |
| --- | --- | --- |
| `ActionView.vue` | Route component for action/list/kanban/scene surfaces. | May orchestrate route state, session state, page contracts, and view runtimes. |
| `usePageContract('action')` | Consumes action-page contract text, actions, sections, and targets. | Contract consumption only; no local permission invention. |
| `useActionPageModel` | Builds the current action-page view model from records, contracts, and runtime state. | View-model assembly; no API writes. |
| `useActionViewActionRuntime` | Executes action commands and navigation effects. | Keep transaction boundary in runtime until behavior coverage exists. |

## Responsibility Bands

| Band | Current responsibility | Extraction direction |
| --- | --- | --- |
| Template composition | Status panels, action toolbar, quick filters, group summary, list surface, kanban surface, and empty/error states. | Keep as page template until smaller surface components have behavioral coverage. |
| Page contract and session binding | `usePageContract('action')`, session menu tree, action meta, scene identity, and section text/style contracts. | Keep contract consumption explicit in the route shell. |
| Route/query runtime | Route preset application, activity route key, menu/action/scene query sync, group/filter/view route sync, and reload sequencing. | Extract only pure route-query builders first. |
| Contract/list/kanban state | Records, totals, aggregates, list columns, kanban fields, group rows, and `useActionPageModel` view model. | Keep state in the page until model tests cover list and kanban projections. |
| Selection and batch actions | Selected IDs, if-match/idempotency maps, archive/activate/delete policy, batch feedback, and refresh. | Do not move mutation transaction yet. Extract pure guard/request builders only. |
| Contract actions and navigation | Header actions, focus actions, create record flow, business category picker, internal route navigation, external URL navigation. | Keep navigation side effects at current boundary. |
| List preferences | Visibility/order/width load, save, optimistic status, timer cleanup, and preference policy application. | Extract pure normalization and scope builders before moving API calls. |
| Lifecycle and error state | Mounted load, menu-only redirect, project context event listener, route watches, retained route full path, render error state. | Keep watch/reload chain in page until regression coverage exists. |
| Activity runtime query normalization | `normalizeActivityRuntimeRouteQuery` whitelists route query keys and normalizes activity runtime query state. | Pure helper in `actionViewRouteRuntime.ts`; no router, API, session, or notification access. |
| Activity runtime route state builder | `buildActivityRuntimeRouteState` merges current route query, local list state, and route-sync extras before normalization. | Pure helper in `actionViewRouteRuntime.ts`; page remains responsible for session writes. |
| Activity route key builder | `buildActionActivityRouteKey` builds the action/menu activity runtime key from route params and query values. | Pure helper in `actionViewRouteRuntime.ts`; page remains responsible for reading route state. |
| Button status projection | `applyActionViewV2ButtonStatus` maps v2 button status contracts onto action presentation buttons. | Pure helper in `actionViewContractActionRuntime.ts`; page remains responsible for collecting the current contract status map. |
| Business category create query | `buildBusinessCategoryCreateNavQuery` maps create-picker category metadata into navigation query defaults. | Pure helper in `navigationContext.ts`; page remains responsible for `resolveCarryQuery` and router navigation. |

## Current Side-Effect Boundaries

These functions own side effects today and should not be moved as a batch:

| Boundary | Side effect |
| --- | --- |
| `openCreateRecordWithBusinessCategory` | Builds create-route query and opens the business category flow. |
| `openCreateRecord` | Performs create navigation through `router.push`. |
| `handleSceneBlockAction` | Runs scene block action routing and external navigation. |
| `runBatchPolicyAction` | Runs archive/activate/delete API mutations, confirmation, busy state, feedback, and reload. |
| `handleSaveFavorite` | Persists action favorite state and refreshes local UI state. |
| `applyRoutePatchAndReload` | Applies route patches and triggers reload. |
| `syncRouteStateAndReload` | Synchronizes route state and triggers reload. |
| `restartLoadWithRouteSync` | Restarts load after route-sync decisions. |
| `loadListColumnPreference` | Reads user list preferences and applies visibility/order/width state. |
| `handleListColumnVisibilityChange` | Saves visibility preference changes. |
| `handleListColumnOrderChange` | Saves column order preference changes. |
| `handleListColumnWidthsChange` | Saves column width preference changes and updates timer-backed status. |
| `handleToggleRecordFavorite` | Writes record-level favorite field state and rolls back on error. |
| `redirectMenuOnlyRouteIfNeeded` | Resolves menu-only routes and performs canonical `router.replace` navigation. |
| `onMounted` and route watches | Own initial load, project context listener, route reloads, and cleanup. |

Side-effect tokens intentionally tracked by the guard include `router.push`,
`router.replace`, `window.open`, `window.location.assign`, and
`PROJECT_CONTEXT_CHANGED_EVENT`.

## Do Not Move Yet

Do not move these responsibilities before behavior coverage exists:

- route navigation transactions;
- batch mutation transactions;
- list preference load/save transactions;
- record favorite mutation;
- lifecycle/watch project-context reload chain;
- external navigation with `window.open` and `window.location.assign`;
- menu-only redirect and canonical route replacement;
- action runtime execution through `useActionViewActionRuntime`.

## Stage 1 Target

Stage 1 is complete:

- document the current responsibility bands and side-effect boundaries;
- add a guard so the map remains connected to `ci.local.quick`;
- do not move router, API, session, lifecycle, or window side effects.

## Stage 2 Target

Stage 2 is complete:

- `actionViewRouteRuntime.ts` owns the pure
  `normalizeActivityRuntimeRouteQuery` helper;
- `ActionView.vue` imports the helper and keeps only session write
  orchestration in `updateActivityRuntimeQueryFromRoute` and
  `syncRouteListState`;
- no router, API, session, lifecycle, window, or notification side effects were
  moved.

## Stage 3 Target

Stage 3 is complete:

- `actionViewRouteRuntime.ts` also owns the pure
  `buildActivityRuntimeRouteState` helper;
- `ActionView.vue` keeps `syncRouteListState` as orchestration only:
  route-preset sync first, activity runtime route state build second, session
  write last;
- `ActionView.vue` is locked at `<=3736` lines;
- no router, API, session, lifecycle, window, or notification side effects were
  moved.

## Stage 4 Target

Stage 4 is complete:

- `actionViewRouteRuntime.ts` also owns the pure
  `buildActionActivityRouteKey` helper;
- `ActionView.vue` keeps `currentActionActivityRouteKey` as route-read
  orchestration only;
- `ActionView.vue` is locked at `<=3735` lines;
- no router, API, session, lifecycle, window, or notification side effects were
  moved.

## Stage 5 Target

Stage 5 is complete:

- `actionViewContractActionRuntime.ts` owns the pure
  `stableActionContractId`, `resolveActionViewV2ButtonStatus`, and
  `applyActionViewV2ButtonStatus` helpers;
- `ActionView.vue` keeps only presentation runtime wiring and current contract
  status collection;
- `ActionView.vue` is locked at `<=3695` lines;
- no router, API, session, lifecycle, window, or notification side effects were
  moved.

## Stage 6 Target

Stage 6 is complete:

- `navigationContext.ts` owns the pure
  `buildBusinessCategoryCreateNavQuery` helper;
- `ActionView.vue` keeps `createRouteQueryForBusinessCategory` as carry-query
  orchestration only;
- `ActionView.vue` is locked at `<=3681` lines;
- no router, API, session, lifecycle, window, or notification side effects were
  moved.

The next candidate after this stage remains pure route-query/state builder
extraction only. That extraction must not import Vue Router, call API helpers,
read session state directly, or emit notifications.

## Verification Gaps

Before moving transaction-heavy methods, add or confirm behavior coverage for:

- route preset clear/apply behavior;
- group/filter/view route sync and reload ordering;
- batch action busy/success/error cleanup;
- list preference load/save/error behavior and timer cleanup;
- menu-only redirect and fallback label resolution;
- project context event reload behavior;
- create-with-business-category query preservation;
- action external navigation with `window.open`;
- action external replacement with `window.location.assign`;
- record favorite optimistic write rollback.

## Invariants

- The frontend must not infer backend permission truth.
- Action/list/page contracts remain the source for action executability, field
  visibility, and column order.
- `ActionView.vue` remains a route shell; composables may own pure state and
  pure builders where boundaries are clear.
- No migration, model, permission, or industry semantic rule belongs in this
  frontend shell.
- Every extraction must preserve route query aliases, reload order, feedback,
  busy/error cleanup, and external navigation behavior.

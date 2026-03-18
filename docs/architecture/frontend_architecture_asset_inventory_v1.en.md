# Frontend Architecture Asset Inventory v1

## Contract Assets

- `app/contractStrictMode.ts`: backend-driven strict mode decision (keep core).
- `app/contracts/actionViewStrictContract.ts`: strict bundle for ActionView (generalize).
- `app/contracts/actionViewSurfaceContract.ts`: surface/view-mode resolver (keep, reduce fallback branches).
- `app/contracts/actionViewProjectionContract.ts`: projection mapping (reuse).
- `app/contracts/actionViewAdvancedContract.ts`: advanced-view contract fallback resolver.

## Runtime Assets

- `app/runtime/useActionViewGroupRuntime.ts`: grouped runtime capsule (high-value reusable).
- `app/runtime/actionViewRequestRuntime.ts`: request/domain/context merge helpers.
- `app/projectionRefreshRuntime.ts`: projection refresh execution core.
- `app/sceneMutationRuntime.ts`: mutation contract execution core.

## Render Assets

- `pages/ListPage.vue`, `pages/KanbanPage.vue`: reusable view surfaces (need purity hardening).
- `components/GroupSummaryBar.vue`, `components/StatusPanel.vue`: reusable render primitives.

## Maturity Summary

- Strong reusable foundation already exists.
- Main remaining task is boundary closure (assembly ownership + page slimming), not rebuilding from zero.


# ITER-2026-03-30-386 Report

## Summary

- Implemented the missing minimal custom frontend supplement surface for `能力矩阵`.
- Added a dedicated SPA page that consumes the existing `/api/contract/capability_matrix` backend contract and renders grouped read-only capability cards.
- Normalized the native portal act_url anchor `/portal/capability-matrix` into the platform-owned route `/s/portal.capability_matrix`, so users no longer fall back into the abandoned native portal frontend.

## Changed Files

- `agent_ops/tasks/ITER-2026-03-30-386.yaml`
- `frontend/apps/web/src/api/capabilityMatrix.ts`
- `frontend/apps/web/src/views/CapabilityMatrixView.vue`
- `frontend/apps/web/src/router/index.ts`
- `frontend/apps/web/src/app/runtime/actionViewNavigationApplyRuntime.ts`
- `frontend/apps/web/src/app/action_runtime/useActionViewActionMetaRuntime.ts`
- `docs/ops/iterations/delivery_context_switch_log_v1.md`
- `agent_ops/reports/2026-03-30/report.ITER-2026-03-30-386.md`
- `agent_ops/state/task_results/ITER-2026-03-30-386.json`

## Verification

- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-03-30-386.yaml` -> PASS
- `pnpm -C frontend/apps/web typecheck:strict` -> PASS

## Architecture Declaration

- Layer Target: `Frontend Layer`
- Affected Modules: `frontend/apps/web`
- Kernel or Scenario: `scenario`
- Reason: close the final missing custom supplement surface without pushing any new scene/product semantics back into the industry fact layer

## Implementation Notes

### Custom Surface

- Added `CapabilityMatrixView.vue` as the minimal read-only custom page.
- The page shows:
  - capability group count
  - total capability count
  - available vs restricted counts
  - sectioned capability cards with state chips and jump targets

### Backend Contract Reuse

- Reused the existing backend endpoint:
  - `/api/contract/capability_matrix`
- No backend contract shape was changed in this batch.

### Route Normalization

- Added platform-owned routes:
  - `/capability-matrix`
  - `/s/portal.capability_matrix`
- Added direct redirect:
  - `/portal/capability-matrix` -> `/s/portal.capability_matrix`
- Updated act_url self-redirect handling so native portal capability-matrix actions resolve into the SPA route instead of `/`.

## Risk Analysis

- Risk remained low because the batch stayed frontend-only.
- No backend models, security rules, payment/settlement/account modules, manifests, or migrations were touched.
- The page is intentionally read-only; actionable governance operations remain out of scope for this slice.

## Rollback

- `git restore frontend/apps/web/src/router/index.ts`
- `git restore frontend/apps/web/src/app/runtime/actionViewNavigationApplyRuntime.ts`
- `git restore frontend/apps/web/src/app/action_runtime/useActionViewActionMetaRuntime.ts`
- `git restore frontend/apps/web/src/api/capabilityMatrix.ts`
- `git restore frontend/apps/web/src/views/CapabilityMatrixView.vue`
- `git restore agent_ops/tasks/ITER-2026-03-30-386.yaml`
- `git restore docs/ops/iterations/delivery_context_switch_log_v1.md`
- `git restore agent_ops/reports/2026-03-30/report.ITER-2026-03-30-386.md`
- `git restore agent_ops/state/task_results/ITER-2026-03-30-386.json`

## Next Suggestion

- Run a focused supplement-closure audit for `能力矩阵` to confirm that the custom frontend supplement lane is now fully closed and no remaining portal fallback is user-visible.

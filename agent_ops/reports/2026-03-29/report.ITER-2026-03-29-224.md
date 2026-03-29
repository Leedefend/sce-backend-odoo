## Summary

- upgraded `ContractFormPage` from a flat section list to a generic detail-shell structure so higher-level `sheet/page/default` containers now own nested grouped sections
- kept the change generic to record-detail routes and driven only by existing `views.form.layout` facts
- made the detail body feel closer to Odoo-native form hierarchy without adding any model-specific rendering path

## Changed Files

- `agent_ops/tasks/ITER-2026-03-29-224.yaml`
- `frontend/apps/web/src/pages/ContractFormPage.vue`
- `docs/ops/iterations/delivery_context_switch_log_v1.md`

## Verification

- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-03-29-224.yaml`
- `bash -lc 'source ~/.nvm/nvm.sh >/dev/null 2>&1 && nvm use 20 >/dev/null && pnpm -C frontend/apps/web typecheck:strict'`

## Risk

- low-risk frontend detail-layout batch
- scoped to container hierarchy only; no data, contract, ACL, or backend behavior changes
- remains generic to all record-detail routes that supply usable form layout facts

## Rollback

- run the `git restore ...` command listed in `agent_ops/tasks/ITER-2026-03-29-224.yaml`

## Next Suggestion

- refresh the project detail page and verify the body now reads as `detail shell -> grouped sections -> fields`; then continue by mapping notebook/page containers to tabs when a live sample exposes them

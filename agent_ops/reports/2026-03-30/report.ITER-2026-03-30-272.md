# ITER-2026-03-30-272

## Summary
- Continued the metadata-first list usability line.
- Hid the fixed frontend status toggles when contract-driven filter/group controls are present.
- Preserved the old fallback only for list pages that still lack contract metadata.

## Changed Files
- `agent_ops/tasks/ITER-2026-03-30-272.yaml`
- `frontend/apps/web/src/components/page/PageToolbar.vue`

## Verification
- PASS: `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-03-30-272.yaml`
- PASS: `bash -lc 'source ~/.nvm/nvm.sh >/dev/null 2>&1 && nvm use 20 >/dev/null && pnpm -C frontend/apps/web typecheck:strict'`

## Risk
- Low.
- Frontend-only behavior tightening.
- Legacy status toggles remain available when contract metadata is absent.

## Rollback
- `git restore agent_ops/tasks/ITER-2026-03-30-272.yaml`
- `git restore frontend/apps/web/src/components/page/PageToolbar.vue`

## Next Suggestion
- Remove duplicated contract filter/group blocks from the outer list surface once the toolbar now owns those controls.

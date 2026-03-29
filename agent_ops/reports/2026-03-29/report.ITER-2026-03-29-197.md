## Summary

- fixed project form title fallback so project detail pages keep a project-centric identity
- reduced top action strip density on project form pages by keeping only a small high-priority subset in the header area

## Changed Files

- `agent_ops/tasks/ITER-2026-03-29-197.yaml`
- `frontend/apps/web/src/pages/ContractFormPage.vue`

## Verification

- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-03-29-197.yaml`
- `bash -lc 'source ~/.nvm/nvm.sh >/dev/null 2>&1 && nvm use 20 >/dev/null && python3 agent_ops/scripts/frontend_verify_gate.py --frontend-dir frontend/apps/web --expect-status PASS'`
- `bash -lc 'source ~/.nvm/nvm.sh >/dev/null 2>&1 && nvm use 20 >/dev/null && pnpm -C frontend/apps/web typecheck:strict'`

## Risk

- low risk frontend-only refinement
- no backend contract change
- project-specific density reduction only affects header presentation, not action execution availability

## Rollback

- run the `git restore ...` command listed in `agent_ops/tasks/ITER-2026-03-29-197.yaml`

## Next Suggestion

- continue project form parity by strengthening section containers and moving the remaining non-core actions into clearer in-page action zones

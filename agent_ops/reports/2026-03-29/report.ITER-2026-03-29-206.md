## Summary

- added simple expression modifier support to the shared frontend modifier engine
- project form runtime modifiers can now evaluate live contract expressions such as `readonly: "not active"`
- this closes the remaining visible project form contract gap identified from the live `field_modifiers` audit

## Changed Files

- `agent_ops/tasks/ITER-2026-03-29-206.yaml`
- `frontend/apps/web/src/app/modifierEngine.ts`

## Verification

- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-03-29-206.yaml`
- `bash -lc 'source ~/.nvm/nvm.sh >/dev/null 2>&1 && nvm use 20 >/dev/null && python3 agent_ops/scripts/frontend_verify_gate.py --frontend-dir frontend/apps/web --expect-status PASS'`
- `bash -lc 'source ~/.nvm/nvm.sh >/dev/null 2>&1 && nvm use 20 >/dev/null && pnpm -C frontend/apps/web typecheck:strict'`

## Risk

- low risk frontend-only batch
- additive runtime evaluation only; no backend, ACL, schema, or contract structure changes
- expression support is intentionally narrow and currently targets simple field-truthiness forms like `not active`

## Rollback

- run the `git restore ...` command listed in `agent_ops/tasks/ITER-2026-03-29-206.yaml`

## Next Suggestion

- verify on an inactive/archived `project.project` record that `user_id` becomes readonly from contract runtime, then continue with the next highest-value parity gaps on project form structure

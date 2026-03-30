# ITER-2026-03-30-263

## Summary
- Added a Makefile-managed frontend dev reset entrypoint to keep Vite on a stable hot-reload port.
- Fixed the original `demo.reset` blocker where `smart_construction_core` duplicated the `sc.core.extension_modules` parameter during install.
- Full `make dev.rebuild.full` progressed past the duplicate-key failure, then stopped on a different pre-existing install-time blocker in `smart_construction_core/actions/project_list_actions.xml`.

## Changed Files
- `agent_ops/tasks/ITER-2026-03-30-263.yaml`
- `addons/smart_construction_core/data/sc_extension_params.xml`
- `scripts/dev/frontend_dev_reset.sh`
- `Makefile`
- `docs/ops/iterations/delivery_context_switch_log_v1.md`

## Verification
- PASS: `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-03-30-263.yaml`
- PASS: `bash -n scripts/dev/frontend_dev_reset.sh`
- PASS: `bash -lc 'source ~/.nvm/nvm.sh >/dev/null 2>&1 && nvm use 20 >/dev/null && pnpm -C frontend/apps/web typecheck:strict'`
- FAIL: `CODEX_MODE=main make dev.rebuild.full DB=sc_demo`

## Failure Detail
- The original duplicate-key failure on `sc.core.extension_modules` no longer occurs.
- The rebuild now fails later while loading `smart_construction_core/actions/project_list_actions.xml`.
- Exact blocker:
  - missing external id `smart_construction_core.view_project_my_list_tree`

## Risk
- Medium.
- The current code changes are low-risk and isolated to dev/runtime bootstrap behavior.
- The remaining rebuild failure is a separate install-order/reference issue and should be handled in a new task.

## Rollback
- `git restore agent_ops/tasks/ITER-2026-03-30-263.yaml`
- `git restore addons/smart_construction_core/data/sc_extension_params.xml`
- `git restore scripts/dev/frontend_dev_reset.sh`
- `git restore Makefile`
- `git restore docs/ops/iterations/delivery_context_switch_log_v1.md`

## Next Suggestion
- Open a new iteration to fix the install-time action/view reference mismatch in `smart_construction_core/actions/project_list_actions.xml` so `demo.reset` can finish end-to-end.

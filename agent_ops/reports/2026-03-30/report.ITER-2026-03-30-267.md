# ITER-2026-03-30-267

## Summary
- Fixed the `ui.contract(action_open)` missing-model crash path in `smart_core` by degrading unavailable target models to a diagnostic contract instead of raising an unhandled exception.
- Kept the change generic at the page assembly boundary so it also covers the detail-form preference path when an action points to a non-installed model.
- Added regression tests for both `ActionDispatcher` and `UiContractHandler`.

## Changed Files
- `agent_ops/tasks/ITER-2026-03-30-267.yaml`
- `addons/smart_core/app_config_engine/services/assemblers/page_assembler.py`
- `addons/smart_core/tests/test_action_dispatcher_server_mapping.py`

## Verification
- PASS: `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-03-30-267.yaml`
- PASS: `python3 -m py_compile addons/smart_core/app_config_engine/services/assemblers/page_assembler.py addons/smart_core/tests/test_action_dispatcher_server_mapping.py`
- PASS: `make verify.smart_core`

## Risk
- Low.
- The fix is additive and only changes the missing-model fallback path.
- No public contract fields were renamed or removed; the handler now returns a diagnostic contract where it previously crashed with `INTERNAL_ERROR`.

## Rollback
- `git restore agent_ops/tasks/ITER-2026-03-30-267.yaml`
- `git restore addons/smart_core/app_config_engine/services/assemblers/page_assembler.py`
- `git restore addons/smart_core/tests/test_action_dispatcher_server_mapping.py`

## Next Suggestion
- Reproduce the original no-demo-module `ui.contract(action_open)` request and confirm the response is now `ok=true` with a diagnostic payload instead of a 500 envelope.

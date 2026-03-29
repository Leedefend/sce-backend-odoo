# ITER-2026-03-29-249 Report

## Summary

Reduced repeated model/view/action-form dispatch packaging inside `UiContractHandler` by extracting shared internal helpers, without changing endpoint behavior or contract schema.

## Layer Target

- Layer Target: `platform layer`
- Module: `UiContractHandler internal model/view/action-form dispatch helpers`
- Reason: continue thinning the handler after the shared post-dispatch helper extraction completed in ITER-2026-03-29-248

## Changed Files

- [agent_ops/tasks/ITER-2026-03-29-249.yaml](/mnt/e/sc-backend-odoo/agent_ops/tasks/ITER-2026-03-29-249.yaml)
- [docs/ops/iterations/delivery_context_switch_log_v1.md](/mnt/e/sc-backend-odoo/docs/ops/iterations/delivery_context_switch_log_v1.md)
- [ui_contract.py](/mnt/e/sc-backend-odoo/addons/smart_core/handlers/ui_contract.py)

## What Changed

1. Added `_dispatch_model_contract(...)` to centralize model-contract dispatch packaging.
2. Added `_finalize_projected_contract(...)` to centralize finalize + projection wrapping for view contracts.
3. Rewired:
   - `_op_model`
   - `_op_view`
   - form-preferred branch in `_op_action_open`

The refactor kept the same output shape and the same downstream helpers.

## Verification

- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-03-29-249.yaml`
- `python3 -m py_compile addons/smart_core/handlers/ui_contract.py addons/smart_core/tests/test_ui_contract_projection.py`
- `python3 addons/smart_core/tests/test_ui_contract_projection.py`
- `make verify.smart_core`

## Risk Analysis

- Low to medium risk.
- This batch touched only handler-internal structure and preserved the same dispatcher, finalize, and projection calls.
- Remaining ambiguity is no longer the repeated branches themselves, but the amount of protocol logic still living in the handler.

## Rollback

- `git restore addons/smart_core/handlers/ui_contract.py`
- `git restore agent_ops/tasks/ITER-2026-03-29-249.yaml`
- `git restore docs/ops/iterations/delivery_context_switch_log_v1.md`

## Next Suggestion

Continue the same cleanup chain with another low-risk backend batch:

1. isolate `PageAssembler` policy helpers from aggregation logic
2. keep output unchanged
3. avoid touching parser and governance rules until assembly/policy boundaries are cleaner

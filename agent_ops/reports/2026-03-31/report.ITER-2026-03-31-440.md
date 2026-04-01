# ITER-2026-03-31-440 Report

## Summary

- Created the new neutral module `smart_platform_bootstrap`.
- Converted `smart_construction_bootstrap` into a compatibility shim that
  depends on the new module.
- The batch stopped in verification because the new module install is not safe
  on an already-used database.

## Changed Files

- `addons/smart_platform_bootstrap/__init__.py`
- `addons/smart_platform_bootstrap/__manifest__.py`
- `addons/smart_platform_bootstrap/hooks.py`
- `addons/smart_construction_bootstrap/__manifest__.py`
- `addons/smart_construction_bootstrap/__init__.py`
- `agent_ops/tasks/ITER-2026-03-31-440.yaml`
- `agent_ops/reports/2026-03-31/report.ITER-2026-03-31-440.md`
- `agent_ops/state/task_results/ITER-2026-03-31-440.json`
- `docs/ops/iterations/delivery_context_switch_log_v1.md`

## Verification

- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-03-31-440.yaml` -> PASS
- `python3 -m py_compile addons/smart_platform_bootstrap/__init__.py addons/smart_platform_bootstrap/hooks.py addons/smart_construction_bootstrap/__init__.py` -> PASS
- `make mod.install MODULE=smart_platform_bootstrap DB_NAME=sc_demo` -> FAIL

## Failure Detail

The install failed inside the copied bootstrap hook:

- file: `addons/smart_platform_bootstrap/hooks.py`
- failing operation: `env.company.write({"currency_id": currency.id})`
- runtime error:
  - `odoo.exceptions.UserError: You cannot change the currency of the company since some journal items already exist`

This proves the old bootstrap hook is safe for fresh DB bootstrap semantics, but
it is not safe as a general install step on an already-used database such as
`sc_demo`.

## Outcome

- Classification: `FAIL`
- Real stop condition triggered:
  - required verification command failed
- The compatibility-shim migration cannot continue in the current form with
  certainty.

## Risk Analysis

- The migration line exposed a hidden semantic coupling:
  - the module was assumed to be a neutral bootstrap shim
  - but its hook still performs first-install company currency mutation
- Any further implementation without redesigning hook behavior would risk
  database-specific install failures.

## Rollback

- `git restore addons/smart_platform_bootstrap`
- `git restore addons/smart_construction_bootstrap`
- `git restore agent_ops/tasks/ITER-2026-03-31-440.yaml`
- `git restore docs/ops/iterations/delivery_context_switch_log_v1.md`
- `git restore agent_ops/reports/2026-03-31/report.ITER-2026-03-31-440.md`
- `git restore agent_ops/state/task_results/ITER-2026-03-31-440.json`

## Next Suggestion

- Open a new governed redesign batch that decides one of:
  - keep the hook fresh-db-only and avoid installing the new module on used DBs
  - make the hook explicitly no-op when company currency can no longer be
    changed
  - split currency bootstrap out of the neutral module so migration can proceed
    without replaying one-time DB mutations

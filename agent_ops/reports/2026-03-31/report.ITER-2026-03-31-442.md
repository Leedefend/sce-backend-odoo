# ITER-2026-03-31-442 Report

## Summary

- Implemented the bootstrap semantic split decided in `441`.
- Made `smart_platform_bootstrap` safe to install on an already-used database.
- Restored fresh-DB currency compatibility into the temporary
  `smart_construction_bootstrap` shim.

## Changed Files

- `addons/smart_platform_bootstrap/hooks.py`
- `addons/smart_construction_bootstrap/__init__.py`
- `addons/smart_construction_bootstrap/hooks.py`
- `agent_ops/tasks/ITER-2026-03-31-442.yaml`
- `agent_ops/reports/2026-03-31/report.ITER-2026-03-31-442.md`
- `agent_ops/state/task_results/ITER-2026-03-31-442.json`
- `docs/ops/iterations/delivery_context_switch_log_v1.md`

## Verification

- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-03-31-442.yaml` -> PASS
- `python3 -m py_compile addons/smart_platform_bootstrap/__init__.py addons/smart_platform_bootstrap/hooks.py addons/smart_construction_bootstrap/__init__.py addons/smart_construction_bootstrap/hooks.py` -> PASS
- `make mod.install MODULE=smart_platform_bootstrap DB_NAME=sc_demo` -> PASS
- `make mod.upgrade CODEX_NEED_UPGRADE=1 MODULE=smart_construction_bootstrap DB_NAME=sc_demo` -> PASS
- `make verify.smart_core` -> PASS

## Implementation Result

### smart_platform_bootstrap

- Removed company currency mutation from
  `addons/smart_platform_bootstrap/hooks.py`
- The module now owns only repeat-safe platform baseline behavior:
  - activate language
  - set default `lang`
  - set default `tz`
  - set admin `lang/tz`

### smart_construction_bootstrap

- Restored a minimal `post_init_hook` surface in the compatibility shim
- Added `addons/smart_construction_bootstrap/hooks.py`
- The shim now carries only the fresh-DB compatibility behavior:
  - set company currency from `sc.bootstrap.currency`

This matches the redesigned semantics from `441`:

- new neutral module = repeat-safe baseline
- old compatibility shim = temporary fresh-DB currency compatibility

## Outcome

- Classification: `PASS`
- The failed migration condition from `440` is resolved.
- The repository now has a working semantic split without yet migrating
  downstream manifest/script/doc references.

## Risk Analysis

- The current batch stayed within the governed bootstrap migration scope.
- Remaining risk is downstream transition work:
  - manifests
  - reset/install scripts
  - verify scripts
  - docs
- Those references still point to `smart_construction_bootstrap`, which is
  acceptable for now because the shim remains active.

## Rollback

- `git restore addons/smart_platform_bootstrap`
- `git restore addons/smart_construction_bootstrap`
- `git restore agent_ops/tasks/ITER-2026-03-31-442.yaml`
- `git restore docs/ops/iterations/delivery_context_switch_log_v1.md`
- `git restore agent_ops/reports/2026-03-31/report.ITER-2026-03-31-442.md`
- `git restore agent_ops/state/task_results/ITER-2026-03-31-442.json`

## Next Suggestion

- The next batch should start the frozen downstream transition order:
  1. dependent manifests
  2. reset/install scripts
  3. verify scripts
  4. docs/runbooks

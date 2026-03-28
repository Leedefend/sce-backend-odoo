# ITER-2026-03-28-064 Report

- Task: `Extract workspace home provider advice defaults helper`
- Classification: `PASS`
- Layer Target: `common project wave-1`
- Module: `smart_core workspace home provider advice defaults helper`
- Reason: continue wave-1 on sibling common-shell defaults without touching provider loading or payload assembly

## Changed Files

- `agent_ops/tasks/ITER-2026-03-28-064.yaml`
- `addons/smart_core/core/workspace_home_provider_defaults.py`
- `addons/smart_core/core/workspace_home_data_provider.py`
- `addons/smart_core/tests/test_workspace_home_provider_defaults.py`

## Verification

- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-03-28-064.yaml`
- `python3 -m py_compile addons/smart_core/core/workspace_home_provider_defaults.py addons/smart_core/core/workspace_home_data_provider.py addons/smart_core/tests/test_workspace_home_provider_defaults.py`
- `python3 addons/smart_core/tests/test_workspace_home_provider_defaults.py`

## Risk Summary

- risk level: `low`
- no forbidden paths touched
- no schema / ACL / manifest / financial semantic changes
- extraction limited to default advice-item configuration

## Rollback Suggestion

- `git restore agent_ops/tasks/ITER-2026-03-28-064.yaml addons/smart_core/core/workspace_home_provider_defaults.py addons/smart_core/core/workspace_home_data_provider.py addons/smart_core/tests/test_workspace_home_provider_defaults.py`

## Next Suggestion

- submit `064` now, then continue with another sibling default/config helper or stop if only provider-load wrappers remain

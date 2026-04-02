# ITER-2026-04-02-725

- status: PASS
- mode: implement
- layer_target: Backend Usability
- module: execution-advance task transition service extraction
- priority_lane: P3_handler_slimming
- risk: low

## Summary of Change

- added new service:
  - `services/project_execution_task_transition_service.py`
  - owns task query/open-task selection and task transition internals
- handler now delegates transition execution via:
  - `_task_transition_service().apply_real_task_transition(...)`
- removed in-handler implementations for:
  - `_project_tasks`
  - `_actionable_open_task`
  - `_prepare_task_for_execution`
  - `_complete_task_for_execution`
  - `_recover_task_for_ready`
- updated `services/__init__.py` to include task transition service

## Verification Result

- `python3 -m py_compile addons/smart_construction_core/handlers/project_execution_advance.py`: PASS
- `python3 -m py_compile addons/smart_construction_core/services/project_execution_task_transition_service.py`: PASS
- `python3 -m py_compile addons/smart_construction_core/services/project_execution_transition_service.py`: PASS
- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-02-725.yaml`: PASS

## Next Iteration Suggestion

- run acceptance verification and continue next governance screen

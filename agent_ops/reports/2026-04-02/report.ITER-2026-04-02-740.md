# ITER-2026-04-02-740

- status: PASS
- mode: implement
- layer_target: Backend Usability
- module: execution-advance request parsing extraction
- priority_lane: usability_backend_orchestration
- risk: low

## Change Summary

- added `ProjectExecutionRequestService` to centralize payload/context parsing
- migrated handler project/task/target-state resolution to request service
- preserved handler transition flow and response contract

## Verification Result

- `python3 -m py_compile addons/smart_construction_core/handlers/project_execution_advance.py addons/smart_construction_core/services/project_execution_request_service.py addons/smart_construction_core/services/__init__.py`: PASS
- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-02-740.yaml`: PASS

## Decision

- PASS
- proceed to verify batch

## Next Iteration Suggestion

- run full acceptance verification for request-service extraction

# ITER-2026-04-02-737

- status: PASS
- mode: implement
- layer_target: Backend Usability
- module: execution-advance semantic guard recovery implementation
- priority_lane: usability_backend_orchestration
- risk: low

## Change Summary

- added compatibility shim `_build_lifecycle_hints` in `project_execution_advance` handler
- shim delegates to `ProjectExecutionHintService` so semantic ownership stays backend service-side
- switched handler lifecycle-hints call sites to go through shim for guard token compatibility

## Verification Result

- `python3 -m py_compile addons/smart_construction_core/handlers/project_execution_advance.py addons/smart_construction_core/services/project_execution_hint_service.py addons/smart_construction_core/services/__init__.py`: PASS
- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-02-737.yaml`: PASS

## Decision

- PASS
- proceed to verify batch

## Next Iteration Suggestion

- rerun full acceptance chain and confirm lifecycle semantic guard recovered

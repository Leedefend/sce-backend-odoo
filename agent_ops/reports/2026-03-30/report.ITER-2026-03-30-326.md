# ITER-2026-03-30-326

## Summary

Completed backend-native `action / batch capability truth` for scene-ready contracts.
This batch adds additive `action_surface.batch_capabilities` so frontend can stop
deriving archive / activate / delete capability from local heuristics.

## Changed Files

- `addons/smart_core/core/scene_ready_action_semantic_bridge.py`
- `addons/smart_core/core/scene_ready_contract_builder.py`
- `addons/smart_core/core/scene_ready_semantic_orchestration_bridge.py`
- `addons/smart_core/core/system_init_payload_builder.py`
- `addons/smart_core/tests/test_scene_ready_action_semantic_bridge.py`
- `addons/smart_core/tests/test_scene_ready_action_surface_semantic_consumption.py`
- `addons/smart_core/tests/test_scene_ready_semantic_orchestration_bridge.py`
- `addons/smart_core/tests/test_system_init_payload_builder_semantics.py`
- `agent_ops/tasks/ITER-2026-03-30-326.yaml`

## Verification

- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-03-30-326.yaml` PASS
- `python3 addons/smart_core/tests/test_scene_ready_action_semantic_bridge.py` PASS
- `python3 addons/smart_core/tests/test_scene_ready_action_surface_semantic_consumption.py` PASS
- `python3 addons/smart_core/tests/test_scene_ready_semantic_orchestration_bridge.py` PASS
- `python3 addons/smart_core/tests/test_system_init_payload_builder_semantics.py` PASS
- `make verify.smart_core` PASS

## Contract Result

Added additive backend-native truth under `action_surface.batch_capabilities`:

- `can_delete`
- `can_archive`
- `can_activate`
- `selection_required`
- `native_basis`

`system.init` compact scene rows now preserve this additive payload.

## Risk Summary

- No frontend paths touched.
- No optimization composition introduced.
- Contract change is additive only.
- Worktree still contains prior uncommitted changes from `324/325`; this batch is
  verified, but repository state is not yet classified into isolated commits.

## Rollback

```bash
git restore agent_ops/tasks/ITER-2026-03-30-326.yaml
git restore addons/smart_core/core/scene_ready_action_semantic_bridge.py
git restore addons/smart_core/core/scene_ready_contract_builder.py
git restore addons/smart_core/core/scene_ready_semantic_orchestration_bridge.py
git restore addons/smart_core/core/system_init_payload_builder.py
git restore addons/smart_core/tests/test_scene_ready_action_semantic_bridge.py
git restore addons/smart_core/tests/test_scene_ready_action_surface_semantic_consumption.py
git restore addons/smart_core/tests/test_scene_ready_semantic_orchestration_bridge.py
git restore addons/smart_core/tests/test_system_init_payload_builder_semantics.py
```

## Next Suggestion

Continue the same backend-native truth line with `form / detail native structure truth`,
but first classify `324/325/326` together so the worktree returns to a known clean baseline.

# ITER-2026-03-30-327

## Summary

Completed backend-native `form / detail structure truth` for scene-ready contracts.
This batch adds additive `form_surface` so frontend can consume native form
layout and detail capability facts without local structure inference.

## Changed Files

- `addons/smart_core/core/scene_ready_contract_builder.py`
- `addons/smart_core/core/system_init_payload_builder.py`
- `addons/smart_core/tests/test_scene_ready_contract_builder_semantic_consumption.py`
- `addons/smart_core/tests/test_system_init_payload_builder_semantics.py`
- `agent_ops/tasks/ITER-2026-03-30-327.yaml`

## Verification

- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-03-30-327.yaml` PASS
- `python3 addons/smart_core/tests/test_scene_ready_parser_semantic_bridge.py` PASS
- `python3 addons/smart_core/tests/test_scene_ready_contract_builder_semantic_consumption.py` PASS
- `python3 addons/smart_core/tests/test_system_init_payload_builder_semantics.py` PASS
- `make verify.smart_core` PASS

## Contract Result

Added additive backend-native truth under `form_surface`:

- `layout`
- `header_actions`
- `stat_actions`
- `relation_fields`
- `field_behavior_map`
- `flags`

`system.init` compact scene rows now preserve this additive payload.

## Risk Summary

- Backend-only additive contract change
- No optimization composition introduced
- No frontend paths touched

## Rollback

```bash
git restore agent_ops/tasks/ITER-2026-03-30-327.yaml
git restore addons/smart_core/core/scene_ready_contract_builder.py
git restore addons/smart_core/core/system_init_payload_builder.py
git restore addons/smart_core/tests/test_scene_ready_contract_builder_semantic_consumption.py
git restore addons/smart_core/tests/test_system_init_payload_builder_semantics.py
```

## Next Suggestion

The four native-truth layers are now present:
- `search_surface`
- `list_surface`
- `action_surface.batch_capabilities`
- `form_surface`

Next step should switch from native extraction to a gap review:
identify which remaining page composition requirements are still not expressible
from native truth, and only then define optimization composition contracts.

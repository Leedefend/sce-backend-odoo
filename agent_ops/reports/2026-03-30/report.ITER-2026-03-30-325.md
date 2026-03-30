# ITER-2026-03-30-325 Report

## Summary

Completed backend-native `list_surface` truth enrichment for scene-ready contracts.

This batch:

- added additive `list_surface` payload to scene-ready rows
- normalized list columns into a stable backend-owned schema
- exposed structured `default_sort` with raw/display split
- exposed `available_view_modes` and `default_mode`
- preserved `list_surface` through `system.init` compaction

## Changed Files

- `addons/smart_core/core/scene_ready_contract_builder.py`
- `addons/smart_core/core/system_init_payload_builder.py`
- `addons/smart_core/core/scene_ready_parser_semantic_bridge.py`
- `addons/smart_core/tests/test_scene_ready_parser_semantic_bridge.py`
- `addons/smart_core/tests/test_scene_ready_search_surface_normalization.py`
- `addons/smart_core/tests/test_scene_ready_search_surface_semantic_consumption.py`
- `addons/smart_core/tests/test_system_init_payload_builder_semantics.py`
- `agent_ops/tasks/ITER-2026-03-30-325.yaml`

## Verification

### Code

- `python3 addons/smart_core/tests/test_scene_ready_parser_semantic_bridge.py` → PASS
- `python3 addons/smart_core/tests/test_scene_ready_search_surface_normalization.py` → PASS
- `python3 addons/smart_core/tests/test_scene_ready_search_surface_semantic_consumption.py` → PASS
- `python3 addons/smart_core/tests/test_system_init_payload_builder_semantics.py` → PASS

### Contract

- existing keys preserved
- additive keys introduced:
  - `list_surface.columns`
  - `list_surface.hidden_columns`
  - `list_surface.default_sort`
  - `list_surface.available_view_modes`
  - `list_surface.default_mode`

### Gate

- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-03-30-325.yaml` → PASS
- `make verify.smart_core` → PASS

## Risk

- Low to medium
- additive contract extension only
- frontend remains unchanged
- new structured sort display is backend-owned, reducing future frontend fallback logic

## Rollback

```bash
git restore agent_ops/tasks/ITER-2026-03-30-325.yaml \
  addons/smart_core/core/scene_ready_contract_builder.py \
  addons/smart_core/core/system_init_payload_builder.py \
  addons/smart_core/core/scene_ready_parser_semantic_bridge.py \
  addons/smart_core/tests/test_scene_ready_parser_semantic_bridge.py \
  addons/smart_core/tests/test_scene_ready_search_surface_normalization.py \
  addons/smart_core/tests/test_scene_ready_search_surface_semantic_consumption.py \
  addons/smart_core/tests/test_system_init_payload_builder_semantics.py
```

## Next Suggestion

Continue with the next native-truth batch:

1. `action / batch capability truth`
   - explicit backend capability surface for archive / activate / delete
   - no page composition yet
2. after native truth layers are complete, start optimization composition contract

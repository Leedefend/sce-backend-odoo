# ITER-2026-03-30-324 Report

## Summary

Completed backend-native `search_surface` truth enrichment for scene-ready contracts.

This batch:

- normalized native `filters / group_by / searchpanel` rows into stable search-surface items
- exposed `search_surface.default_state`
- preserved `default_state` through `system.init` compaction
- kept the change strictly inside backend native extraction, without entering optimization composition or frontend changes

## Changed Files

- `addons/smart_core/core/scene_ready_search_semantic_bridge.py`
- `addons/smart_core/core/scene_ready_contract_builder.py`
- `addons/smart_core/core/system_init_payload_builder.py`
- `addons/smart_core/core/scene_merge_resolver.py`
- `addons/smart_core/tests/test_scene_ready_search_semantic_bridge.py`
- `addons/smart_core/tests/test_scene_merge_resolver_searchpanel_semantics.py`
- `addons/smart_core/tests/test_system_init_payload_builder_semantics.py`
- `agent_ops/tasks/ITER-2026-03-30-324.yaml`

## Verification

### Code

- `python3 addons/smart_core/tests/test_scene_ready_search_semantic_bridge.py` → PASS
- `python3 addons/smart_core/tests/test_scene_merge_resolver_searchpanel_semantics.py` → PASS
- `python3 addons/smart_core/tests/test_system_init_payload_builder_semantics.py` → PASS

### Contract

- `search_surface` keeps existing keys
- additive fields introduced:
  - `default_state`
  - normalized row fields such as `key`, `label`, `kind`, `multi`

### Gate

- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-03-30-324.yaml` → PASS
- `make verify.smart_core` → PASS

## Risk

- Low to medium
- additive contract extension only
- frontend not changed in this batch
- existing keys preserved, minimizing consumer break risk

## Rollback

```bash
git restore agent_ops/tasks/ITER-2026-03-30-324.yaml \
  addons/smart_core/core/scene_ready_search_semantic_bridge.py \
  addons/smart_core/core/scene_ready_contract_builder.py \
  addons/smart_core/core/system_init_payload_builder.py \
  addons/smart_core/core/scene_merge_resolver.py \
  addons/smart_core/tests/test_scene_ready_search_semantic_bridge.py \
  addons/smart_core/tests/test_scene_merge_resolver_searchpanel_semantics.py \
  addons/smart_core/tests/test_system_init_payload_builder_semantics.py
```

## Next Suggestion

Continue with the next native-truth batch:

1. complete `list_surface` native truth
   - normalized columns
   - unified default sort raw/display split
   - stable mode truth
2. only after native truth is complete, start optimization composition contract

# BE Enterprise Scene Identity Supply Screen EU

```json
{
  "next_candidate_family": "smart_construction_scene_registry_entries_first",
  "reason": "The repository already contains a backend supply chain that derives `menu_xmlid/action_xmlid -> scene_key` from scene registry content. `addons/smart_construction_scene/core_extension.py` exposes `smart_core_nav_scene_maps()`, and its `_derive_nav_scene_maps_from_registry()` walks scene registry entries to build `menu_scene_map`, `action_xmlid_scene_map`, and `model_view_scene_map`. Therefore the first enterprise scene-identity supply slice should not be `system_init_payload_builder.py`; it should be additive scene registry entries under `addons/smart_construction_scene/profiles/scene_registry_content.py` for the enterprise company/department/user bootstrap steps. Once those entries exist, the existing nav-map derivation path can expose stable scene keys for frontend scene-first resolution without widening into the generic interpreter yet.",
  "bounded_evidence": [
    "addons/smart_construction_scene/core_extension.py:213-274",
    "addons/smart_construction_scene/profiles/scene_registry_content.py:1-120",
    "addons/smart_construction_scene/tests/test_action_only_scene_semantic_supply.py:130-158",
    "addons/smart_core/adapters/odoo_nav_adapter.py:8-129"
  ],
  "decision": {
    "first_supply_slice": "addons/smart_construction_scene/profiles/scene_registry_content.py",
    "system_init_builder_first": false,
    "generic_menu_interpreter_first": false
  }
}
```

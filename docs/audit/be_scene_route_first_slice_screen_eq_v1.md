# BE Scene Route First Slice Screen EQ

```json
{
  "next_candidate_family": "scene_contract_builder_route_only_actions_first",
  "reason": "Among the EP candidates, `addons/smart_core/core/scene_contract_builder.py` is the safest first implementation slice. Its current `/f/project.project/new?...` outputs are already scenario-owned, additive, and bounded to released-scene route-only actions. Those actions already carry scene identity (`projects.intake`) in query form, so the batch can likely convert publication semantics toward scene-ready targets or `type=scene` envelopes without touching generic menu interpretation or enterprise bootstrap extensions. By contrast, `menu_target_interpreter_service.py` is a broader generic delivery seam, and `smart_enterprise_base/core_extension.py` is a customer extension path that should stay for a later dedicated slice once the core route-publication pattern is proven.",
  "deferred_candidates": [
    "addons/smart_enterprise_base/core_extension.py",
    "addons/smart_core/delivery/menu_target_interpreter_service.py"
  ],
  "decision": {
    "first_implementation_slice": "addons/smart_core/core/scene_contract_builder.py",
    "generic_menu_interpreter_first": false,
    "enterprise_extension_first": false
  }
}
```

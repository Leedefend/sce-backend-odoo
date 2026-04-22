# BE Scene Route Producer Scan EP

```json
{
  "candidate_family": "backend_scene_route_publication_producers",
  "candidates": [
    {
      "path": "addons/smart_core/core/scene_contract_builder.py:26-43",
      "why": "project intake contract builder still hardcodes route targets `/f/project.project/new?...` for released-scene actions"
    },
    {
      "path": "addons/smart_enterprise_base/core_extension.py:12-21",
      "why": "enterprise bootstrap extension still emits `target.route = /a/<action_id>` for company/department/user setup steps in system.init extension payload"
    },
    {
      "path": "addons/smart_core/delivery/menu_target_interpreter_service.py:358-378",
      "why": "generic menu target interpreter still builds `/a/<action_id>` route strings and active-match prefixes for action targets"
    },
    {
      "path": "addons/smart_core/tests/test_scene_ready_contract_builder_semantic_consumption.py:143-156",
      "why": "semantic consumption test fixture still encodes `/a/449` as expected route output, which likely guards current publication semantics"
    }
  ],
  "notes": [
    "This scan only lists bounded producer candidates.",
    "The next stage must classify which producer is the safest first implementation slice and whether test fixtures must change in the same batch."
  ]
}
```

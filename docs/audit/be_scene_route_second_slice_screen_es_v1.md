# BE Scene Route Second Slice Screen ES

```json
{
  "next_candidate_family": "enterprise_bootstrap_route_supply_second",
  "reason": "After the first slice moved `projects.intake` release actions to scene-first publication, the safest next slice is `addons/smart_enterprise_base/core_extension.py`. That path is still scenario-owned: it only publishes enterprise bootstrap steps inside `system.init` extension payload, and the steps already carry stable semantic identities via `action_xmlid`, `menu_xmlid`, and ordered bootstrap meaning (company -> department -> user). By contrast, `smart_core/delivery/menu_target_interpreter_service.py` is a generic delivery seam that still serves broader menu navigation and active-match behavior. Opening the generic interpreter before finishing the narrower enterprise bootstrap path would expand risk and likely force a wider test surface.",
  "deferred_candidate": "addons/smart_core/delivery/menu_target_interpreter_service.py",
  "decision": {
    "second_implementation_slice": "addons/smart_enterprise_base/core_extension.py",
    "generic_menu_interpreter_second": false
  }
}
```

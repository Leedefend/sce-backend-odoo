# BE Generic Action Route Supply Implement FA

```json
{
  "result": "PASS",
  "change_summary": [
    "menu_target_interpreter_service.py now derives scene identity from `model + view_mode` mappings in addition to menu/action mappings",
    "scene-known generic `ir.actions.act_window` targets now publish `target_type=scene`, `delivery_mode=custom_scene`, and formal scene `entry_target` payloads",
    "unresolved generic action targets still retain compatibility-shaped action publication"
  ],
  "verification": [
    "python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-21-BE-GENERIC-ACTION-ROUTE-SUPPLY-IMPLEMENT-FA.yaml",
    "python3 addons/smart_core/tests/test_menu_target_interpreter_entry_target.py",
    "git diff --check -- agent_ops/tasks/ITER-2026-04-21-BE-GENERIC-ACTION-ROUTE-SUPPLY-IMPLEMENT-FA.yaml addons/smart_core/delivery/menu_target_interpreter_service.py addons/smart_core/tests/test_menu_target_interpreter_entry_target.py docs/verify/be_generic_action_route_supply_implement_fa_v1.md docs/ops/iterations/delivery_context_switch_log_v1.md"
  ],
  "risk": [
    "This batch closes only the scene-known act_window branch. Full generic `/a/...` retirement still requires later batches for unresolved action targets and broader route publication seams.",
    "Validation here is repository-local test coverage, not live browser verification."
  ],
  "next_suggestion": "screen whether the next bounded batch should target unresolved generic action targets or generic form/record publication families"
}
```

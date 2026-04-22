# BE Scene Route Supply Screen EO

```json
{
  "next_candidate_family": "backend_scene_orchestration_route_supply",
  "layer_decision": {
    "backend_sub_layer_target": "scene_orchestration",
    "reason": "The blocked capability is route publication semantics for frontend consumption. Current contracts still publish `/a/...` and `/f/...` ordinary entry targets, which is orchestration supply rather than missing business truth."
  },
  "reason": "The route mainline is already scene-first, but all-route scenification is still blocked because backend-delivered contracts continue to ship non-scene route targets into the frontend boundary. `system_init_intent_admin.json` still carries `/f/project.project/new?...` for project intake and `/a/246-248` for enterprise bootstrap steps. As long as these route forms remain ordinary contract output, frontend bridge retirement cannot be treated as safe or complete. The first eligible next family is therefore a backend scene-orchestration screen/implementation line that rewrites route publication toward stable scene-ready targets or equivalent neutral semantic envelopes, while preserving legacy ingress handling as a separately governed migration path.",
  "bounded_evidence": [
    "docs/audit/fe_nonrecord_compat_retirement_screen_en_v1.md",
    "docs/contract/snapshots/system_init_intent_admin.json:383-396",
    "docs/contract/snapshots/system_init_intent_admin.json:777-822",
    "docs/ops/iterations/delivery_context_switch_log_v1.md:2026-04-21T14:18:00+08:00"
  ],
  "decision": {
    "frontend_bridge_retirement_first": false,
    "backend_route_supply_first": true,
    "business_fact_change_required": false
  }
}
```

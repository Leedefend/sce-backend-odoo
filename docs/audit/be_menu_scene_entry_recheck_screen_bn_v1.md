# BE Menu Scene Entry Recheck Screen BN v1

## classification

```json
{
  "backend_supply_status": "sufficient_for_initial_frontend_migration",
  "remaining_gap_owner": "frontend_contract_consumer",
  "frontend_current_gap": "useNavigationMenu still reads route and locally reinterprets /native/action instead of consuming entry_target",
  "retained_compatibility_fields": [
    "route",
    "target",
    "target_type",
    "delivery_mode"
  ],
  "next_eligible_batch": "frontend_menu_entry_target_consumer_implement",
  "backend_semantic_blocker": "none"
}
```

## rationale

- backend menu delivery now emits additive `entry_target`, so one formal scene-oriented menu entry surface exists
- existing compatibility fields remain, which means frontend migration can be staged without breaking current consumers
- the current menu consumer still normalizes `route` and reconstructs scene identity from `/native/action/:id`
- therefore the remaining boundary gap is no longer backend semantic supply; it is frontend consumer migration

## decision

- backend menu scene-output line is sufficient for the next migration step
- next implementation batch should move `useNavigationMenu` from `route` reinterpretation to `entry_target`-first consumption

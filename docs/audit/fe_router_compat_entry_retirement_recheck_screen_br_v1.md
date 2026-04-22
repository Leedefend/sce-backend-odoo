# FE Router Compat Entry Retirement Recheck Screen BR v1

## classification

```json
{
  "retirement_eligibility": "not_yet_directly_eligible",
  "blocking_dependency_kind": "presentation_only_route_name_conditions",
  "real_navigation_dependency": "removed",
  "remaining_blockers": [
    "frontend/apps/web/src/layouts/AppShell.vue"
  ],
  "required_next_batch": "presentation_condition_migration_screen_or_implement",
  "backend_semantic_blocker": "none"
}
```

## rationale

- real navigation dependencies on `record` and `model-form` compat route names were removed in batch `BQ`
- the remaining known dependency set is now dominated by presentation-only route-name conditions in `AppShell.vue`
- router compat entry retirement is therefore no longer blocked by true navigation ownership
- however, direct retirement is still not cleanly eligible until those shell/display conditions are migrated or explicitly retired

## decision

- do not retire router compat entries yet in this batch
- next bounded batch should target `AppShell.vue` presentation conditions that still branch on `action/record/model-form`
- after that presentation migration, router compat entry retirement should become a cleanly eligible final cleanup batch

# FE Router Compat Caller Migration Screen BJ v1

## classification

```json
{
  "real_navigation_dependencies": [
    "frontend/apps/web/src/views/RecordView.vue",
    "frontend/apps/web/src/views/ActionView.vue",
    "frontend/apps/web/src/pages/ContractFormPage.vue",
    "frontend/apps/web/src/components/view/ViewRelationalRenderer.vue"
  ],
  "presentation_only_dependencies": [
    "frontend/apps/web/src/layouts/AppShell.vue"
  ],
  "retirement_eligibility": "not_yet_eligible",
  "required_next_batch": "call_site_migration_implement",
  "backend_semantic_blocker": "none"
}
```

## rationale

- real navigation dependencies still exist where code explicitly pushes compat route names:
  - `RecordView.vue` pushes `name: 'record'`
  - `ActionView.vue` pushes `name: 'model-form'`
  - `ContractFormPage.vue` pushes `name: 'model-form'`
  - `ViewRelationalRenderer.vue` pushes `name: 'record'`
- presentation-only dependencies exist in `AppShell.vue`, where route names are used for shell mode and display classification rather than navigation ownership
- because true navigation call sites still exist, router compat entry retirement is not yet eligible
- the next correct step is a bounded implementation batch that migrates the real navigation call sites to direct scene-first navigation, followed by a recheck on whether the presentation-only route-name conditions also need remapping

## decision

- do not open direct router compat entry retirement yet
- open a bounded caller-migration implementation batch first, focused only on the real navigation dependencies listed above

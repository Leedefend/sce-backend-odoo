# FE Router Compat Entry Retention Screen BI v1

## classification

```json
{
  "retention_decision": "retain_for_now",
  "retention_kind": "internal_compatibility_entry_surface",
  "retirement_eligibility": "not_yet_safe_without_call_site_migration_screen",
  "dominant_reason": "existing in-repo push-by-name flows still target action/record/model-form route names",
  "backend_semantic_blocker": "none"
}
```

## rationale

- recent bounded evidence already shows in-repo callers still navigate through:
  - `name: 'record'`
  - `name: 'model-form'`
  - route-name checks for `action/record/model-form` inside shell/layout logic
- the router compat entries no longer own shell-page rendering, so their current cost/risk is already much lower than before
- because those names still participate in internal navigation compatibility, immediate retirement would require a separate bounded migration screen first
- therefore the correct current classification is:
  - keep them for now as compatibility entry surface
  - do not treat them as permanent product boundary
  - only open retirement implementation after a dedicated caller-migration screen

## decision

- next governance step, if continued, should screen the remaining in-repo callers of `action/record/model-form` route names and classify whether they can be migrated safely to direct scene-first navigation
- direct retirement implementation is not yet eligible from the current evidence set

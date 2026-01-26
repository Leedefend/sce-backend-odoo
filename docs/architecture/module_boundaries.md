---
capability_stage: P0.1
status: active
since: v0.3.0-stable
---
# Module Boundaries

This document defines responsibilities, red lines, and lightweight move rules for modules.

## Dependency Direction (must be one-way)

```
odoo_test_helper (tools)
  -> sc_norm_engine (standards)
     -> smart_construction_bootstrap (setup)
        -> smart_construction_core (product)
           -> smart_construction_custom (client extension)
           -> smart_construction_seed (baseline init)
           -> smart_construction_demo (demo data)
```

Core must not depend on demo/seed/custom. Seed must not depend on demo.

## Module Responsibilities

### smart_construction_bootstrap
- Minimal system bring-up: locale/timezone/currency, required parameters, safe defaults.
- No business models or demo content.

### smart_construction_core
- Product models, business rules, state machine, ACL/record rules.
- Official views/actions/menus and UI contract behavior.
- Contract v1 APIs and UI contracts live here.

### smart_construction_custom
- Client-specific fields, workflows, reports, and UI overrides.
- Must extend core contracts, not replace them.

### smart_construction_seed
- Deterministic, idempotent initialization for new databases.
- Baseline dictionaries, minimal system data, environment consistency.
- Must fail fast with a clear message on old/non-empty databases.

### smart_construction_demo
- Demo-only data, showcase content, demo users/roles.
- No business logic or guard bypasses.

### sc_norm_engine
- Industry standards and validation dictionaries.

### odoo_test_helper
- Test utilities only.

## Red Lines
- Core must not include demo/seed-only shortcuts or guards.
- Demo must not introduce or modify production behavior.
- Seed must be idempotent and safe to re-run on new DBs only.
- Custom must not alter Contract v1 semantics.

## Lightweight Move Rules
- Action/view definitions referenced by other XML must load before use; if needed, split into a small `*_views.xml` or `*_actions_views.xml` and load early.
- Demo data belongs in `smart_construction_demo`; never in core.
- Seed steps belong in `smart_construction_seed/seed/steps`, and may create minimal records required by guards (with explicit comments).
- Contract v1 endpoints and UI contracts belong to core; custom may add fields via extension points only.

## Related SOP
- Seed lifecycle: `docs/ops/seed_lifecycle.md`
- Release checklist: `docs/ops/release_checklist_v0.3.0-stable.md`

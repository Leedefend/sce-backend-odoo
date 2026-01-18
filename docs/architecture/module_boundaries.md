---
capability_stage: P0.1
status: active
since: v0.3.0-stable
---
# Module Boundaries

This document defines responsibilities and dependency rules for modules.

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

Core must **not** depend on demo/seed/custom. Demo and custom must not push business logic into core.

## Module Responsibilities

### smart_construction_core
- Business models, fields, views, menus, actions.
- ACLs/record rules.
- UI components (sidebar, workbench, login redirect).
- Must be installable without demo/seed.

### smart_construction_seed
- Idempotent baseline initialization (ICP defaults, dictionaries, minimal stages).
- Profiles (`base`, `demo_full`).
- Must be safe to re-run.

### smart_construction_demo
- Demo data only (users, demo projects, demo dictionaries).
- No behavior hooks.
- Must be removable without affecting production behavior.

### smart_construction_custom
- Client-specific variations (workflow differences, reports, labels).
- Should not be required for demo unless explicitly planned.

### smart_construction_bootstrap
- Installation/initial setup helpers (if module-based).

### sc_norm_engine
- Industry standards, dictionaries, validations.

### odoo_test_helper
- Test helpers only (no production behavior).

## Forbidden Patterns
- Core depends on demo/seed/custom.
- Demo provides behavior hooks that change production behavior.
- Seed writes demo-only data into prod.

## Related SOP
- Seed lifecycle: `docs/ops/seed_lifecycle.md`
- Release checklist: `docs/ops/release_checklist_v0.3.0-stable.md`

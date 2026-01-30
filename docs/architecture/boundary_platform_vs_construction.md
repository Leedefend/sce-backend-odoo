# Boundary: Platform (smart_core) vs Construction Domain

## Purpose
Define what belongs to platform core (`smart_core`) and what must live in construction domain modules (e.g. `smart_construction_core`). This prevents reverse dependencies and keeps the platform extensible.

## Dependency Direction Rule
- smart_core MUST NOT import any construction modules.
- Construction modules MAY import smart_core.
- Enforcement: `make audit.boundary.smart_core` (and `make gate.boundary`).

## Platform Intents (smart_core)
These are stable, platform-level intents:
- `login`
- `auth.logout`
- `system.init`
- `ui.contract`
- `load_contract`
- `load_view`
- `load_metadata`
- `api.data`
- `meta.describe_model`
- `execute_button`

If an intent is generic and not construction-specific, it can stay in smart_core.

## Construction Domain Intents (smart_construction_*)
These are construction-specific and must live outside smart_core:
- Anything tied to construction roles, menu roots, settlement/ledger/boq/payment semantics
- Domain-specific portals, dashboards, or workflows

## Extension Registration Contract
Construction modules can register handlers into smart_core via hook:

```python
def smart_core_register(registry):
    # registry is a dict of intent -> handler class
    registry["your.intent"] = YourHandlerClass
```

Configuration:
- `ir.config_parameter`: `sc.core.extension_modules`
- Format: comma-separated module names (e.g. `smart_construction_core,smart_construction_portal`)

Example:
```
sc.core.extension_modules = smart_construction_core
```

Demo intent (from smart_construction_core):
- `system.ping.construction`

Behavior:
- Missing modules are skipped with a warning (no crash).
- Hook is optional; modules without it are skipped with a warning.

## How to Add a New Business Intent
1) Implement handler in a construction module.
2) Add `smart_core_register(registry)` in that module.
3) Add module name to `sc.core.extension_modules`.
4) Verify with `make audit.boundary.smart_core` and `make verify.smart_core`.

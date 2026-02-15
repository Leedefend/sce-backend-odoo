# Menu Scene Coverage Evidence (Current Baseline)

## Scope

- Delivery/release review baseline for sidebar menu -> scene semantic coverage.
- Default enforcement only targets business namespaces:
  - `smart_construction_core.`
  - `smart_construction_demo.`
  - `smart_construction_portal.`

## Commands

```bash
make verify.extension_modules.guard DB_NAME=sc_demo
make verify.menu.scene_resolve.container DB_NAME=sc_demo E2E_LOGIN=demo_pm E2E_PASSWORD=demo
make verify.menu.scene_resolve.summary
make verify.phase_9_8.gate_summary
```

Optional strict-all namespace mode:

```bash
MENU_SCENE_ENFORCE_PREFIXES= make verify.menu.scene_resolve.container DB_NAME=sc_demo E2E_LOGIN=demo_pm E2E_PASSWORD=demo
```

## Required Evidence Keys

From `artifacts/codex/summary.md`:

- `menu_scene_resolve_effective_total`
- `menu_scene_resolve_coverage`
- `menu_scene_resolve_enforce_prefixes`
- `menu_scene_resolve_exempt_manual`
- `menu_scene_resolve_exempt_auto`

From `artifacts/codex/phase-9-8/gate_summary.json`:

- `menu_scene_resolve.summary.effective_total`
- `menu_scene_resolve.summary.coverage`
- `menu_scene_resolve.summary.enforce_prefixes`
- `menu_scene_resolve_quick.exempt_manual`
- `menu_scene_resolve_quick.exempt_auto`

## Review Rule

- Business delivery review is PASS only when:
  - extension baseline includes both `smart_construction_core` and `smart_construction_portal`
  - `menu_scene_resolve_failures = 0`
  - and `menu_scene_resolve_coverage = 100%` under default business enforcement prefixes.

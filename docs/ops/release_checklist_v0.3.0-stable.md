---
capability_stage: P0
status: frozen
since: v0.3.0-stable
---
# Release Checklist — v0.3.0-stable

## Preconditions
- Working tree clean
- Tag `v0.3.0-stable` exists locally and on origin
- `docs/ops/release_notes_v0.3.0-stable.md` reviewed

## Guard Verification (required)
- `ENV=prod make verify.prod.guard` passes (guard-only)
- JSON summary emitted by `scripts/verify/prod_guard_smoke.sh`
- Release is approved iff JSON reports `rc=0`
- Runtime extension baseline for demo gate is satisfied:
  - `make verify.extension_modules.guard DB_NAME=sc_demo`
  - required module tokens in `sc.core.extension_modules`:
    - `smart_construction_core`
    - `smart_construction_portal`
- Phase 9.8 menu/scene coverage summary is present in release evidence:
  - `make verify.menu.scene_resolve.summary`
  - required keys in `artifacts/codex/summary.md`:
    - `menu_scene_resolve_effective_total`
    - `menu_scene_resolve_coverage`
    - `menu_scene_resolve_enforce_prefixes`
  - default business enforcement scope:
    - `MENU_SCENE_ENFORCE_PREFIXES=smart_construction_core.,smart_construction_demo.,smart_construction_portal.`

## Production Safety Checks
- `ENV=prod` forbids: `make db.reset`, `make demo.*`, `make ci.*`, `make gate.*`
- `ENV=prod` requires `PROD_DANGER=1` for `mod.install`, `mod.upgrade`, policy apply
- `seed.run` in prod requires explicit DB name (`SEED_DB_NAME_EXPLICIT=1`)

## Seed Base (if running)
- `SC_SEED_PROFILE=base` only
- `SC_BOOTSTRAP_USERS=1` requires `SEED_ALLOW_USERS_BOOTSTRAP=1` and password

## Post-Release
- Record verification output (JSON) in release log
- Confirm branch `main` matches tag:
  - `git rev-parse v0.3.0-stable`
  - `git rev-parse main`

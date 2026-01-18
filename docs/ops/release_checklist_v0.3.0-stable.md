# Release Checklist — v0.3.0-stable

## Preconditions
- Working tree clean
- Tag `v0.3.0-stable` exists locally and on origin
- `docs/ops/release_notes_v0.3.0-stable.md` reviewed

## Guard Verification (required)
- `ENV=prod make verify.prod.guard` passes (guard-only)
- JSON summary emitted by `scripts/verify/prod_guard_smoke.sh`
- Release is approved iff JSON reports `rc=0`

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

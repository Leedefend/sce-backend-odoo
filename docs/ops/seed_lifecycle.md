# Seed Lifecycle

This document defines how seed is used across environments and what is allowed in production.

## Purpose
- Seed initializes a **usable baseline** for a new database.
- Seed is **not** demo data and **not** migration.

## Profiles
- `base`: production-safe baseline configuration.
- `demo` / `demo_full`: demo-only data and flows.

## Production Rules
- Only `PROFILE=base` is allowed in prod.
- `seed.run` in prod must be explicit: `SEED_DB_NAME_EXPLICIT=1` + `DB_NAME=<target>`.
- Users bootstrap is opt-in:
  - `SC_BOOTSTRAP_USERS=1` requires `SEED_ALLOW_USERS_BOOTSTRAP=1`.
  - `SC_BOOTSTRAP_ADMIN_PASSWORD` is mandatory.

## Typical Commands
- Base profile (prod-safe):
  - `ENV=prod SEED_DB_NAME_EXPLICIT=1 PROFILE=base DB_NAME=sc_prod make seed.run`
- Base + users bootstrap:
  - `ENV=prod SEED_DB_NAME_EXPLICIT=1 SEED_ALLOW_USERS_BOOTSTRAP=1 SC_BOOTSTRAP_USERS=1 \
    SC_BOOTSTRAP_ADMIN_PASSWORD='***' PROFILE=base DB_NAME=sc_prod make seed.run`

## Common Failure Causes
- Missing admin password when `SC_BOOTSTRAP_USERS=1`.
- Missing explicit DB name in prod.
- Using `demo_full` profile in prod (guarded).

## Related SOP
- Production command policy: `docs/ops/prod_command_policy.md`
- Release checklist: `docs/ops/release_checklist_v0.3.0-stable.md`

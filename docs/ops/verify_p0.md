---
capability_stage: P0
status: frozen
since: v0.3.0-stable
---
# P0 Verification (Base Usable)

This verifies a fresh database can install core + seed, apply the base profile,
and pass minimal usability checks.

## One-shot flow

```bash
make verify.p0.flow DB_NAME=sc_p0_base
```

## What it does

1) Reset database
2) Install core
3) Install seed
4) Run P0 checks (ICP defaults, dictionary presence, project stages)

## Notes

- Requires `SC_SEED_ENABLED=1` and `SC_SEED_PROFILE=base` during install/reset.
- For local runs, export envs before calling make:
- Production command policy: `docs/ops/prod_command_policy.md`
- Release checklist (stable): `docs/ops/release_checklist_v0.3.0-stable.md`

```bash
export SC_SEED_ENABLED=1
export SC_SEED_PROFILE=base
```

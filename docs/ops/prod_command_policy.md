# Production Command Policy

This policy enforces safe command usage in production. It is enforced by
Makefile guards and script-level guards.

## Allowed (safe)

- `make up/down/logs/ps`
- `make diag.project`
- `make verify.baseline` (requires PROD_DANGER=1)
- `make verify.p0` (requires PROD_DANGER=1)
- `make verify.p0.flow` (requires PROD_DANGER=1)

## Allowed with PROD_DANGER=1 (danger)

- `make mod.install`
- `make mod.upgrade`
- `make restart` (requires PROD_DANGER=1)
- `make prod.restart.safe` (requires PROD_DANGER=1)
- `make prod.restart.full` (requires PROD_DANGER=1)
- `make policy.apply.business_full`
- `make policy.apply.role_matrix`
- `make audit.project.actions`
- `make prod.upgrade.core`

## Forbidden in prod (hard stop)

- `make db.reset` / `db.reset.manual`
- `make demo.reset` / `demo.load*` / `demo.rebuild` / `demo.ci` / `demo.full` / `demo.repro` / `demo.verify`
- `make gate.*` / `make gate.audit`
- `make test` / `make test.safe`
- `make ci.*`
- `make verify.ops`
- `make seed.run PROFILE!=base`
- `make seed.run` with `SC_BOOTSTRAP_USERS=1` unless `SEED_ALLOW_USERS_BOOTSTRAP=1`

## Examples

Enable a guarded operation:

```bash
ENV=prod PROD_DANGER=1 make mod.upgrade MODULE=smart_construction_seed DB_NAME=sc_prod
```

Allow bootstrap users in prod:

```bash
ENV=prod SEED_ALLOW_USERS_BOOTSTRAP=1 SC_BOOTSTRAP_USERS=1 PROFILE=base make seed.run DB_NAME=sc_prod
```

Blocked demo in prod:

```bash
ENV=prod make demo.reset DB_NAME=sc_demo
```

## Notes

- `ENV=prod` or `ENV_FILE=.env.prod` triggers production guard.
- Guards also apply when scripts are called directly (bypassing Makefile).

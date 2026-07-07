# Environment Tiers Unified Runbook v1

## Scope

This runbook unifies three execution tiers:

- Daily development (`dev`)
- Test dedicated (`test`)
- Production (`prod`)

It is the single command policy for environment setup, script usage, and Makefile entrypoints.

## Layer Target / Module / Reason

- Layer Target: `Governance Layer (Ops/Execution Policy)`
- Module: `Makefile + env governance + runbook`
- Reason: prevent mis-execution caused by mixed DB knobs and non-standard command paths before formal deployment.

## Single Source of Truth

1. Environment variables must come from `.env.<tier>` or explicit CLI override.
2. Canonical database knob is `DB_NAME`.
3. Compatibility aliases:
- `DB` is accepted.
- `BD` is legacy only.
4. Priority is fixed:
- `DB_NAME` > `DB` > `BD` > default value.

## Tier Profiles

| Tier | ENV | ENV_FILE | DB baseline | Usage |
| --- | --- | --- | --- | --- |
| Daily dev | `dev` | `.env.dev` | `sc_demo` | Day-to-day feature work, replay rehearsal |
| Test dedicated | `test` | `.env.test` | `sc_test` | CI-like gates, strict verification |
| Production | `prod` | `.env.prod` | `sc_prod` | Formal deployment only, guarded operations |

## Runtime Topology

| Tier | Host alias | Runtime path | ENV | ENV_FILE | DB_NAME |
| --- | --- | --- | --- | --- | --- |
| Daily dev | `sc-root` | `/opt/projects/repos/sce-backend-odoo` | `dev` | `.env.dev` | `sc_demo` |
| Production | `sc-prod` | `/opt/sce/production/sce-backend-odoo` | `prod` | `.env.prod` | `sc_prod` |

The daily development runtime repository is the only deployable `dev` working tree.
Before publishing or upgrading it, run `make verify.daily_dev.runtime_repo.clean`
inside `/opt/projects/repos/sce-backend-odoo`.
Daily acceptance publication must use `make release.daily_dev.acceptance.publish`
from that same runtime repository.
That target only accepts `ENV=dev`, `ENV_FILE=.env.dev`, and `DB_NAME=sc_demo`;
wrong DB or tier parameters must fail before frontend build or acceptance probes run.

Production code authority is `main` or a frozen release package applied under `/opt/sce/production/sce-backend-odoo`.
If production is a Git working tree, run `make verify.production_git.authority.guard` before upgrade.
Do not deploy from scratch worktrees or archived runtime directories.

## Mandatory Preflight

Always run before operations:

```bash
make env.matrix.check
```

This command checks:

- `.env.dev/.env.test/.env.prod` presence and required keys
- three-tier env validation via `check-compose-env`
- DB knob precedence (`DB_NAME`, `DB`, `BD`) to avoid wrong-database execution
- runtime topology policy for daily development and production

## Standard Command Entry

Use Makefile only for runtime-changing actions:

- container lifecycle: `make up/down/restart/logs/ps`
- DB reset / seed / demo: `make db.reset`, `make seed.run`, `make demo.*`
- module install/upgrade: `make mod.install`, `make mod.upgrade`
- verifications/gates: `make verify.*`, `make gate.*`

## Forbidden Usage

Do not use ad-hoc direct commands for state mutation:

- direct `docker compose exec ...` for core flows that already have Make targets
- direct SQL mutation outside governed scripts
- mixed DB knobs in one command (for example setting both `DB_NAME` and `DB` with conflicting values)

## Canonical Usage Examples

Daily:

```bash
ENV=dev ENV_FILE=.env.dev DB_NAME=sc_demo make seed.run
```

Test:

```bash
ENV=test ENV_FILE=.env.test DB_NAME=sc_test make verify.restricted
```

Production (guarded):

```bash
ENV=prod ENV_FILE=.env.prod DB_NAME=sc_prod make verify.prod.guard
```

## Merge-to-main Gate (Deployment Readiness)

Before integrating to `main`, required minimum:

1. `make env.matrix.check`
2. required verification bundle for this batch (at least restricted gate)
3. run controlled merge path only (`make codex.merge`) after explicit approval

If any check fails, stop integration and fix environment policy drift first.

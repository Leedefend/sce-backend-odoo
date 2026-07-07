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
it also requires `ACCEPTANCE_BASE_URL=http://127.0.0.1:18081` and
`ACCEPTANCE_LOGIN=wutao`, a non-empty `ACCEPTANCE_PASSWORD`, and
`ACCEPTANCE_NAV_MIN_ACTIONS=60`, `ACCEPTANCE_NAV_MAX_ACTIONS=70`, and
`ACCEPTANCE_NAV_FORBIDDEN_LABELS=用户核对菜单,用户数据验收,用户验收,直营项目系统菜单`.
`ACCEPTANCE_NAV_REQUIRED_PATHS` must include the locked daily product path
sample covering customer, supplier, project ledger, general contract,
construction diary, inbound, payment request, project capital overview, payroll,
company archive, and input invoice entries.
`ACCEPTANCE_NAV_REQUIRED_ACTIONS` must pin that same sample to locked runtime
action ids.
`ACCEPTANCE_PROBE_OUTPUT=artifacts/backend/dev_acceptance_release_probe.json`.
The frontend build output must stay `FRONTEND_DIST_DIR=./frontend/apps/web/dist-dev`,
and `VITE_ODOO_DB`, `VITE_APP_ENV`, `VITE_BUILD_MODE`, and
`VITE_BUILD_OUT_DIR` must not be overridden. `VITE_PLATFORM_ADMIN_DB` must stay
`sc_platform_core`, and `VITE_API_BASE_URL`, `VITE_API_PROXY_TARGET`,
`VITE_ODOO_DB_LOCKED`, `VITE_DELIVERY_MODE`, `VITE_FEATURE_FLAGS`,
`VITE_LITE_CONTRACT_PILOT`, `VITE_LITE_CONTRACT_ROLLOUT`, and `VITE_TENANT`
must stay unset. Wrong DB, tier, served URL, evidence
path, or frontend build/runtime override parameters must fail before frontend
build or acceptance probes run.

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

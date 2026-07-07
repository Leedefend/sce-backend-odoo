# System Capability Baseline v1

## 1. Baseline Purpose

This baseline is the new system-level reference point after the current
front-end and back-end iteration. Future work should compare against this file
before changing contracts, navigation, scene delivery, frontend rendering, or
release operations.

## 2. Boundary

- Layer Target: Product / Contract / Frontend / Ops baseline
- Module: full system capability baseline
- Reason: give later iterations a stable capability floor and a repeatable
  verification path.

This baseline does not introduce new business behavior. It freezes the current
accepted capability posture and defines how later batches may extend it.

## 3. Baseline Layers

| Layer | Capability Floor | Primary Evidence |
|---|---|---|
| Platform runtime | `login -> system.init -> ui.contract` remains the startup chain; role source is `role_surface.role_code`; default route comes from backend contract. | `make verify.backend.guard`, `make verify.contract.snapshot` |
| Contract surface | Scene/catalog/runtime contract must be deterministic, versioned, and schema-guarded. | `make verify.business.capability_baseline.guard`, `make verify.contract.evidence.guard` |
| Product boundary | Platform, industry, user, low-code, and ops ownership must stay explicit and addon modules must be mapped to a formal product layer. | `make verify.docs.product_boundary`, `docs/product/formal_product_boundary_v1.md` |
| Frontend consumer | Web frontend consumes backend contract without semantic guessing; served static bundle must match target DB/env for acceptance. | `make verify.frontend.typecheck.strict`, `make verify.frontend.build` |
| Business delivery | 9 delivery modules and 22 scoped scenes are the current product delivery floor. | `docs/product/delivery/v1/module_scene_capability_map.md` |
| Ops release | Uploaded backup, frontend static publication, API lock, runtime repository cleanliness, and real-user acceptance are repeatable checks. Daily acceptance also locks product navigation size, forbidden labels, required paths, and required action targets. | `make verify.dev.acceptance.release`, `make release.daily_dev.acceptance.publish` |

## 4. Frozen Capability Floor

| Dimension | Baseline |
|---|---|
| Delivery modules | 9 |
| Delivery scoped scenes | 22 |
| Required business intents | >= 10 |
| Required role floors | >= 4 |
| Dev acceptance DB | `sc_demo` |
| Simulated production DB | `sc_prod_sim` |
| Real-user release probe | Required when an acceptance user is provided |

## 5. Iteration Rules

1. Each batch must declare `Layer Target`, `Module`, and `Reason`.
2. A batch may raise the baseline only after its own implementation and gate
   evidence pass.
3. A batch may not lower the baseline unless the rollback or de-scope is
   explicitly documented.
4. Contract/schema changes must update the contract evidence path before
   frontend consumption changes are accepted.
5. Frontend changes that affect user-visible acceptance must rebuild the served
   static bundle, not only restart the Vite dev server.
6. Release or restore flows must preserve database and filestore pairing.
7. Real-user continuity checks should use canonical users such as `wutao`,
   `chenshuai`, or the user-specified acceptance account, not only service
   smoke credentials.

## 6. Default Verification Ladder

Use the lightest command that proves the batch boundary:

```bash
make verify.system.capability_baseline.report
make verify.docs.product_boundary
make verify.restricted
make verify.business.capability_baseline.guard
make verify.scene.delivery.readiness.role_company_matrix
make verify.product.delivery.mainline
```

For dev acceptance publication:

```bash
ENV=dev ENV_FILE=.env.dev DB_NAME=sc_demo \
  ACCEPTANCE_BACKUP_DIR=<uploaded_backup_dir> \
  ACCEPTANCE_BASE_URL=http://127.0.0.1:18081 \
  make release.daily_dev.acceptance.publish
```

## 7. Baseline Sources

- Policy: `scripts/verify/baselines/system_capability_baseline_v1.json`
- Report: `artifacts/backend/system_capability_baseline_report.json`
- Formal product boundary: `docs/product/formal_product_boundary_v1.md`
- Delivery map: `docs/product/delivery/v1/module_scene_capability_map.md`
- Delivery scoreboard: `docs/product/delivery/v1/delivery_readiness_scoreboard_v1.md`
- Dev acceptance runbook: `docs/ops/dev_acceptance_release_runbook_v1.md`

## 8. Stop Conditions

- Startup chain payload changes without contract evidence.
- Role source drifts away from `role_surface.role_code`.
- A new addon module exists without a formal product boundary row.
- Formal product boundary loses P0-P4 product layers or delivery acceptance rules.
- A delivery module loses its scene mapping.
- Served frontend bundle defaults to the wrong acceptance DB.
- A release probe cannot authenticate and run `system.init` for the named
  real-user acceptance account.
- Daily acceptance navigation loses a required product path, exposes a forbidden
  legacy label, or maps a locked path to the wrong action target.

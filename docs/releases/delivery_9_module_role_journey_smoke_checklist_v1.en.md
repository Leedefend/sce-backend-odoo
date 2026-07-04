# 9-Module Role-Journey Smoke Checklist v1

## 1. Purpose

Turn “9-module deliverability” into an executable, system-bound acceptance checklist with a unified command set, pass criteria, and evidence paths.

---

## 2. Baseline Commands (Common for all modules)

```bash
make verify.scene.delivery.readiness.role_matrix
make verify.portal.role_surface_smoke.container
make verify.portal.scene_health_contract_smoke.container
make verify.portal.scene_health_pagination_smoke.container
make verify.frontend.quick.gate
```

Pass criteria:

- all commands exit with code 0
- output contains `PASS`
- artifacts are traceable under `artifacts/backend/*` and `artifacts/codex/*`

---

## 3. Module-Level Role Journeys (Executable Items)

| Module | Key Roles | Verification Command | Current Result | Notes |
|---|---|---|---|---|
| Project Management | PM / Executive | `make verify.portal.role_surface_smoke.container` | PASS | landing scenes verified |
| Project Execution | PM | `make verify.scene.delivery.readiness.role_matrix` | PASS | runtime boundary + role matrix passed |
| Task Management | PM | `make verify.scene.delivery.readiness.role_matrix` | PASS | covered by scene-readiness main chain |
| Risk Management | PM / Executive | `make verify.scene.delivery.readiness.role_matrix` | PASS | covered by scene-readiness main chain |
| Cost Management | PM / Finance | `make verify.scene.delivery.readiness.role_matrix` | PASS | covered by scene-readiness main chain |
| Contract Management | PM / Executive | `make verify.scene.delivery.readiness.role_matrix` | PASS | covered by scene-readiness main chain |
| Finance Management | Finance / Executive | `make verify.portal.payment_request_approval_all_smoke.container` | PASS | finance -> executive handoff passed |
| Data & Dictionary | Config Admin | `make verify.scene.delivery.readiness.role_matrix` | PASS | entry + governance chain covered |
| Config Center | Config Admin | `make verify.scene.delivery.readiness.role_matrix` | PASS | entry + governance chain covered |

---

## 4. Blocker Closeout (Final)

Command:

```bash
make verify.portal.payment_request_approval_all_smoke.container
```

Result: PASS (2026-07-05)

Core failure message:

- `payment_request_approval_smoke`: PASS
- `payment_request_approval_handoff_smoke`: PASS
- `verify.portal.payment_request_approval_field_consumer_audit`: PASS (`unexpected_deprecated_refs=0`)
- after finance submit, executive sees `approve/reject` and completes approve handoff.

Conclusion: finance cross-role approval handoff is closed.

---

## 5. Next Actions

1. Keep `make verify.portal.payment_request_approval_all_smoke.container` as the finance journey regression.
2. Keep `make verify.release.delivery_9_module.final_closeout.guard` as the 9-module document/evidence closeout gate.
3. Route later role journeys into normal iteration without reopening this P0.

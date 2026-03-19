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
| Finance Management | Finance / Executive | `make verify.portal.payment_request_approval_all_smoke.container` | FAIL | handoff flow is blocked (see section 4) |
| Data & Dictionary | Config Admin | `make verify.scene.delivery.readiness.role_matrix` | PASS | entry + governance chain covered |
| Config Center | Config Admin | `make verify.scene.delivery.readiness.role_matrix` | PASS | entry + governance chain covered |

---

## 4. Blocker Found in This Iteration

Command:

```bash
make verify.portal.payment_request_approval_all_smoke.container
```

Result: FAIL

Core failure message:

- `payment_request_approval_handoff_smoke` failed
- reason: `executive has no allowed follow-up action after submit`
- actual allowed actions: `['submit']`
- expected follow-up action: one of `approve/reject`

Conclusion: this is a P0 blocker for finance cross-role approval handoff and must be tracked explicitly.

---

## 5. Next Actions

1. fix payment request handoff strategy/permission mapping (finance → executive)
2. rerun:

```bash
make verify.portal.payment_request_approval_all_smoke.container
```

3. once green, move finance module status from `FAIL/BLOCKED` to `IN_PROGRESS` or `READY_FOR_PILOT`


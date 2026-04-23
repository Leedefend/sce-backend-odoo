# Native Runtime Environment Repair Lane Batch8 Process/Entry Diagnostics v1

## Scope

- Task: `ITER-2026-04-07-1221`
- Objective: collect process status and entry-log diagnostics around 8069 handshake failures

## Process-Level Signals

- `docker compose ... ps` for dev project shows:
  - `db`, `redis`, `nginx` running
  - `odoo` service is not listed as active in current snapshot

## Entry/Log Signals

- `docker compose ... logs --tail=120 odoo` returns historical `odoo-1` login traffic logs.
- Direct runtime evidence in this cycle still reports:
  - `8069 -> RemoteDisconnected`
  - `8070 -> timeout`

## Interpretation

- Service-chain state appears inconsistent: listener/path responds at transport layer, yet compose service snapshot does not show active `odoo` container.
- This supports a runtime process/entry boundary issue, not a verify-helper semantic issue.

## Verification

- `make verify.scene.legacy_auth.runtime_probe`: PASS
- `make verify.scene.legacy_contract.guard`: PASS
- `make verify.test_seed_dependency.guard`: PASS
- `make verify.scene.legacy_auth.smoke.semantic`: PASS

## Conclusion

- Batch8 PASS with process/entry diagnostics evidence.
- Next step should be environment execute action to reconcile compose runtime state for `odoo` service and re-check `/api/scenes/my` live response.

## Legacy Endpoint Deprecation Note
- `/api/scenes/my` is deprecated.
- Successor endpoint: `/api/v1/intent` with `intent=app.init`.
- Sunset date: `2026-04-30`.
- Deprecation header contract reference: `Deprecation`, `Sunset`, `Link`, `X-Legacy-Endpoint`.

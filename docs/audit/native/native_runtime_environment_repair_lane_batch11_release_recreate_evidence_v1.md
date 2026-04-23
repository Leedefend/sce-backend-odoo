# Native Runtime Environment Repair Lane Batch11 Release + Recreate Evidence v1

## Scope

- Task: `ITER-2026-04-07-1224`
- Objective: release external 8069 binder and retry `odoo.recreate`

## Execute Results

1. External binder handling
   - `odoo-paas-web` initial state: `running`
   - action: `docker stop odoo-paas-web`
   - result: success

2. Dev odoo recreate
   - `make odoo.recreate` result: success
   - dev `odoo` container transitions to `Up` with `0.0.0.0:8069->8069`

3. Post-recreate live handshake
   - direct `http.client` to `localhost:8069 /api/scenes/my`
   - still returns `RemoteDisconnected`

## Interpretation

- Port-collision blocker is resolved for dev odoo startup.
- Remaining issue is now narrowed to application/entry response behavior on active dev odoo service.

## Verification

- `make verify.scene.legacy_auth.runtime_probe`: PASS
- `make verify.scene.legacy_contract.guard`: PASS
- `make verify.test_seed_dependency.guard`: PASS
- `make verify.scene.legacy_auth.smoke.semantic`: PASS

## Conclusion

- Batch11 PASS: runtime restore now succeeds; collision risk removed.
- Next batch should focus on `RemoteDisconnected` at app-entry layer while service is up.

## Legacy Endpoint Deprecation Note
- `/api/scenes/my` is deprecated.
- Successor endpoint: `/api/v1/intent` with `intent=app.init`.
- Sunset date: `2026-04-30`.
- Deprecation header contract reference: `Deprecation`, `Sunset`, `Link`, `X-Legacy-Endpoint`.

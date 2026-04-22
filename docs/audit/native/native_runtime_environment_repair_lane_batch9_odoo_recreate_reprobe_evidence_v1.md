# Native Runtime Environment Repair Lane Batch9 Odoo Recreate Re-Probe Evidence v1

## Scope

- Task: `ITER-2026-04-07-1222`
- Objective: minimal runtime restore attempt (`make odoo.recreate`) and re-probe

## Execute Result

- `make odoo.recreate` failed:
  - docker daemon bind error on `0.0.0.0:8069`
  - message: `Bind for 0.0.0.0:8069 failed: port is already allocated`

## Post-Attempt Diagnostics

- `docker compose ... ps` still shows only `db/redis/nginx` active in project snapshot.
- direct `http.client` probe to `localhost:8069 /api/scenes/my` still returns `RemoteDisconnected`.
- `ss -ltnp` confirms `*:8069` listener exists but owner details are not exposed in current environment.

## Verification

- `make verify.scene.legacy_auth.runtime_probe`: PASS
- `make verify.scene.legacy_contract.guard`: PASS
- `make verify.test_seed_dependency.guard`: PASS
- `make verify.scene.legacy_auth.smoke.semantic`: PASS

## Risk Summary

- **PASS_WITH_RISK**: runtime execute objective blocked by external port allocation conflict.
- Service-state recovery cannot be completed with certainty without resolving port owner contention.

## Conclusion

- Batch9 provides actionable blocker evidence.
- Next batch must focus on port-collision owner identification/resolution before further runtime restore attempts.

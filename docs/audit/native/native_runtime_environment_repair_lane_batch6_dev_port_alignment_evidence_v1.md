# Native Runtime Environment Repair Lane Batch6 Dev Port Alignment Evidence v1

## Scope

- Task: `ITER-2026-04-07-1219`
- Objective: switch `.env.dev` `ODOO_PORT` from `8070` to `8069`

## Change

- `.env.dev`
  - `ODOO_PORT=8070` -> `ODOO_PORT=8069`

## Verification Signals

- `make verify.scene.legacy_auth.runtime_probe`: PASS
  - primary base URL now resolves to `http://localhost:8069`
  - probe still emits companion 8070 sample because runtime probe includes fallback comparison URL
- `make verify.scene.legacy_contract.guard`: PASS
- `make verify.test_seed_dependency.guard`: PASS
- `make verify.scene.legacy_auth.smoke.semantic`: PASS

## Interpretation

- Dev explicit config now aligns with observed listener baseline.
- Remaining transport anomalies (`8069 -> RemoteDisconnected`) are runtime service behavior, not port-mapping ambiguity.

## Conclusion

- Batch6 PASS with successful configuration alignment.

# Native Runtime Environment Repair Lane Batch4 Fallback Port Fix Evidence v1

## Scope

- Task: `ITER-2026-04-07-1217`
- Objective: correct no-env default fallback port in HTTP smoke utils

## Change

- `scripts/verify/python_http_smoke_utils.py`
  - default port changed from `8070` to `8069` when `E2E_BASE_URL`/`ODOO_PORT` are absent

## Validation Evidence

- Direct base-url resolution check:
  - `E2E_BASE_URL= ODOO_PORT= ENV_FILE=/tmp/nonexistent_env_file python3 ... get_base_url()`
  - output: `http://localhost:8069`

- Gate runs remain PASS under current environment configuration:
  - `make verify.scene.legacy_auth.runtime_probe`
  - `make verify.scene.legacy_contract.guard`
  - `make verify.test_seed_dependency.guard`
  - `make verify.scene.legacy_auth.smoke.semantic`

## Note

- Current environment still resolves runtime probe to `8070` due explicit environment/config input.
- This batch fixes fallback behavior for no-config scenarios and future clean environments.

## Conclusion

- Batch4 PASS: fallback default now aligns with observed listener baseline (`8069`) when config is absent.

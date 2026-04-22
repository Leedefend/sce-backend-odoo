# auth_signup Smoke Recovery Screen (ITER-2026-04-05-1041)

## Failure Snapshot

- failed batch: `ITER-2026-04-05-1040`
- failed command:
  - `FRONTEND_API_BASE_URL=http://127.0.0.1:18069 python3 scripts/verify/scene_legacy_auth_smoke.py`
- observed error: `RemoteDisconnected` / connection issues during GET request.

## Evidence-Based Diagnosis

1. `scene_legacy_auth_smoke.py` resolves base URL via `get_base_url()` from `python_http_smoke_utils.py`.
2. `get_base_url()` uses `E2E_BASE_URL` first, then `ODOO_PORT`/`.env`, and **does not read** `FRONTEND_API_BASE_URL`.
3. Therefore, `1040` acceptance command passed an unrelated env var and could hit wrong endpoint/port.

Evidence:
- `scripts/verify/scene_legacy_auth_smoke.py` imports `get_base_url`.
- `scripts/verify/python_http_smoke_utils.py:get_base_url()` variable precedence.

## Recovery Verification

- executed corrected command:
  - `E2E_BASE_URL=http://127.0.0.1:18069 python3 scripts/verify/scene_legacy_auth_smoke.py`
- result: `PASS`

## Recovery Decision

- root cause classification: **acceptance command contract mismatch** (not auth controller logic failure).
- recovery action:
  1. update Implement-1 task pack acceptance command to use `E2E_BASE_URL` (or `ODOO_PORT`) for legacy auth smoke.
  2. rerun `1040` acceptance with corrected command set.

## Corrected Legacy Auth Smoke Command

- `E2E_BASE_URL=http://127.0.0.1:18069 python3 scripts/verify/scene_legacy_auth_smoke.py`

## Stop-Guard Note

- `1040` remains `FAIL` until acceptance is rerun and recorded under corrected command contract.

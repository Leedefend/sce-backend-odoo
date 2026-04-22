# Frontend API Timeout Recovery Screen (ITER-2026-04-05-1055)

## Screen Scope

- `scripts/verify/frontend_api_smoke.py`
- `Makefile` (`verify.frontend_api` target)
- runtime container reachability evidence

## Evidence

1. **`verify.frontend_api` default target is host URL `http://localhost:8070`**
   - `scripts/verify/frontend_api_smoke.py` defaults `FRONTEND_API_BASE_URL` to `http://localhost:8070`.
   - `Makefile` target `verify.frontend_api` does not override this base URL.

2. **Current running stacks do not expose `8070` for Odoo API**
   - active containers include:
     - `sc-backend-odoo-prod-sim-odoo-1` (`com.docker.compose.project=sc-backend-odoo-prod-sim`)
     - `odoo-paas-web` (`com.docker.compose.project=odoo-doubao`)
   - no active stack maps a healthy frontend API endpoint at `localhost:8070`.

3. **Host-side reachability in this execution environment is blocked/timeout**
   - direct host probes to `localhost:8070/8069/18069/18081` fail from current runner context.
   - `make verify.frontend_api` and escalated retry both timeout with `urllib.error.URLError: <urlopen error timed out>`.

4. **Container-local endpoint is reachable and smoke passes**
   - inside `sc-backend-odoo-prod-sim-odoo-1`, `http://localhost:8069/web/login` returns `200`.
   - container-local execution succeeds:
     - `FRONTEND_API_BASE_URL=http://localhost:8069 DB_NAME=sc_demo python3 /mnt/scripts/verify/frontend_api_smoke.py`
     - result: `[frontend_api] PASS (http://localhost:8069)`

## Root Cause Classification

- primary cause: **runtime endpoint mismatch + host-network unreachability in current runner context**.
- not caused by controller policy migration logic in `ITER-2026-04-05-1054`.

## Recovery Commands

### Recovery-A (recommended in current environment)

- run smoke inside active Odoo container:

```bash
docker exec sc-backend-odoo-prod-sim-odoo-1 sh -lc \
  "FRONTEND_API_BASE_URL=http://localhost:8069 DB_NAME=sc_demo python3 /mnt/scripts/verify/frontend_api_smoke.py"
```

### Recovery-B (host mode, only if host networking is reachable)

```bash
FRONTEND_API_BASE_URL=http://127.0.0.1:18069 DB_NAME=sc_demo make verify.frontend_api
```

## Suggested Next Batch

- open recovery-implement batch to replay `ITER-2026-04-05-1054` acceptance using Recovery-A evidence path,
  then either:
  - (a) mark 1054 reconciled PASS with container-local smoke evidence, or
  - (b) add an explicit env override wrapper for `verify.frontend_api` in this repo's local execution profile.

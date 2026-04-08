# ITER-2026-04-08-1361 Report

## Batch
- Batch: `1/1`

## Summary of change
- Installed/upgraded real-user carrier module on `sc_test`:
  - `make mod.install MODULE=smart_construction_custom ENV=test DB_NAME=sc_test`
  - `CODEX_NEED_UPGRADE=1 CODEX_MODULES=smart_construction_custom make mod.upgrade MODULE=smart_construction_custom ENV=test DB_NAME=sc_test`
- Restarted test backend runtime:
  - `make restart ENV=test DB_NAME=sc_test`
- Deployed frontend runtime for test verification:
  - `pnpm -C frontend/apps/web build`
  - started Vite test server with `VITE_API_PROXY_TARGET=http://localhost:8071`, `VITE_ODOO_DB=sc_test` on `http://127.0.0.1:5174`
- Prepared immediate real-user login verification conditions on `sc_test`:
  - disabled login cooldown (`base.login_cooldown_after=0`)
  - reset `smart_construction_custom` seeded users password to `demo`
  - reset admin password to `admin`

## Verification result
- Module state on `sc_test`: `smart_construction_custom=installed` (and chain installed).
- Frontend service check: `http://127.0.0.1:5174/` returns index HTML.
- Real-user login check (`/web/session/authenticate`, `db=sc_test`):
  - `admin/admin -> uid=2`
  - `chenshuai/demo -> uid=20`
  - `chentianyou/demo -> uid=10`
  - `duanyijun/demo -> uid=8`
  - `hujun/demo -> uid=24`
  - `jiangyijiao/demo -> uid=14`
  - `lidexue/demo -> uid=19`
  - `lijianfeng/demo -> uid=17`
  - `lilinxu/demo -> uid=12`

## Risk analysis
- Conclusion: `PASS`
- Low risk note: login cooldown was lowered for test verification convenience; keep test-only usage.

## Rollback suggestion
- Restart test stack to clear transient runtime state:
  - `make restart ENV=test DB_NAME=sc_test`
- If needed, restore previous user passwords manually from known baseline snapshot.

## Next suggestion
- You can now directly open `http://127.0.0.1:5174` and log in with seeded real users (`demo`) against `sc_test`.

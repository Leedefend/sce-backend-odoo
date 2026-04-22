# FE Nav Compat Tail Verify CV

## Goal

Verify the real menu click usability runtime after the frontend compatibility
tail cleanup on the requested custom frontend path.

## Verification

1. `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-20-FE-NAV-COMPAT-TAIL-VERIFY-CV.yaml`
   - PASS
2. `BASE_URL=http://127.0.0.1:5174 API_BASE_URL=http://127.0.0.1:8069 DB_NAME=sc_demo E2E_LOGIN=wutao E2E_PASSWORD=demo make verify.portal.unified_system_menu_click_usability_smoke.host`
   - FAIL
   - Artifact: `artifacts/codex/unified-system-menu-click-usability-smoke/20260420T075837Z/summary.json`
   - Frozen result:
     - `status=FAIL`
     - `used_api_base=http://127.0.0.1:8069`
     - `leaf_count=0`
     - `fail_count=0`
     - `error=no menu leaves discovered from runtime storage`

## Result

This verify batch failed before menu-leaf click assertions could execute.

The immediate blocker is no longer a specific degraded menu leaf; it is that
the runtime storage snapshot observed by the verifier did not expose any menu
leaf rows at all on the requested custom frontend path.

Per stop rule, this iteration line stops here on `verify_failed`.

# FE Nav Verifier Source Align CX

## Goal

Align the unified menu click usability smoke with the active navigation source
so the verifier no longer stops early when legacy session cache exposes no menu
leaves.

## Verification

1. `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-20-FE-NAV-VERIFIER-SOURCE-ALIGN-CX.yaml`
   - PASS
2. `node --check scripts/verify/unified_system_menu_click_usability_smoke.mjs`
   - PASS
3. `BASE_URL=http://127.0.0.1:5174 API_BASE_URL=http://127.0.0.1:8069 DB_NAME=sc_demo E2E_LOGIN=wutao E2E_PASSWORD=demo make verify.portal.unified_system_menu_click_usability_smoke.host`
   - FAIL
   - Artifact: `artifacts/codex/unified-system-menu-click-usability-smoke/20260420T080748Z/summary.json`
   - Frozen result:
     - `leaf_count=31`
     - `fail_count=26`
     - `nav_source=release_tree`
     - `error=menu click usability failures=26`
4. `git diff --check -- agent_ops/tasks/ITER-2026-04-20-FE-NAV-VERIFIER-SOURCE-ALIGN-CX.yaml docs/verify/fe_nav_verifier_source_align_cx_v1.md docs/ops/iterations/delivery_context_switch_log_v1.md scripts/verify/unified_system_menu_click_usability_smoke.mjs`
   - PASS

## Result

The verifier source-alignment patch succeeded in removing the previous
`leaf_count=0 / no menu leaves discovered from runtime storage` blocker.

This verify line still fails overall because the smoke now reaches the real
leaf-click stage and freezes 26 remaining menu failures. The next blocker is no
longer verifier source blindness; it is the actual menu contract/runtime gap on
those failing leaves.

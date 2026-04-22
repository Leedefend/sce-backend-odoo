# FE Nav Verifier Source Selection DD

## Goal

Make the unified menu click usability smoke prefer the active explained
navigation tree before cached release/menu trees.

## Verification

1. `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-20-FE-NAV-VERIFIER-SOURCE-SELECTION-DD.yaml`
   - PASS
2. `node --check scripts/verify/unified_system_menu_click_usability_smoke.mjs`
   - PASS
3. `BASE_URL=http://127.0.0.1:5174 API_BASE_URL=http://127.0.0.1:8069 DB_NAME=sc_demo E2E_LOGIN=wutao E2E_PASSWORD=demo make verify.portal.unified_system_menu_click_usability_smoke.host`
   - FAIL
   - Artifact: `artifacts/codex/unified-system-menu-click-usability-smoke/20260420T083057Z/summary.json`
   - Frozen result:
     - `nav_source=nav_explained.tree`
     - `leaf_count=60`
     - `fail_count=54`
     - common-entry leaves now fail with `Menu resolve failed / menu not found`
4. `git diff --check -- agent_ops/tasks/ITER-2026-04-20-FE-NAV-VERIFIER-SOURCE-SELECTION-DD.yaml docs/verify/fe_nav_verifier_source_selection_dd_v1.md docs/ops/iterations/delivery_context_switch_log_v1.md scripts/verify/unified_system_menu_click_usability_smoke.mjs`
   - PASS

## Result

The source-selection experiment conclusively changed verifier behavior:
`nav_source` switched from `release_tree` to `nav_explained.tree`.

This still fails overall and exposes a larger problem surface: the active
explained navigation tree contains many leaf nodes that `/m/:menuId` cannot
resolve at all, especially under the common-entry branch. Per stop rule, this
line stops on `verify_failed`.

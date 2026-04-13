# Delivery Package Index v1

## Core Decisions

- final_go_decision: `docs/ops/delivery_readiness_final_check_v1.md`
- formal_entry_review: `docs/ops/delivery_formal_entry_page_review_v2.md`
- freeze_baseline: `docs/ops/delivery_freeze_baseline_v1.md`

## Trial & Remediation

- trial_orchestration: `docs/ops/delivery_user_trial_orchestration_v1.md`
- trial_execution_log: `docs/ops/delivery_user_trial_execution_log_v1.md`
- trial_issue_board: `artifacts/delivery/user_trial_issue_board_v1.json`
- remediation_plan: `docs/ops/delivery_user_trial_remediation_plan_v1.md`
- remediation_1709: `artifacts/delivery/remediation_1709_summary.json`
- remediation_1710: `artifacts/delivery/remediation_1710_summary.json`

## Verification Entry

- governance_gate: `python3 scripts/verify/v2_app_governance_gate_audit.py --json`
- menu_smoke: `BASE_URL=http://127.0.0.1:5174 DB_NAME=sc_demo E2E_LOGIN=wutao E2E_PASSWORD=demo API_BASE_URL=http://127.0.0.1:8069 node scripts/verify/unified_system_menu_click_usability_smoke.mjs`
- final_check_audit: `python3 scripts/verify/delivery_readiness_final_check_audit.py`

## Latest Smoke Evidence

- latest_smoke_summary: `artifacts/codex/unified-system-menu-click-usability-smoke/20260411T210022Z/summary.json`

## Handover Note

- 本索引作为交付包总入口，后续若有新增批次，请同步更新到 `v2` 索引版本。

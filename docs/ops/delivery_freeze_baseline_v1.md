# Delivery Freeze Baseline v1

## Freeze Scope

- freeze_version: `v1`
- freeze_mode: `delivery_pre_handover`
- baseline_branch: `codex/next-round`
- baseline_commit: `0049675`

## Frozen Evidence

- menu_user_snapshot: `artifacts/menu/delivery_user_navigation_v1.json`
- menu_admin_snapshot: `artifacts/menu/delivery_admin_navigation_v1.json`
- menu_convergence_diff: `artifacts/menu/menu_convergence_diff_v1.json`
- formal_entry_review: `docs/ops/delivery_formal_entry_page_review_v2.md`
- latest_menu_smoke: `artifacts/codex/unified-system-menu-click-usability-smoke/20260411T181557Z/summary.json`

## Frozen Decisions

- delivery_decision: `GO`
- focus_intents_status: `session.bootstrap/meta.describe_model/ui.contract => v2_primary ready`
- menu_299_return_path: `closed`
- watchpoint_count: `0`

## Acceptance Snapshot

- v2_governance_gate: `PASS (27/27)`
- unified_menu_smoke: `PASS (leaf_count=28, fail_count=0)`
- formal_entry_review_refinement: `PASS`
- menu_299_return_path_smoke: `PASS`

## Handover Notes

- 当前冻结基线用于交付前验收与试用，后续改动需新建批次并更新冻结版本。
- 若需回滚到冻结基线，请以本文件引用的快照与报告为准执行文件级回滚。

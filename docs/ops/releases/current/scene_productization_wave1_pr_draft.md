# PR Draft · Scene Productization Wave1

## Title

`feat(scene): complete wave1 productization to full R3 coverage`

## Summary

- 完成场景成熟度治理闭环：Inventory + Coverage Dashboard + Freeze Guard。
- 完成主线场景产品化：从 `R0/R1` 分层推进到 `R2/R3`。
- 完成 Wave1 收口：当前 inventory 中 13 个场景全部达到 `R3`。

## Architecture Impact

- 新增能力集中在 **Scene Layer / Page Orchestration Layer**，未引入跨层调用。
- 通过 `scene_inventory_freeze_guard` 固化“新增 scene 必须先入 inventory”的治理规则。
- 保持平台层与行业层边界：行业模块仅提供场景事实与产品化配置，不改平台核心治理链路。

## Layer Target

- `Scene Layer`
- `Page Orchestration Layer`

## Affected Modules

- `addons/smart_construction_scene`
- `scripts/verify`
- `docs/ops`
- `Makefile`

## Key Changes

- 场景产品化内容升级（`page / zone_blocks / action_specs / role_variants / data_sources / product_policy`）：
  - `projects.intake`
  - `projects.list`
  - `project.management`
  - `projects.ledger`
  - `contract.center`
  - `contracts.workspace`
  - `cost.cost_compare`
  - `cost.project_cost_ledger`
  - `cost.analysis`
  - `finance.center`
  - `finance.workspace`
  - `finance.payment_requests`
  - `finance.settlement_orders`
- 新增守护脚本：
  - `scripts/verify/scene_maturity_guard.py`
  - `scripts/verify/scene_coverage_dashboard_report.py`
  - `scripts/verify/scene_inventory_freeze_guard.py`
- 新增基线：
  - `scripts/verify/baselines/scene_inventory_freeze_guard_exemptions.json`
- 新增 Make 入口：
  - `verify.scene.maturity.guard`
  - `verify.scene.coverage.dashboard`
  - `verify.scene.inventory.freeze.guard`

## Validation

- `python3 scripts/verify/scene_maturity_guard.py`
- `python3 scripts/verify/scene_coverage_dashboard_report.py`
- `python3 scripts/verify/scene_inventory_freeze_guard.py`
- `python3 scripts/verify/scene_definition_semantics_guard.py`
- `make verify.scene.coverage.dashboard`
- `make verify.scene.inventory.freeze.guard`

## Acceptance Snapshot

- 覆盖看板：`docs/ops/audit/scene_coverage_dashboard.md`
- 当前结果：`R3=13/13`，`R2+=13/13`，`R1=0`。

## Commits (Wave1)

- `4b992f7` bootstrap inventory/guard
- `9304a65` day3-day7 productization + freeze
- `61be1e4` finalize wave targets
- `d136e0a` clear remaining `R1`
- `c4b19d2` deepen `R3`
- `2a18c5e` promote remaining scenes to `R3`


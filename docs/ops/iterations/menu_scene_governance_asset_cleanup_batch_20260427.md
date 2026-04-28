# Menu Scene Governance Asset Cleanup Batch 20260427

## 1. 本轮变更
- 目标：清理 scene-governance CSV 资产中 demo showcase 与 canonical `projects.list` 的过期映射。
- 完成：
  - 从 baseline mapping 删除 `smart_construction_demo.menu_sc_project_list_showcase -> projects.list`。
  - 从 baseline mapping 删除 `smart_construction_demo.action_sc_project_list_showcase -> projects.list`。
  - 从 generated current mapping 删除同两条过期映射。
- 未完成：未重建缺失的 `scene_governance_asset_export.py`，本轮只修复已入库治理资产。

## 2. 影响范围
- 模块：`docs/architecture/scene-governance/assets`、`docs/ops/iterations`
- 启动链：否
- contract/schema：否
- default_route：否
- Odoo 运行时代码：否

## 3. 风险
- P0：无，未改运行时代码。
- P1：若后续恢复自动导出脚本，必须确保导出源遵守 dual-track owner-signal 规则，否则 generated CSV 可能再次回退。
- P2：baseline 文件已按当前架构口径修正，不再保留旧 demo showcase 误映射作为基线事实。

## 4. 验证
- `rg -n "smart_construction_demo\\.(menu_sc_project_list_showcase|action_sc_project_list_showcase).*projects\\.list|projects\\.list.*smart_construction_demo\\.(menu_sc_project_list_showcase|action_sc_project_list_showcase)|menu_sc_project_list_showcase,.*projects\\.list|action_sc_project_list_showcase,projects\\.list" docs/architecture/scene-governance/assets -S`：PASS（无输出）
- `git diff --check -- docs/architecture/scene-governance/assets/menu_scene_mapping_baseline_v1.csv docs/architecture/scene-governance/assets/generated/menu_scene_mapping_current_v1.csv docs/ops/iterations/menu_scene_governance_asset_cleanup_batch_20260427.md docs/ops/iterations/delivery_context_switch_log_v1.md`：PASS

## 5. 产物
- updated assets：
  - `docs/architecture/scene-governance/assets/menu_scene_mapping_baseline_v1.csv`
  - `docs/architecture/scene-governance/assets/generated/menu_scene_mapping_current_v1.csv`
- docs：`docs/ops/iterations/menu_scene_governance_asset_cleanup_batch_20260427.md`

## 6. 回滚
- 方法：回退本批次提交，或恢复两份 CSV 中删除的两条 demo showcase 映射。
- 数据/升级：无需 `-u`，无需重启。

## 7. 下一批次
- 目标：继续扫描 contract snapshots 与历史验证文档，区分可再生快照和历史记录，避免把历史记录误当当前规范残留。
- 前置条件：不改历史审计记录，除非它被当前验证或生成资产消费。

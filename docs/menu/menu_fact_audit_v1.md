# Menu Fact Audit v1

## Scope
- Data source: `artifacts/menu/menu_fact_snapshot_v1.json`
- Audit output: `artifacts/menu/menu_fact_anomalies_v1.json`
- Layer boundary: facts-only (`ir.ui.menu` + raw action binding), no route/scene/delivery interpretation.

## Summary
- 菜单总数：0
- 目录菜单数：0
- action 菜单数：0
- 异常菜单数：0

## Anomaly Categories
- `orphan_menus`: `parent_id` 指向不存在的菜单
- `empty_menus`: 无 `action_raw` 且无 `child_ids`
- `invalid_action_menus`: `action_raw` 存在但解析失败/动作不存在/模型不支持
- `mixed_menus`: 既有 `action_raw` 又有 `child_ids`
- `sequence_risk.missing_or_invalid`: sequence 缺失或非法
- `sequence_risk.duplicate`: 同级 sequence 重复

## Notes
- 当前仓库快照为占位快照（无运行态数据）。
- 在 Odoo 运行时执行：
  - `python3 scripts/verify/menu_fact_export.py --db <db>`
  - `python3 scripts/verify/menu_fact_anomaly_audit.py --snapshot artifacts/menu/menu_fact_snapshot_v1.json --output artifacts/menu/menu_fact_anomalies_v1.json`
  以生成真实审计结果。

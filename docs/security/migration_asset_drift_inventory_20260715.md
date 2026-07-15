# 迁移资产静态漂移盘点（2026-07-15）

## 边界

本报告在代码基线 `5c41a434c` 上静态生成；未连接旧系统、未访问数据库、未执行 replay、未刷新锁文件，也未生成历史业务基线。

## 221 步调用链

`scripts/migration/history_continuity_oneclick.sh` SHA256：

```text
980daf94887576ace80744ac221ad723b25eaf2db17f295358fb2fd0d2c64bfa
```

| 分类 | 数量 |
| --- | ---: |
| adapter | 69 |
| baseline replay | 62 |
| formal projection | 42 |
| repair/normalization | 23 |
| probe/guard | 20 |
| special | 5 |
| 合计 | 221 |

静态发现 127 个写脚本。105 个直接出现既有稳定来源键词汇；以下 22 个未直接体现这些键，必须在任何在线增量或循环 replay 前逐项人工确认，不能据此直接断言其不幂等：

```text
fresh_db_legacy_personnel_movement_replay_write.py
fresh_db_partner_l4_replay_write.py
fresh_db_legacy_file_index_replay_write.py
contract_12_row_missing_partner_anchor_write.py
history_partner_master_targeted_replay_write.py
history_partner_master_direction_defer_replay_write.py
history_supplier_partner_targeted_replay_write.py
history_receipt_partner_targeted_replay_write.py
visible_surface_receipt_core_creator_normalize_write.py
visible_surface_receipt_request_scope_normalize_write.py
visible_surface_receipt_invoice_line_normalize_write.py
history_outflow_partner_targeted_replay_write.py
history_actual_outflow_partner_targeted_replay_write.py
visible_surface_payment_request_contract_normalize_write.py
history_receipt_income_partner_targeted_replay_write.py
history_expense_deposit_partner_targeted_replay_write.py
history_payment_request_outflow_state_activation_write.py
fresh_db_payment_execution_taxonomy_projection_write.py
visible_surface_project_contract_enrichment_write.py
project_migration_field_continuity_backfill_write.py
fresh_db_labor_equipment_projection_write.py
fresh_db_work_breakdown_projection_write.py
```

静态字符串扫描还发现 42 个脚本包含 `unlink`、SQL `DELETE`、清理或重建相关语义。多数正式投影可能仅清理由自身拥有的投影行，部分匹配也可能来自 rollback 代码；因此它们属于“隔离库审计候选”，不能作为本任务的删除结论，也不得在在线采集阶段执行。

## 锁与物化漂移

当前发布包锁：

- package：`migration_assets_release_20260618T104314Z`
- SHA256：`b8ba1f85cf084679655015b8d5f763b47c8d7c964e1e9920ca2f3fb1e76b84f0`
- size：634,798,244 bytes
- included files：3,723
- `package_path`：空
- `sha256_path`：空
- 当前仓库未物化该 tar 包。

当前工作树 `migration_assets/` 有 99 个文件、490,713,632 bytes。`scbs55_replay_payload_gap_report_v1.json` 记录 221 步且状态为 `PASS_WITH_GAPS`；`scbs55_full_migration_asset_freeze_v1.json` 仍为 `topic_in_progress`。

只读执行 `make migration.assets.full_scope_guard` 返回 FAIL，共 13 项：

1. freeze package ID 与 lock 漂移；
2. package SHA256 漂移；
3. package size 漂移；
4. materializes 描述漂移；
5. lock 未满足双目录物化断言；
6. audit/manifest asset file count 漂移；
7. unreferenced file count 漂移；
8. total asset size 漂移；
9. replay steps 221/219 漂移；
10. baseline exclusion count 漂移；
11. delivery required count 漂移；
12. release required count 漂移；
13. delivery required artifact set 漂移。

## 正式资产与 live-delta 边界

`scripts/migration/scbs55_live_delta_backfill_write.py` 仍被正式 inventory 标记为 `reference_only_not_delivery_asset`，原因是它不受完整迁移包锁与 evidence manifest 约束。它没有 watermark/checkpoint，不能作为连续在线同步入口。

## 结论

```text
MIGRATION_ASSET_DRIFT_INVENTORIED=true
MIGRATION_ASSET_LOCK_REFRESHED=false
REPLAY_EXECUTED=false
HISTORICAL_BASELINE_CREATED=false
```

English: [migration_asset_drift_inventory_20260715.en.md](migration_asset_drift_inventory_20260715.en.md)

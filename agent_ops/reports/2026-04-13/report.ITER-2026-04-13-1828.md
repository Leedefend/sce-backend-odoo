# ITER-2026-04-13-1828 项目骨架回滚 dry-run 脚本专项

## 任务结论

- 结果：PASS_WITH_EXPANSION_BLOCKED
- 层级：Migration Dry-Run Tooling
- 模块：project.project rollback dry-run and stage default diagnosis
- 范围：实现并执行只读 rollback dry-run；未删除、未写入、未扩样。

## 修改文件

- `agent_ops/tasks/ITER-2026-04-13-1828.yaml`
- `scripts/migration/project_rollback_dry_run.py`
- `artifacts/migration/project_rollback_dry_run_result_v1.json`
- `docs/migration_alignment/project_rollback_dry_run_report_v1.md`
- `docs/migration_alignment/project_stage_default_behavior_review_v1.md`
- `docs/migration_alignment/project_write_trial_next_gate_v1.md`
- `agent_ops/reports/2026-04-13/report.ITER-2026-04-13-1828.md`
- `agent_ops/state/task_results/ITER-2026-04-13-1828.json`
- `docs/ops/iterations/delivery_context_switch_log_v1.md`

## Rollback Dry-Run 结果

- status：`ROLLBACK_READY`
- total_targets：30
- matched_rows：30
- missing_rows：0
- duplicate_matches：0
- out_of_scope_matches：0
- rollback_key：`legacy_project_id`

结论：如果按 30 个 `legacy_project_id` 回滚，可以精确锁定本批写入试导记录。

## Stage 默认行为诊断

- stage_id_all_same：true
- stage_id：5
- stage_name：`筹备中`
- count：30

结论：30 条记录全部落到同一个默认阶段 `筹备中`。该行为可作为 create-only 项目骨架默认阶段的候选，但扩样前必须人工确认业务可接受；如果不可接受，应在下一轮 stage policy gate 中处理。

## GO / NO-GO

- 真实回滚：技术上可执行，但本批未授权真实删除；仍需单独高风险删除授权批次。
- 扩大样本：当前不允许；先确认默认 `stage_id` 策略。
- update/upsert：NO-GO。
- 全量导入：NO-GO。

## 验证结果

- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-13-1828.yaml`：PASS
- `python3 -m py_compile scripts/migration/project_rollback_dry_run.py`：PASS
- rollback dry-run 静态检查：PASS，脚本不包含 `unlink/write/create/commit`
- `ENV=dev DB_NAME=sc_demo make odoo.shell.exec`：PASS
- `python3 -m json.tool artifacts/migration/project_rollback_dry_run_result_v1.json`：PASS
- `python3 -m json.tool agent_ops/state/task_results/ITER-2026-04-13-1828.json`：PASS
- `make verify.native.business_fact.static`：PASS

## 下一轮建议

下一轮建议执行“项目默认阶段策略确认专项 v1”。如果确认 `筹备中` 可作为骨架默认阶段，则进入 bounded create-only 扩样门禁；如果不接受，则先定义 safe import 的 stage policy，不做扩样。

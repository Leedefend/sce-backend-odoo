# ITER-2026-04-13-1827 项目骨架写后复核与回滚演练专项

## 任务结论

- 结果：PASS_WITH_EXPANSION_BLOCKED
- 层级：Migration Governance Documentation
- 模块：project.project post-write review and rollback rehearsal planning
- 范围：只读核验与回滚方案设计；未新增写入，未执行删除，未扩大样本。

## 修改文件

- `agent_ops/tasks/ITER-2026-04-13-1827.yaml`
- `docs/migration_alignment/project_post_write_manual_review_checklist_v1.md`
- `docs/migration_alignment/project_post_write_readonly_review_v1.md`
- `docs/migration_alignment/project_write_trial_rollback_target_v1.md`
- `docs/migration_alignment/project_write_trial_rollback_plan_v1.md`
- `docs/migration_alignment/project_write_trial_rollback_script_design_v1.md`
- `docs/migration_alignment/project_write_trial_expand_gate_v1.md`
- `artifacts/migration/project_post_write_readonly_review_v1.json`
- `agent_ops/reports/2026-04-13/report.ITER-2026-04-13-1827.md`
- `agent_ops/state/task_results/ITER-2026-04-13-1827.json`
- `docs/ops/iterations/delivery_context_switch_log_v1.md`

## 只读复核结果

- target database：`sc_demo`
- sample rows：30
- records found：30
- unique identities found：30
- missing identities：0
- duplicate identities：0
- empty names：0
- rows with default `stage_id` warning：30

`stage_id` 是 Odoo/project 创建时默认产生的关系值，不是 1825 写入脚本显式写入的 safe-slice 字段。扩样前必须人工确认该默认行为可接受，或在后续写入门禁中明确处理。

## 回滚对象锁定

回滚对象清晰：30 条记录均可按 `legacy_project_id` 精确锁定，Odoo ID 范围为 2107-2136。

回滚选择器只能使用 30 个 `legacy_project_id`，不得按项目名称、公司文本、`other_system_id`、`other_system_code` 或 legacy `PROJECT_CODE` 删除。

## 回滚方案

回滚方案可执行，但必须另开显式删除授权批次。后续脚本必须先 dry-run，证明目标数恰好 30、无缺失、无重复、无越界记录，才能进入 delete 模式。

本批没有执行真实删除。

## 扩样结论

当前不允许扩大下一批 create-only 样本。扩样前必须完成：

- 人工复核 30 条记录可用性；
- 接受或处理默认 `stage_id`；
- 设计并执行 no-delete rollback dry-run；
- 新建 bounded create-only 样本扩展任务契约。

## 验证结果

- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-13-1827.yaml`：PASS
- `ENV=dev DB_NAME=sc_demo make odoo.shell.exec`：PASS，只读复核
- `python3 -m json.tool artifacts/migration/project_post_write_readonly_review_v1.json`：PASS
- `python3 -m json.tool agent_ops/state/task_results/ITER-2026-04-13-1827.json`：PASS
- `make verify.native.business_fact.static`：PASS

## 下一轮建议

下一轮建议执行“项目骨架回滚 dry-run 脚本专项 v1”：只实现 dry-run，不删除，输出 30 条 rollback target 的可删除性诊断。该批通过后再决定是否需要真实回滚或扩样。

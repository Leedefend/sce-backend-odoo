# ITER-2026-04-13-1829 项目状态体系治理专项

## 任务结论

- 结果：PASS
- 层级：Business Fact Governance Documentation
- 模块：project.project state system governance
- 范围：documentation-only；未写代码，未改模型，未改导入逻辑，未扩样。

## 修改文件

- `agent_ops/tasks/ITER-2026-04-13-1829.yaml`
- `docs/architecture/project_state_system_inventory_v1.md`
- `docs/architecture/project_state_role_definition_v1.md`
- `docs/architecture/project_state_mapping_v1.md`
- `docs/architecture/project_state_write_policy_v1.md`
- `docs/architecture/project_state_control_policy_v1.md`
- `docs/migration_alignment/project_stage_policy_final_v1.md`
- `docs/architecture/project_state_governance_decision_v1.md`
- `agent_ops/reports/2026-04-13/report.ITER-2026-04-13-1829.md`
- `agent_ops/state/task_results/ITER-2026-04-13-1829.json`
- `docs/ops/iterations/delivery_context_switch_log_v1.md`

## 核心决策

```text
lifecycle_state = 主状态 / business truth
stage_id = 从状态 / Odoo UI stage projection
```

状态同步方向：

```text
lifecycle_state -> stage_id
stage_id -/-> lifecycle_state
```

## 状态映射

| lifecycle_state | Stage |
| --- | --- |
| `draft` | 筹备中 |
| `in_progress` | 在建 |
| `paused` | 停工 |
| `done` | 竣工 |
| `closing` | 结算中 |
| `warranty` | 保修期 |
| `closed` | 关闭 |

## 导入策略

导入时写 normalized `lifecycle_state`，再映射 `stage_id`。在生命周期转换规则未获批前，create-only 骨架导入可继续依赖默认：

```text
lifecycle_state=draft
stage_id=筹备中
```

`CONTRACT_STATUS/QYZT -> 已签约` 在当前 v1 中不能落为独立 runtime 状态，因为代码尚无 `signed` lifecycle 或 `待启动` stage；如业务要求，需要另开状态扩展门禁。

## 当前实现差异

当前代码已体现 lifecycle -> stage 同步，也已用 `lifecycle_state` 替换原生表单 header 的 `stage_id` statusbar。当前代码还存在 stage-only write 的业务信号防越级逻辑；本批不改代码，只把目标治理方向固化为 stage 不反向修改 lifecycle。

## 验证结果

- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-13-1829.yaml`：PASS
- `python3 -m json.tool agent_ops/state/task_results/ITER-2026-04-13-1829.json`：PASS
- `make verify.native.business_fact.static`：PASS

## 下一轮建议

下一轮建议执行“项目状态实现对齐审计专项 v1”：只读审计现有代码是否完全符合 `lifecycle_state -> stage_id` 单向治理，列出是否需要移除或收紧 stage-only 逻辑，但仍不直接改代码。

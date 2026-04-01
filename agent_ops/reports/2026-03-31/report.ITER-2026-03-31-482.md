# ITER-2026-03-31-482

## Summary
- 收口了 `481` 发现的 next-action expression 规范化残差
- `condition_expr` 现在会先去缩进、去空行并折叠成单行，再进入 `safe_eval`
- 结论为 `PASS`

## Scope
- 实现修复：
  - `sc.project.next_action.service` expression normalization
- 回归覆盖：
  - multiline `condition_expr` evaluation

## Changed Files
- [project_next_action_service.py](/mnt/e/sc-backend-odoo/addons/smart_construction_core/services/project_next_action_service.py)
- [test_project_object_button_runtime_backend.py](/mnt/e/sc-backend-odoo/addons/smart_construction_core/tests/test_project_object_button_runtime_backend.py)

## Implementation Facts
- [project_next_action_service.py](/mnt/e/sc-backend-odoo/addons/smart_construction_core/services/project_next_action_service.py#L27)
  - 新增 `_normalize_expr()`
  - 处理顺序为：
    - `textwrap.dedent`
    - `strip`
    - 按行裁剪空白
    - 折叠为单行表达式
- [project_next_action_service.py](/mnt/e/sc-backend-odoo/addons/smart_construction_core/services/project_next_action_service.py#L27)
  - `get_next_actions()` 在 `_is_expr_safe` 和 `safe_eval` 之前统一使用规范化后的表达式
- [test_project_object_button_runtime_backend.py](/mnt/e/sc-backend-odoo/addons/smart_construction_core/tests/test_project_object_button_runtime_backend.py#L128)
  - 新增 multiline `condition_expr` regression，确保 draft 项目可重新拿到 `action_sc_submit`

## Verification
- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-03-31-482.yaml` → `PASS`
- `make verify.smart_core` → `PASS`
- `make mod.upgrade CODEX_NEED_UPGRADE=1 MODULE=smart_construction_core DB_NAME=sc_odoo` → `PASS`
- `sc_odoo` runtime audit → `PASS`
  - `draft / project.id = 1`
  - `PM / hujun` next-actions 中重新出现：
    - `action_sc_submit`
    - 执行成功，返回 `bool`
  - 不再出现 `rule=1 eval failed` 的 expression 解析告警

## Conclusion
- `draft` 阶段的提交立项推荐已恢复
- `482` 修复的是表达式规范化，不改变原有规则语义，也不触碰 ACL
- 目前 next-action 在“规则评估 -> dispatcher 执行”链路上的已知残差已进一步收口

## Risk
- 结果：`PASS`
- 残余风险：
  - 后续仍应继续审计 role-specific recommendation 稳定性，避免执行副作用影响同批次角色观察
  - 其他未覆盖的复杂表达式若含更特殊语法，仍需后续抽样

## Rollback
- `git restore addons/smart_construction_core/services/project_next_action_service.py`
- `git restore addons/smart_construction_core/tests/test_project_object_button_runtime_backend.py`
- `git restore agent_ops/tasks/ITER-2026-03-31-482.yaml`
- `git restore agent_ops/reports/2026-03-31/report.ITER-2026-03-31-482.md`
- `git restore agent_ops/state/task_results/ITER-2026-03-31-482.json`
- `git restore docs/ops/iterations/delivery_context_switch_log_v1.md`

## Next
- 继续开低风险审计批次，检查 role-specific next-action recommendation 是否在无执行副作用干扰的情况下保持稳定一致

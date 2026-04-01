# ITER-2026-04-01-507

## Summary
- 执行了 `tender` 查询面 / 执行面拆分的高风险治理批次
- 结论为 `FAIL`
- 仓库实现已落地，但 runtime 复核触发真实 stop condition：`project_read` 样本仍然表现为 tender 可写，未收口为只读查询面

## Scope
- 本批变更：
  - [ir.model.access.csv](/mnt/e/sc-backend-odoo/addons/smart_construction_core/security/ir.model.access.csv)
  - [tender_views.xml](/mnt/e/sc-backend-odoo/addons/smart_construction_core/views/support/tender_views.xml)
  - [test_tender_read_surface_backend.py](/mnt/e/sc-backend-odoo/addons/smart_construction_core/tests/test_tender_read_surface_backend.py)
  - [test_acl_matrix_gate.py](/mnt/e/sc-backend-odoo/addons/smart_construction_core/tests/test_acl_matrix_gate.py)

## Intended implementation
- 给 `tender.bid` 及其子模型补 `group_sc_cap_project_read` 的只读 ACL
- 保留 `project_user / project_manager` 的 tender 写能力
- 在 [tender_views.xml](/mnt/e/sc-backend-odoo/addons/smart_construction_core/views/support/tender_views.xml)
  中把状态栏点击流转收回到执行角色，纯只读角色只展示不可点击状态

## Verification
- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-01-507.yaml` → `PASS`
- `make verify.smart_core` → `PASS`
- `make mod.upgrade CODEX_NEED_UPGRADE=1 MODULE=smart_construction_core DB_NAME=sc_odoo` → `PASS`
- runtime audit on `sc_odoo` → `FAIL`

## Runtime facts
- `action_tender_bid` 仍可成功打开，`res_model = tender.bid`
- 但 runtime 样本结果为：
  - `project_read` 样本用户：`read = True`, `create = True`, `write = True`, `unlink = False`
  - `project_manager` 样本用户：`read = True`, `create = True`, `write = True`, `unlink = False`
- 也就是说，本批目标中的“`project_read` 仅只读查询”并未成立
- 同时 view 复核也未达到预期：
  - 只读样本仍看到 `clickable` 状态栏
  - 未看到预期的 `readonly` 状态栏分支

## Conclusion
- 这是高风险批次的真实失败，不是样本不足
- 当前仓库改动还没有把 tender 收口成“查询面只读、执行面可写”
- 更关键的是，runtime 已暴露出 implied groups / 实际权限面与预期不一致的问题
- 根据仓库 stop 规则，此时必须停止，不能继续在当前链路里追加第二轮权限改动

## Risk
- 结果：`FAIL`
- 风险点：
  - `project_read` 当前仍然拿到 tender 写能力，存在权限泄漏风险
  - 继续自动迭代会在未厘清 group 继承 / 实际角色承载的前提下扩大 ACL 变更面
  - 这已经触发高风险批次的强制停机条件

## Rollback
- 如需撤回本批实现：
  - `git restore addons/smart_construction_core/security/ir.model.access.csv`
  - `git restore addons/smart_construction_core/views/support/tender_views.xml`
  - `git restore addons/smart_construction_core/tests/test_tender_read_surface_backend.py`
  - `git restore addons/smart_construction_core/tests/test_acl_matrix_gate.py`
  - `git restore agent_ops/tasks/ITER-2026-04-01-507.yaml`
  - `git restore agent_ops/reports/2026-04-01/report.ITER-2026-04-01-507.md`
  - `git restore agent_ops/state/task_results/ITER-2026-04-01-507.json`
  - `git restore docs/ops/iterations/delivery_context_switch_log_v1.md`

## Next
- 当前链路必须停止
- 下一步只能新开一张更窄的高风险审计批次，先查清：
  - `group_sc_cap_project_read` 是否通过 implied groups / role overlay 实际带上了 `project_user`
  - 为什么只读样本在 view 上仍命中了 clickable statusbar 分支

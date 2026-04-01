# ITER-2026-03-31-488

## Summary
- 对 `487` 暴露的样本覆盖缺口做了 recipe 审计
- 结论为 `PASS_WITH_RISK`
- 这批没有执行 runtime 造样，而是把三条未覆盖 recommendation 分支的最小造样路径和风险边界收清了

## Scope
- 本批为 audit-only
- 不改代码、不改 seed、不改 runtime 数据
- 仅审计：
  - `payment.request` / `project.task` / `project.project` 的最小创建与状态推进路径
  - 现有测试里的最小夹具
  - 当前 runtime 为什么缺样本，以及是否存在低副作用造样方案

## Verification
- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-03-31-488.yaml` → `PASS`
- repository and runtime audit → `PASS_WITH_RISK`

## Repository facts
- `处理待审批付款`
  - 规则条件：`payment.pending > 0`
  - [payment_request.py](/mnt/e/sc-backend-odoo/addons/smart_construction_core/models/core/payment_request.py)
    显示 pending 统计来自 `state in ['submit', 'approve', 'approved']`
  - 最小创建字段从 [test_payment_request_action_surface_backend.py](/mnt/e/sc-backend-odoo/addons/smart_construction_core/tests/test_payment_request_action_surface_backend.py) 可收敛为：
    - `project_id`
    - `partner_id`
    - `amount`
    - `type`
  - 但要稳定进入 pending 状态，真实 `action_submit()` 还会触发：
    - funding gate
    - settlement consistency
    - validator
    - tier validation
  - 仓库里存在 `with_context(allow_transition=True).write({'state': 'submit'})` 这种测试/内部路径，但它属于绕过业务前置校验的受控状态写
- `推进任务执行`
  - 规则条件：`task.in_progress > 0`
  - [task_extend.py](/mnt/e/sc-backend-odoo/addons/smart_construction_core/models/support/task_extend.py)
    显示可通过：
    - 创建 `project.task(name, project_id, user_ids)`
    - `action_prepare_task()`
    - `action_start_task()`
    进入 `sc_state = in_progress`
  - [test_project_plan_bootstrap_backend.py](/mnt/e/sc-backend-odoo/addons/smart_construction_core/tests/test_project_plan_bootstrap_backend.py)
    证明这条任务推进路径在测试里是可用的
- `创建任务`
  - 规则条件：`task.count == 0 and task.in_progress == 0`
  - 需要一个 `lifecycle_state = in_progress` 且无任务的项目
  - [project_core.py](/mnt/e/sc-backend-odoo/addons/smart_construction_core/models/core/project_core.py)
    显示正式状态推进需要 `owner_id / location / manager_id or user_id`
  - 仓库测试里既有直接创建 `lifecycle_state = in_progress` 的项目，也有
    `action_set_lifecycle_state('in_progress')` 的正式推进路径

## Classification
- `处理待审批付款`
  - 有最小 recipe，但想在当前 runtime 低副作用、确定性地命中这条分支，最现实的路径是受控状态写或补齐一整套资金/校验前置
  - 前者会绕过业务校验，后者 blast radius 明显扩大
  - 结论：当前不能把它归类为低风险 runtime 造样
- `推进任务执行`
  - 存在相对清晰的 scratch 造样路径：
    - scratch `project.project`
    - scratch `project.task`
    - `action_prepare_task()`
    - `action_start_task()`
  - 结论：这条分支存在可控 recipe
- `创建任务`
  - 也存在相对清晰的 scratch 造样路径：
    - scratch `project.project`
    - 进入 `in_progress`
    - 保持零任务
  - 结论：这条分支存在可控 recipe

## Conclusion
- 当前真正卡住连续验收的不是三条分支都没有方案，而是 `pending payment` 分支没有低风险、低副作用的 runtime 造样路径
- 任务相关的两条分支可以通过 scratch 项目/任务样本覆盖
- 付款 pending 分支如果要继续，就必须进入显式高风险批次：
  - 要么接受受控状态写作为验收样本手段
  - 要么补齐完整资金/校验前置，做更重的真实业务样本

## Risk
- 结果：`PASS_WITH_RISK`
- 风险点：
  - `pending payment` 分支的受控造样会触碰业务状态语义，不适合在没有单独高风险授权与回滚方案时自动推进
  - 如果盲目继续 runtime 造样，容易把 recommendation 验收问题升级成支付业务样本污染问题

## Rollback
- 本批为只读审计，无实现代码变更需要回滚
- 如需撤回治理文件：
  - `git restore agent_ops/tasks/ITER-2026-03-31-488.yaml`
  - `git restore agent_ops/reports/2026-03-31/report.ITER-2026-03-31-488.md`
  - `git restore agent_ops/state/task_results/ITER-2026-03-31-488.json`
  - `git restore docs/ops/iterations/delivery_context_switch_log_v1.md`

## Next
- 不能继续自动推进
- 下一步必须新开一张显式高风险批次，且只能二选一：
  - `A`：只为 `task in progress / create task` 两条分支补 scratch runtime 样本，暂时把 `pending payment` 留作未验收
  - `B`：专门为 `pending payment` 设计受控验收样本与回滚策略，再继续全链路 recommendation correctness 验收

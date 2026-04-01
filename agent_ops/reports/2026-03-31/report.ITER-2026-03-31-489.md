# ITER-2026-03-31-489

## Summary
- 在用户显式选择高风险路线后，先收口 `pending payment` 分支的受控验收样本策略
- 结论为 `PASS`
- 本批没有执行 runtime mutation，而是把单一 scratch 样本的创建、验证、清理边界具体化了

## Scope
- 本批为 strategy-only
- 不改代码、不改 seed、不改 runtime 数据
- 只定义：
  - scratch sample 的最小对象集合
  - sample marker
  - verification query
  - cleanup target

## Verification
- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-03-31-489.yaml` → `PASS`
- repository audit on model/test behavior → `PASS`

## Strategy
- 目标分支：
  - `in_progress` 项目上的 `payment.pending > 0`
  - recommendation 期望命中：`处理待审批付款`
- 单一 scratch sample 边界：
  - 1 个 scratch `project.project`
    - 最小要求：`name / owner_id / location / manager_id or user_id`
    - 进入 `lifecycle_state = in_progress`
  - 1 个 scratch `res.partner`
  - 1 条 scratch `payment.request`
    - 最小创建字段可收敛为：
      - `name`
      - `type = pay`
      - `project_id`
      - `partner_id`
      - `amount`
    - sample marker：
      - `name = CODEx-PENDING-SAMPLE-<timestamp>`
      - `note = ITER-2026-03-31-489`
- 受控状态策略：
  - 不走完整 finance 提交流程
  - 采用单点受控状态写，将 sample request 推到 `state = submit`
  - 这样只为 recommendation acceptance 提供 `payment.pending > 0` 事实，不扩散到真实审批/台账执行链
- verification：
  - 对 scratch project 调用：
    - `sc.project.overview.service.get_overview([project.id])`
    - `project.sc_get_next_actions(limit=5)`
  - 期望：
    - `payment.pending >= 1`
    - `actions` 含 `处理待审批付款`
- cleanup：
  - 删除 scratch `payment.request`
  - 删除 `source_model = 'payment.request'` 且 `source_id = scratch_payment_id` 的 `sc.business.evidence`
    - 需 `allow_evidence_mutation=True`
  - 删除 scratch `project.project`
  - 删除 scratch `res.partner`

## Repository facts supporting the strategy
- [payment_request.py](/mnt/e/sc-backend-odoo/addons/smart_construction_core/models/core/payment_request.py)
  - `pending` 统计口径就是 `state in ['submit', 'approve', 'approved']`
  - `create()` 会自动生成 payment evidence
- [test_payment_request_action_surface_backend.py](/mnt/e/sc-backend-odoo/addons/smart_construction_core/tests/test_payment_request_action_surface_backend.py)
  - 提供了 `payment.request` 最小创建字段样式
- [project_core.py](/mnt/e/sc-backend-odoo/addons/smart_construction_core/models/core/project_core.py)
  - 给出了项目进入 `in_progress` 的正式字段前提
- [business_evidence.py](/mnt/e/sc-backend-odoo/addons/smart_construction_core/models/support/business_evidence.py)
  - 证明 evidence 删除必须显式带 `allow_evidence_mutation`

## Conclusion
- `pending payment` 分支现在已经有一条具体、可执行、可回滚的验收样本策略
- 它仍然属于高风险，因为核心手段是受控状态写，不是完整财务业务流
- 但 blast radius 已被压缩到单一 scratch project + scratch payment.request + evidence cleanup

## Risk
- 结果：`PASS`
- 剩余风险：
  - 下一步 actual runtime mutation 批次仍然是高风险执行，不应与普通低风险 audit 混用
  - cleanup 必须同批完成，不能留下 scratch `payment.request` 或 payment evidence 残留

## Rollback
- 本批为策略审计，无实现代码变更需要回滚
- 如需撤回治理文件：
  - `git restore agent_ops/tasks/ITER-2026-03-31-489.yaml`
  - `git restore agent_ops/reports/2026-03-31/report.ITER-2026-03-31-489.md`
  - `git restore agent_ops/state/task_results/ITER-2026-03-31-489.json`
  - `git restore docs/ops/iterations/delivery_context_switch_log_v1.md`

## Next
- 可以新开一张显式高风险执行批次，只落地这一个 scratch pending-payment 样本，完成验证后在同批清理

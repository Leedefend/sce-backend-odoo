# Next Daily Business Iteration Plan v1

## 批次信息

- 批次：Batch-NDB-1
- 目标：制定下一张低成本 `screen` 任务，确认无合同付款已可办之后的下一个日常业务路径断点。
- 范围：业务连续性治理文档、任务合同、执行上下文日志。
- 不做：
  - 不修改 `addons/**`。
  - 不修改 `frontend/**`。
  - 不修改付款、结算、会计业务语义。
  - 不修改 ACL、record rules、manifest。
  - 不从前端增加模型特判。

## 架构定位

- Layer Target：Business Continuity Planning
- Module：next daily business operability path
- Module Ownership：customer-delivery business continuity
- Kernel or Scenario：scenario
- Backend Sub-Layer：business-fact layer
- Reason：无合同、无结算单日常付款已经在真实运行库权限和默认邮箱下完成 rollback-only E2E。下一步应继续从后端业务事实诊断可办性，而不是先改前端或直接进入高风险付款/结算实现。

## 输入事实

- `ITER-2026-04-18-APPLY-AUTHORITY-RUNTIME-UPGRADE`：PASS，日常无合同付款 E2E 已通过。
- `payment_lifecycle_continuity_screen_v1.md`：确认存在 `10429` 条无合同、无结算单 draft 日常付款候选。
- `daily_payment_e2e_probe_v1.md` 与 `authority_runtime_upgrade_v1.md`：确认付款可完成提交、审批、台账、办结，并 rollback clean。
- `procurement_source_lifecycle_screen_v1.md`：采购源、结算行、付款下游链路已被分类，但结算 submit/approve 会被历史孤儿付款请求阻断。
- `legacy_orphan_request_compliance_screen_v1.md`：全部 `30102` 条付款请求缺 `settlement_id`，其中 `12194` 条 done 且有台账，`17908` 条 draft 且无台账。
- `settlement_optional_business_logic_decision_v1.md`：结算单不是所有付款请求的强制前置载体；只有用户选择结算单时才应用结算一致性与余额检查。

## 实施步骤

### Step 1

- 操作：冻结下一张任务为只读 `screen`，目标命名为“settlement-backed daily payable path screen”。
- 修改范围：仅创建下一张 `agent_ops/tasks/*.yaml` 和筛查结果文档。
- 输出：下一张低成本 screen 任务合同。

完成判据：
- 合同声明 `mode: screen`。
- 合同 forbidden paths 覆盖 `addons/**`、`frontend/**`、`security/**`、`record_rules/**`、`ir.model.access.csv`、`__manifest__.py`。
- 合同明确不做付款/结算实现。
- 可进入下一步：是，前提是 `validate_task` 通过。

### Step 2

- 操作：在只读 Odoo shell 中筛查“带结算的日常应付路径”。
- 修改范围：无源码修改；只读查询或 rollback-only 探针。
- 输出：筛查文档，至少包含采购源、结算单、结算行、付款请求、付款台账之间的可办链路判断。

完成判据：
- 说明是否存在可复用的采购源事实。
- 说明新建结算单/结算行是否能在 rollback-only 中支撑带结算付款。
- 说明历史 draft/no-ledger 孤儿付款是否仍会阻断新结算流程。
- 明确下一步是继续 screen、进入高风险实现，还是停止。

### Step 3

- 操作：输出屏蔽边界与下一步建议。
- 修改范围：筛查文档与 delivery context log。
- 输出：可执行的 next_step。

完成判据：
- 如果只读筛查发现需要改 `*payment*` 或 `*settlement*` 语义，必须停止并开专门高风险任务。
- 如果只读筛查只发现数据事实缺口，下一步应先设计数据事实 screen/replay，不直接改业务逻辑。
- 如果可办链路已成立，下一步进入 verify 批次。

## 验证步骤

- verify：`python3 agent_ops/scripts/validate_task.py <next-screen-task>`
- snapshot：本批不改契约，不生成 contract snapshot。
- guard：`git diff --check`；若下一批触及运行态，使用对应 Makefile gate。
- smoke：本批不做前端 smoke；下一批若产生用户路径变更，再按任务合同声明。

## 风险与回滚

- 风险：把结算路径问题误判为前端问题。
- 回滚：撤回计划文档和任务合同，保持上一批 PASS 状态。
- 风险：在 screen 阶段越界进入付款/结算实现。
- 回滚：立即停止，恢复 screen 任务改动，重新开高风险合同。
- 风险：把历史 draft/no-ledger 付款自动当作已完成事实。
- 回滚：筛查结论必须区分 done/ledger 与 draft/no-ledger 两类，不做自动提升。

## 停机条件

- 发现需要修改 `addons/**` 才能完成本计划批次。
- 下一张任务无法保持 screen-only。
- 需要触碰付款、结算、会计、ACL、record rules、manifest。
- 发现前端模型特判方案。
- 只读筛查无法确定业务事实来源。

## 下一张任务建议

创建 `ITER-2026-04-18-SETTLEMENT-BACKED-DAILY-PAYABLE-PATH-SCREEN`：

- Layer Target：Business Fact Screening
- Module：settlement-backed daily payable path
- Backend Sub-Layer：business-fact layer
- Goal：只读筛查“带结算的日常应付路径”是否已具备采购源、结算行、付款申请、付款台账的可办事实链。
- Non-goal：不改付款/结算代码，不补前端特判，不做数据 replay。

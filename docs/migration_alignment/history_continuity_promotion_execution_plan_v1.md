# History Continuity Promotion Execution Plan v1

Status: PROMOTION_A_B_C_COMPLETED

Task: `ITER-2026-04-25-HISTORY-CONTINUITY-PROMOTION-001`

## 批次信息

- 批次：`Batch-History-Continuity-Promotion`
- 目标：
  - 将“历史数据已 replay 进入新系统”推进到“用户进入工作台、我的工作、核心列表/表单后可以继续业务”的可验证状态。
- 范围：
  - `scripts/migration/*`
  - `docs/migration_alignment/*`
  - `docs/ops/*`
  - `Makefile`
- 不做：
  - 不在本批直接重写业务流程
  - 不把所有 carrier 强行提升为 runtime ownership
  - 不改前端页面消费链

## 当前基线

首轮只读 probe 已完成：

- `DB_NAME=sc_demo make history.business.usable.probe`: `PASS`
- 决策：`history_business_usable_visible_but_promotion_gaps`

当前结论已收敛为单一 gap family：

- `payment_request_no_pending_runtime_states = true`

已确认不是 gap 的面：

- runtime list/form 缺失：否
- project ownership/runtime link 缺失：否
- contract partner/runtime link 缺失：否
- todo surface 完全缺失：否
- workflow audit 完全没有可执行 runtime surface：否

## 实施步骤

### Step 1

- 操作：
  - 补充只读 `history_business_usable_probe`，把现状拆成：
    - replayed facts
    - runtime visible records
    - actionable work surfaces
- 修改范围：
  - `scripts/migration/history_business_usable_probe.py`
  - `Makefile`
  - `docs/migration_alignment/*`
- 输出：
  - `history_business_usable_probe_result_v1.json`
  - `history_business_usable_probe_report_v1.md`

完成判据：
- 能明确回答：
  - 项目/合同/付款申请是否已有用户可见 runtime 记录
  - `mail.activity` / `tier.review` 是否已有可执行待办面
  - 哪些历史事实仍停在 carrier 层

### Step 2

- 操作：
  - 冻结第一轮 promotion gap family
  - 将 gap 分成：
    - runtime visible gap
    - actionable todo/approval gap
    - ownership/link gap
- 修改范围：
  - `docs/migration_alignment/*`
  - `docs/ops/iterations/*`
- 输出：
  - promotion gap matrix
  - 下一批执行顺序

完成判据：
- 每个 gap 都能明确归类到单一 family
- 不再把“数据在库里”误判成“用户已经可用”

### Step 3

- 操作：
  - 基于第一轮 gap，确定 promotion 优先顺序
  - 只允许先进入：
    - my-work / todo continuity
    - payment approval continuity
    - project ownership/runtime link continuity
- 修改范围：
  - 文档与计划，不直接改运行态
- 输出：
  - `Batch-History-Continuity-Promotion-A/B/C` 顺序

完成判据：
- 下一批能直接进入单目标实现
- 每批只处理一个用户可见 continuity 面

## 下一批候选

- `Batch-History-Continuity-Promotion-A`
  - 目标：`payment.request` state activation / approval continuity
  - 原因：首轮 probe 证明当前唯一 blocker 是 `27802` 个历史 `payment.request` 全部停留在 `draft`

## Promotion-A Result

`Batch-History-Continuity-Promotion-A` 已完成，采用的是历史状态激活而不是 live approval runtime 重建：

- 只处理 `outflow_request_core`
- 只将带历史 workflow audit 事实的 `payment.request` 从 `draft` 激活到 `submit`
- 不写 `tier.review`
- 不写 `validation_status`

实跑结果：

- workflow-covered rows：`12247`
- promoted rows：`12247`
- blocked rows：`0`
- `DB_NAME=sc_demo make history.business.usable.probe`：
  - `decision = history_business_usable_ready`
  - `gap_count = 0`

## Promotion-B Result

`Batch-History-Continuity-Promotion-B` 也已完成：

- 复用既有 `legacy_payment_approval_downstream_fact` judgment
- 仅对 `outflow_request_core` 执行 `submit -> approved`
- 不写 `tier.review`
- 不写 `validation_status`

实跑结果：

- approved candidates：`12201`
- promoted rows：`12201`
- 当前 `outflow_request_core` 状态分布：
  - `approved = 12201`
  - `submit = 46`
  - `draft = 37`

## Promotion-C Result

`Batch-History-Continuity-Promotion-C` 已完成：

- 复用既有 `legacy_payment_approval_downstream_fact_state_sync_snapshot` paid facts
- 仅对 `outflow_request_core` 执行 `approved -> done`
- 同步恢复最小新系统支付事实：
  - `validation_status = validated`
  - one minimal `payment.ledger` row per recovered request
- 不写 `tier.review`
- 不写 `sc.settlement.order`

实跑结果：

- done candidates：`12194`
- promoted rows：`12194`
- 当前 `outflow_request_core` 状态分布：
  - `done = 12194`
  - `approved = 7`
  - `submit = 46`
  - `draft = 37`

## 验证步骤

- `DB_NAME=sc_demo make history.business.usable.probe`
- `DB_NAME=sc_demo make history.continuity.rehearse`
- 只读 DB probe 与 artifacts 对齐检查

## 风险与回滚

- 风险：
  - 将 carrier 存在误判成 runtime 可用
  - 在 gap 尚未分层前直接推进 promotion，导致跨层混改
- 回滚：
  - 本批仅新增只读 probe 与文档，可按文件级回退

## 停机条件

- 无法明确区分 runtime visible 与 actionable surfaces
- 发现 probe 需要写 DB 才能得出结论
- 业务可用性定义出现跨批次扩张

# Payment Fact Consistency Audit v1

## 目标

冻结项目驾驶舱、付款页、结算页中“付款”语义的统一口径，避免以下三层事实继续混用：

- `payment.request`
- `payment.ledger`
- `sc.settlement.order`

## 核心结论

当前用户面上的“付款”主语义，应明确冻结为：

### 1. 付款申请事实

- 主模型：`payment.request`
- 适用语义：
  - `payment_record_count`
  - `payment_total_amount`
  - `draft_payment_amount`
  - `approved_record_count`
  - 驾驶舱 `payment_total`
  - 结算页 `total_payment`

这意味着当前产品页里“付款”展示的是：

> 项目维度的付款申请事实

而不是：

- 银行已实际支付金额
- 会计记账金额
- 结算单确认金额

### 2. 已支付台账事实

- 主模型：`payment.ledger`
- 当前定位：
  - demo 闭环证据层
  - 支付完成凭证层

当前它不应直接替代驾驶舱和付款页中的“付款合计”，除非后续新批次明确升级产品语义。

### 3. 结算完成事实

- 主模型：`sc.settlement.order(state=done)`
- 当前定位：
  - 项目是否已形成结算闭环
  - Flow Map / Completion 的结算完成判定

结算完成态不能反向覆盖“付款合计”的来源。

## 当前消费矩阵

| 页面/服务 | 当前付款语义 | 当前事实源 | 结论 |
| --- | --- | --- | --- |
| 驾驶舱摘要 `project_dashboard_service.project_payload` | 付款合计 | `PaymentSliceNativeAdapter.summary().total_payment_amount` | 应保留为 `payment.request` |
| 决策引擎 `project_decision_engine_service` | 付款数量/金额 | `payment.request` | 应保留为 `payment.request` |
| 付款页 `payment_slice_service.project_payload` | 付款记录数/付款合计/草稿金额 | `payment.request` | 应保留为 `payment.request` |
| 付款页 block `payment_slice_summary_builder` | total / record_count / approved_record_count | `payment.request` | 应保留为 `payment.request` |
| 结算页 `settlement_slice_service.summary` | total_payment / payment_record_count | `payment.request` | 应保留为 `payment.request` |
| 驾驶舱资金块 `project_finance_builder` | `paid / pay_pending / received` | `payment.request` | 当前语义是“申请已批准/完成”，不是 ledger |
| demo 完整闭环证据 | 已支付证明 | `payment.ledger` | 只作为证据层 |
| 完成闭环判定 | 结算完成 | `sc.settlement.order(state=done)` | 不应替代付款合计 |

## 当前风险点

### 风险 1：把 `payment.ledger` 当成用户面付款合计

这样会导致：

- 驾驶舱与付款页金额不一致
- demo 项目中“有付款申请但未形成 ledger”的场景被误判为无付款

### 风险 2：把结算完成反推为付款已完成

这样会导致：

- `Completion / Flow Map` 看起来已完成
- 付款页却没有对应的付款申请事实

### 风险 3：页面文案与事实源不一致

如果页面写“总付款”，但底层实际上代表“付款申请总额”，用户会天然误解成“已支付金额”。

## 本轮冻结口径

### 用户面付款语义

除非后续显式升级 contract，当前统一冻结为：

> `payment.request(type=pay)` 的项目级申请事实

对应：

- 数量：`request_count`
- 金额：`total_payment_amount`
- 草稿金额：`draft_payment_amount`
- 已批准/完成数：`approved_request_count`

### 已支付语义

若后续要展示“已支付金额”，必须新增独立字段，不得复用当前：

- `payment_total`
- `payment_total_amount`
- `total_payment`

建议未来独立命名为：

- `payment_executed_total`
- `payment_ledger_count`

## 本轮 Guard

新增 `payment_fact_consistency_guard`，验证：

- 驾驶舱 `payment_total` 等于付款页 `payment_total_amount`
- 结算页 `total_payment` 等于付款页 `payment_total_amount`
- 驾驶舱、付款页、结算页的 `payment_record_count` 都等于 `payment.request` 计数
- 决策引擎中的 `payment_count / payment_total` 与同一项目的 `payment.request` 事实一致
- `payment.ledger` 不参与当前用户面付款总额计算

## 后续建议

如果后续要继续提升业务说服力，下一批应做：

### Payment Evidence Layer v1

目标：

- 在不破坏当前“付款申请事实”口径的前提下
- 为驾驶舱或付款页新增独立的“已支付证据”字段
- 让 `payment.request` 与 `payment.ledger` 同时可见但不混义

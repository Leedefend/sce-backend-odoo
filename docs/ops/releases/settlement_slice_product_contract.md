# Settlement Slice Product Contract

## 定位

- 切片：`FR-5 settlement slice`
- 阶段：`Prepared`
- 切片类型：`新切片`
- 目标链路：`execution/cost/payment -> settlement summary`
- 本文性质：`Prepared 产品口径文档`

## 入口

- 上游入口一：`project.execution`
- 上游入口二：`cost.tracking`
- 上游入口三：`payment`
- 切片入口 intent：`settlement.enter`
- 入口来源：`execution` / `cost` / `payment` 的 `next_actions`

## 一句话定义

- 结算 = 基于当前切片数据的项目级简单汇总结果

## 本轮允许内容

- 显示项目总成本
- 显示项目总付款
- 显示项目差额
- 单一 `settlement_summary` block
- `execution/cost/payment -> settlement` 的 next_action
- contract guard、flow smoke、browser smoke 与 prepared gate

## 本轮禁止内容

- 新建复杂模型
- 合同结算规则
- 审批
- 发票
- 税务
- 多维分析
- 报表体系
- 修改 FR-1 / FR-2 / FR-3 / FR-4 冻结语义

## 主链定义

1. 用户进入 `project.execution`、`cost.tracking` 或 `payment`。
2. 用户点击“结算结果”进入 `settlement.enter`。
3. 系统展示项目级只读结算汇总。
4. 用户看到总成本、总付款与差额。

## 最小结果口径

- 主载体：
  - 成本来源：`account.move`
  - 付款来源：`payment.request`
- 后端汇总字段：
  - `total_cost`
  - `total_payment`
  - `delta`
  - `currency_name`
- 前端只展示，不做任何计算

## 用户路径

1. 进入执行、成本或付款场景。
2. 点击结算入口。
3. 查看结算结果 block。
4. 核对总成本、总付款与差额。

## 明确不承诺

- 合同规则
- 审批动作
- 发票与税务
- 分析报表
- 利润复杂计算
- 任何写入型结算动作

## 当前目标结论

- 本轮只做：`Prepared`
- 本轮不宣称：`Freeze`

# Payment Slice Product Contract

## 定位

- 切片：`FR-4 payment slice`
- 阶段：`Prepared`
- 切片类型：`新切片`
- 目标链路：`execution/cost -> payment entry -> payment list -> payment summary`
- 本文性质：`Prepared 产品口径文档`

## 入口

- 上游入口一：`project.execution`
- 上游入口二：`cost.tracking`
- 切片入口 intent：`payment.enter`
- 入口来源：`execution` / `cost` 的 `next_actions`

## 本轮允许内容

- 一条付款记录
- 项目级付款列表
- 项目级付款汇总
- `execution -> payment` 的 next_action
- `cost -> payment` 的 next_action
- browser smoke 与 prepared gate

## 本轮禁止内容

- 合同条款管理
- 审批流
- 发票
- 税务
- 资金账户复杂模型
- 成本联动计算
- 结算
- 修改 FR-1 / FR-2 / FR-3 冻结语义

## 主链定义

1. 用户进入 `project.execution` 或 `cost.tracking`。
2. 用户点击付款入口进入 `payment.enter`。
3. 用户在付款切片中录入一条付款。
4. 用户看到付款记录列表出现该条记录。
5. 用户看到付款汇总发生变化。

## 最小录入口径

- 主载体：`payment.request`
- 必填最小输入：
  - `project_id`
  - `amount`
  - `date`
  - `description`
- 服务端复用字段：
  - `type=pay`
  - `partner_id`
  - `currency_id`
  - `state=draft`

## 最小结果口径

### 付款录入

- 成功创建一条与项目稳定关联的 `draft payment.request`
- 返回统一结果结构

### 付款列表

- 列表至少展示：
  - `date`
  - `amount`
  - `description`
  - `project_id`
  - `partner_name`

### 付款汇总

- 汇总至少展示：
  - `total_payment_amount`
  - `record_count`

## 用户路径

1. 进入执行或成本场景。
2. 点击付款入口。
3. 输入日期、金额与说明。
4. 提交付款记录。
5. 在付款列表中看到该条记录。
6. 在付款汇总中看到合计变化。

## 明确不承诺

- 合同条款管理
- 审批动作
- 发票与税务处理
- 资金账户模型
- 成本联动计算
- 结算闭环

## 当前目标结论

- 本轮只做：`Prepared`
- 本轮不宣称：`Freeze`

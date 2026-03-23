# Cost Slice Product Contract

## 定位

- 切片：`FR-3 cost tracking slice`
- 阶段：`Prepared`
- 目标链路：`项目创建 -> 驾驶舱 -> 计划 -> 执行 -> 成本记录 -> 成本汇总`
- 本文性质：`Prepared 产品口径文档`

## 入口

- 上游入口：`project.execution`
- 切片入口 intent：`cost.tracking.enter`
- 入口来源：`project.execution` 的 `next_actions`

## 本轮允许内容

- 成本录入
- 成本列表
- 成本汇总
- `execution -> cost` 的 next_action
- browser smoke 与 prepared gate

## 本轮禁止内容

- 成本预算
- 成本分析
- 成本审批
- 成本对比
- 财务深度集成
- 合同/付款联动
- 结算切片

## 主链定义

1. 用户进入 `project.execution`。
2. 用户点击成本入口进入 `cost.tracking.enter`。
3. 用户在成本切片中录入一条成本。
4. 用户看到成本记录列表出现该条记录。
5. 用户看到成本汇总发生变化。

## 最小录入口径

- 主载体：`account.move`
- 必填最小输入：
  - `project_id`
  - `amount`
  - `date`
- 可选输入：
  - `description`
  - `cost_code_id`

## 最小结果口径

### 成本录入

- 成功创建一条与项目稳定关联的成本记录
- 返回统一结果结构

### 成本列表

- 列表至少展示：
  - `date`
  - `amount`
  - `description`
  - `category`
  - `project_id`

### 成本汇总

- 汇总至少展示：
  - `total_amount`
  - `record_count`

## 用户路径

1. 进入执行场景。
2. 点击成本入口。
3. 输入金额、日期与说明。
4. 提交成本记录。
5. 在成本列表中看到该条记录。
6. 在成本汇总中看到合计变化。

## 明确不承诺

- 成本预算闭环
- 成本分析报表闭环
- 成本审批流
- 合同/付款协同
- 结算分析

## 当前目标结论

- 本轮只做：`Prepared`
- 本轮不宣称：`Freeze`

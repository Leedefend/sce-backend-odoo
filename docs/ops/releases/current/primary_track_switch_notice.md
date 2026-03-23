# Primary Track Switch Notice

## 主线切换声明

### 旧主线

- `ActionView` 架构拆解

### 新主线

- `项目创建 -> 驾驶舱` 首发切片

## 当前优先级

- `P0 治理收口`
- `首发切片冻结`
- `第二切片（项目创建 -> 驾驶舱 -> 计划 -> 执行）`
- `其他`

## 暂停项

- `ActionView` 深化
- 成本闭环
- 合同/付款切片
- 结算分析

## 允许继续做的范围

- 只允许为 `项目创建 -> 驾驶舱` 首发切片服务的改动：
  - creation flow contract
  - dashboard entry contract
  - dashboard block contract
  - 首发链前端 contract 消费
  - 首发链 verify / smoke / browser evidence
  - 首发范围与冻结文档

## 禁止项

- 未挂到首发链的开发
- 以页面热点为中心的继续深挖
- 借首发切片名义扩展第二切片或成本/合同/结算能力

## 切换理由

- `ActionView` Phase 2 已完成冻结条件，不再是当前最大不确定性来源。
- 当前最大收益点已经转为：
  - 固定首发链结构
  - 固定首发 contract / guard
  - 固定首发前端消费边界

## 执行口径

- 从本通知起，默认开发主线为：
  - `project.initiation -> project.dashboard`
- 任何未直接服务该链路的开发，必须单独说明理由。

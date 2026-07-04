# 正式办理核心流程新增编辑 Smoke V1

本门禁抽取核心正式办理入口，以菜单动作运行上下文执行 ORM 新增与编辑，并在事务 savepoint 内回滚，验证历史数据进入正式模型后仍能按正式业务继续维护。

## 摘要

- 数据库：`sc_demo`
- 核心流程：`12`
- 通过：`12`
- 失败：`0`
- issue 分布：`{}`

## 结果

| 入口 | 模型 | 新增 | 新增后编辑 | 既有记录编辑 | 写字段 | 问题 |
| --- | --- | --- | --- | --- | --- | --- |
| 一般合同（公司） | `sc.general.contract` | `pass` | `pass` | `pass` | `note` | PASS |
| 施工合同 | `construction.contract` | `pass` | `pass` | `pass` | `note` | PASS |
| 材料计划 | `project.material.plan` | `pass` | `pass` | `pass` | `date_plan` | PASS |
| 材料入库 | `sc.material.inbound` | `pass` | `pass` | `pass` | `note` | PASS |
| 材料出库 | `sc.material.outbound` | `pass` | `pass` | `pass` | `note` | PASS |
| 分包申请 | `sc.subcontract.request` | `pass` | `pass` | `pass` | `note` | PASS |
| 分包结算 | `sc.subcontract.settlement` | `pass` | `pass` | `skip` | `note` | PASS |
|  |  |  |  |  |  | `no existing record` |
| 方单 | `sc.labor.usage` | `pass` | `pass` | `pass` | `note` | PASS |
| 机械台班记录 | `sc.equipment.usage` | `pass` | `pass` | `pass` | `note` | PASS |
| 收款登记 | `sc.receipt.income` | `pass` | `pass` | `pass` | `note` | PASS |
| 费用报销单 | `sc.expense.claim` | `pass` | `pass` | `pass` | `note` | PASS |
| 进项发票 | `sc.invoice.registration` | `pass` | `pass` | `pass` | `note` | PASS |

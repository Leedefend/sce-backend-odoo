# Demo Scenarios Catalog (S00–S90)

本文件定义 Smart Construction Demo Platform 的全部演示场景、
业务目标、核心模型与可验证断言。

目标：
- 作为演示与回归测试的统一入口
- 作为业务规则的“可执行样本库”
- 为后续场景（S50+）提供设计基准

## Scenario Index

| Code | Name | Business Goal | Core Models | Verification Focus |
|-----:|------|---------------|-------------|--------------------|
| S00 | Minimal Path | 项目最短可跑路径 | project / boq / material / invoice | 基础数据存在性 |
| S10 | Contract + Payment | 合同 → 付款申请 → 发票 | construction.contract / payment.request / account.move | 关联完整性 |
| S20 | Settlement Clearing | 结算单 + 明细 + 收款关联 | sc.settlement.order(+line) / payment.request | 结算完整性 |
| S30 | Workflow Gate | 可推进但未推进 | sc.settlement.order | 门禁条件成立 |
| S40 | Failure Paths | 非法状态不可推进 | sc.settlement.order | 失败路径锁定 |
| S50 | Repairable Failure | 失败→修复→通过 | sc.settlement.order / payment.request | 修复闭环可验证 |
| S90 | Users & Roles | 角色演示与门禁 | res.users / res.groups | 权限可见性基线 |

## Scenario Dependency

- S00 为所有场景基础
- S10 依赖 S00（项目 / 往来单位）
- S20 依赖 S10（付款申请 / 合同）
- S30 基于 S20，但使用独立结算单
- S40 为独立失败样本，不参与正常流程
- S50 依赖 S00（基础项目/往来单位），通过修复补丁完成闭环
- S90 依赖核心权限组，按场景加载演示账号

## S00 – Minimal Path

目标：
提供最短可跑的演示路径，覆盖项目、BOQ、材料与发票。

断言：
- 项目/BOQ/材料/发票数据存在

## S10 – Contract + Payment

目标：
演示合同、付款申请与发票的最小闭环（均保持 draft）。

关键记录：
- sc_demo_contract_out_010
- sc_demo_pay_req_010_001
- sc_demo_invoice_s10_001 / sc_demo_invoice_s10_002

断言：
- 合同/付款申请/发票记录存在

## S20 – Settlement Clearing

目标：
演示结算单、结算明细与收款关联的业务闭环。

关键记录：
- sc_demo_settlement_020_001
- sc_demo_settle_line_020_001 / sc_demo_settle_line_020_002
- sc_demo_payment_020_001

断言：
- 结算单/明细存在
- 结算单与收款关联存在

## S30 – Settlement Workflow Gate

目标：
验证在满足业务条件前，结算单不会自动推进状态。

关键记录：
- sc_demo_settlement_030_001（完整条件）
- sc_demo_settlement_030_bad_001（缺条件）

断言：
- 完整结算单：state = draft + 条件齐全
- 缺条件结算单：state 永远为 draft

## S40 – Failure Paths

目标：
证明结构性/金额/关联违规数据不会推进状态。

关键记录：
- sc_demo_settlement_040_structural_bad
- sc_demo_settlement_040_amount_bad
- sc_demo_settlement_040_link_bad

断言：
- 所有 S40 记录必须保持 draft
- 结构/金额/关联失败条件可验证

## S50 – Repairable Failure

目标：
演示“失败→修复→通过”的最小闭环。

关键记录：
- sc_demo_settlement_050_001（bad seed）
- sc_demo_payment_050_001（bad: 未关联）

断言：
- bad 阶段：结算单不应关联 payment.request
- fix 阶段：payment.request 成功关联结算单

加载方式：
- bad: `make demo.load SCENARIO=s50_repairable_paths STEP=bad DB_NAME=sc_demo`
- fix: `make demo.load SCENARIO=s50_repairable_paths STEP=fix DB_NAME=sc_demo`

## S90 – Users & Roles

目标：
提供角色演示账号，并验证最小权限门禁。

关键记录：
- demo_pm / demo_finance / demo_cost / demo_audit / demo_readonly

断言：
- 用户存在
- 财务账号不具备合同中心能力
- 只读账号不具备结算经办能力

## Verification Model

所有场景均通过 make demo.verify 验证。

原则：
- 不调用 action_*
- 不依赖 UI 或审批流
- 仅使用 SQL 验证数据状态与约束

这保证了：
- CI 可用
- 回归可复现
- 演示稳定

可选用法：
- `make demo.verify SCENARIO=s30_settlement_workflow`
- `make demo.verify SCENARIO=s50_repairable_paths STEP=bad`

## Versioning & Evolution

当前版本：Demo Platform v2 (S00–S90)

约定：
- 新场景必须新增 Sxx 编号
- 不修改已有场景语义
- S50+ 只能作为增强，不回溯破坏 v1

## Roadmap: cost_domain_demo 拆分计划（S6x）

约定：
- core 中的 cost_domain_demo.xml 保持冻结，不默认加载（仅保留历史参考）
- 未来拆分为 S60–S63，按业务域解耦

建议拆分：
- S60：成本域基础对象（项目/WBS/预算）
- S61：预算 BOQ 与成本分摊
- S62：成本台账与进度
- S63：预算导入/模板样例

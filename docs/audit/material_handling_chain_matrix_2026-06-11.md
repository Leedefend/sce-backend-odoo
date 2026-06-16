# Material Handling Chain Matrix - 2026-06-11

## Scope

本矩阵是 `business_handling_delivery_master_plan_2026-06-11.md` 的 Phase 3 执行拆解。目标不是先做库存报表，而是保护用户最大体量的材料业务数据，并把材料计划、采购申请、询比价、验收、入库、出库、结算、成本和付款办理串起来。

## Current Evidence

```text
DB_NAME=sc_demo scripts/ops/validate_business_category_dictionary.sh
BUSINESS_CATEGORY_DICTIONARY_AUDIT: status=PASS
covered: 37 business category template records
material covered: material.plan, material.purchase.request, material.acceptance, material.rfq, material.inbound, material.outbound, material.return, material.transfer, material.loss, material.settlement
```

```text
DB_NAME=sc_demo scripts/ops/validate_material_business_category_runtime.sh
MATERIAL_BUSINESS_CATEGORY_RUNTIME_AUDIT: status=PASS
covered: 10 material category candidates
evidence: create temp record from runtime action context, then verify current runtime action domain can find it
```

```text
DB_NAME=sc_demo scripts/ops/validate_material_outbound_derivative_strategy.sh
MATERIAL_OUTBOUND_DERIVATIVE_STRATEGY_AUDIT: status=PASS
covered: material.return, material.transfer, material.loss action/domain, stock summary and cost trigger strategy
evidence: return/transfer/loss records are visible through their own actions; all enter stock summary; return/transfer do not create project cost; transfer creates a received inbound fact and nets stock to zero by project/material aggregation; loss creates project cost
```

```text
DB_NAME=sc_demo scripts/ops/validate_material_loss_approval_policy.sh
MATERIAL_LOSS_APPROVAL_POLICY_AUDIT: status=PASS
covered: optional material loss approval policy, required material loss approval policy, cost ledger gate
evidence: default optional policy can confirm loss directly; required policy keeps loss submitted and creates no cost ledger before approval; approved loss confirms and writes project cost
```

```text
DB_NAME=sc_demo scripts/ops/validate_material_handling_evidence.sh
MATERIAL_HANDLING_EVIDENCE_AUDIT: status=PASS
covered: material plan, purchase request, acceptance, RFQ, inbound, outbound, settlement
evidence: attachment, state closure, invalid state blocking, material lines, project/supplier/warehouse relation, audit event
```

```text
DB_NAME=sc_demo scripts/ops/validate_material_downstream_traceability.sh
MATERIAL_DOWNSTREAM_TRACEABILITY_AUDIT: status=PASS
covered: inbound, outbound, material stock summary, material settlement, cost ledger, payment request
evidence: formal inbound/outbound lines enter sc.material.stock.summary; issued outbound creates project.cost.ledger; confirmed settlement creates project.cost.ledger and linked payment.request
```

```text
DB_NAME=sc_demo scripts/ops/validate_material_cross_document_traceability.sh
MATERIAL_CROSS_DOCUMENT_TRACEABILITY_AUDIT: status=PASS
covered: material plan -> RFQ -> purchase order -> acceptance -> inbound -> material stock summary
evidence: source plan, source RFQ, purchase order line, acceptance line and inbound line links remain traceable; inbound amount uses purchase order price
```

```text
DB_NAME=sc_demo scripts/ops/validate_material_plan_purchase_request_traceability.sh
MATERIAL_PLAN_PURCHASE_REQUEST_TRACEABILITY_AUDIT: status=PASS
covered: material plan -> purchase request -> acceptance
evidence: source plan, source plan line, generated request idempotency, request approval and acceptance traceability
```

```text
DB_NAME=sc_demo scripts/ops/validate_material_purchase_request_downstream_strategy.sh
MATERIAL_PURCHASE_REQUEST_DOWNSTREAM_STRATEGY_AUDIT: status=PASS
covered: approved purchase request -> RFQ; approved purchase request -> purchase order -> acceptance
evidence: supplier requirement, request/source line traceability, plan/source line traceability, idempotent RFQ/order generation
```

```text
DB_NAME=sc_demo scripts/ops/validate_material_cost_trigger_policy.sh
MATERIAL_COST_TRIGGER_POLICY_AUDIT: status=PASS
covered: material.outbound issue_project_cost_ledger; material.settlement confirm_project_cost_ledger and confirm_payment_request
evidence: disabled policy produces no cost ledger/payment request; enabled policy creates cost ledger/payment request with source traceability
```

```text
DB_NAME=sc_demo scripts/ops/validate_material_settlement_payment_execution_traceability.sh
MATERIAL_SETTLEMENT_PAYMENT_EXECUTION_TRACEABILITY_AUDIT: status=PASS
covered: material settlement -> payment request -> payment execution -> payment ledger
evidence: material settlement payment request can be submitted/approved without a generic contract; payment execution marks paid; payment ledger opens back to material settlement
```

```text
DB_NAME=sc_demo scripts/ops/validate_material_role_permissions.sh
MATERIAL_ROLE_PERMISSION_AUDIT: status=PASS
covered: material purchase request, acceptance, inbound, outbound, RFQ, settlement, material settlement payment request
evidence: read users cannot execute handling actions; material users can submit but cannot confirm; material managers confirm stock/settlement actions; purchase users start RFQ; purchase managers approve pricing/order generation; finance users/managers handle payment request submit/approval
```

```text
DB_NAME=sc_demo scripts/ops/validate_material_settlement_split_payment.sh
MATERIAL_SETTLEMENT_SPLIT_PAYMENT_AUDIT: status=PASS
covered: material settlement split payment request, cumulative material payment amount gate, over-request blocking, payment summary fields
evidence: first request 60, remaining request 40, full paid 100, extra over request submit blocked
```

```text
DB_NAME=sc_demo scripts/ops/validate_material_settlement_payment_reversal.sh
MATERIAL_SETTLEMENT_PAYMENT_REVERSAL_AUDIT: status=PASS
covered: paid payment execution reversal, payment ledger removal, payment request reopen, material settlement remaining amount recovery, repay after reversal
evidence: paid request returns to approved after reversal; ledger is removed; material settlement unpaid amount recovers; second payment can complete again
```

```text
DB_NAME=sc_demo scripts/ops/validate_material_settlement_payment_execution_approval_policy.sh
MATERIAL_SETTLEMENT_PAYMENT_EXECUTION_APPROVAL_POLICY_AUDIT: status=PASS
covered: optional payment execution approval policy, required payment execution approval policy, material settlement payment registration gate
evidence: default no-approval policy can register payment; required policy blocks payment before approval and allows payment after approval
```

## User Data Reading

当前用户画像中材料相关数据体量最高，材料目录约 228.86 万条，采购库存相关事实合计约 233.51 万条。材料能力不能只做历史查询或库存汇总，必须先保证用户可以继续办理日常材料业务。

设计判断：

- 材料目录和历史映射是基础主数据，不能被新办理记录污染。
- 历史直接验收、历史入库等来源事实保留为追溯入口，不能为了统一菜单覆盖成新办理入口。
- 新办理入口要使用用户可理解的业务语言，例如材料计划、采购申请、验收、入库办理、出库单、材料结算。
- 材料分类进入 `sc.business.category`，必填字段、附件、审批和下游成本/付款策略都挂到分类上，而不是写死到菜单或模型分支。
- 菜单入口可以按能力域整合，但业务类别必须按用户真实数据和用户已理解的办理语言保留清晰边界；可以通过 action 域、默认上下文、表单分组、状态动作和按钮显隐切分办理事项。
- 当前用户材料数据是建筑行业样本，不是产品边界；可复用的材料计划、采购、验收、库存和结算规则要沉淀为行业模板默认值，客户差异通过业务分类字典维护。

## Entry Matrix

| 用户入口 | 分类编码 | 正式模型 | 当前办理动作 | 下游事实 | 当前结论 | 下一步 |
| --- | --- | --- | --- | --- | --- | --- |
| 材料计划 | `material.plan` | `project.material.plan` | 保存、提交、批准、完成、生成询价单、生成采购申请 | 询比价、采购申请、采购订单候选 | 入口可见、状态动作、审计、计划转询价和计划转采购申请追溯通过 | 补计划分支策略配置：直接采购申请、询价采购、框架采购 |
| 采购申请 | `material.purchase.request` | `sc.material.purchase.request` | 提交、审批、生成询价单、生成采购订单 | 询比价、采购订单、验收 | 入口可见、状态动作、来源计划追溯、审批、验收带入、生成询价和直接生成采购订单追溯通过 | 将直接采购、询价采购、框架采购沉淀为分类策略 |
| 材料进场验收 | `material.acceptance` | `sc.material.acceptance` | 提交、验收通过、取消 | 入库单、验收证据 | 附件、状态动作、审计、采购订单带入和验收转入库追溯通过 | 补验收质检/退场分支 |
| 询比价 | `material.rfq` | `sc.material.rfq` | 提交、中选、生成采购订单 | 采购订单、供应商价格 | 附件、状态动作、中选供应商、采购订单生成和追溯通过 | 补多供应商报价策略沉淀 |
| 入库办理 | `material.inbound` | `sc.material.inbound` | 提交、确认入库 | 库存汇总、材料成本 | 新办理入口独立，附件、状态动作、审计、采购订单价格带入和库存汇总追溯通过；默认不在入库时计成本 | 补入库计成本行业模板变体 |
| 领用出库 | `material.outbound` | `sc.material.outbound` | 提交、确认出库 | 库存汇总、项目成本台账 | 状态动作、审计、库存汇总和项目成本台账追溯通过 | 沉淀出库策略到行业模板 |
| 退库办理 | `material.return` | `sc.material.outbound` | 提交、确认退库 | 库存汇总 | action/domain、状态动作、库存汇总、无项目成本策略追溯通过 | 补退库来源单据和供应商退货策略 |
| 材料调拨 | `material.transfer` | `sc.material.outbound` -> `sc.material.inbound` | 提交、确认调拨、自动确认调入入库 | 库存汇总、调入侧入库事实 | action/domain、调入仓库必填、自动生成已入库调入单、双边库存聚合净额、无项目成本策略追溯通过 | 补独立调拨接收确认和跨仓责任策略 |
| 材料损耗 | `material.loss` | `sc.material.outbound` | 提交、确认损耗、可选统一审批 | 库存汇总、项目成本台账 | action/domain、损耗原因必填、可选审批策略、审批前不写成本、审批后确认损耗并写项目成本追溯通过 | 补损耗责任归集策略 |
| 材料结算 | `material.settlement` | `sc.material.settlement` | 提交、确认结算、生成付款申请、生成剩余付款申请、付款审批、付款登记、付款登记审批、登记付款、撤销付款 | 成本台账、付款申请、付款执行、付款台账 | 状态动作、金额计算、审计、成本台账、分批付款、累计超付阻断、付款汇总、付款执行、付款登记审批策略、付款撤销、付款台账、策略开关和角色门禁追溯通过 | 沉淀付款策略到分类/行业模板 |

## Boundary Rules

- 历史材料计划和历史入库入口继续用于来源事实查看；新办理入口不能复用带 `legacy_fact_model` / `legacy_fact_type` 过滤的历史 action。
- `material.plan` 当前绑定 `action_project_material_plan_my`，用于当前用户可办理的材料计划。
- `material.inbound` 当前绑定 `action_sc_material_inbound_handling`，用于新入库办理。
- 入口可以在菜单上整合到材料能力域，但每个入口必须保留明确分类编码、默认上下文和可追溯下游策略。
- 行业模板提供建筑行业默认材料分类；客户可以停用、改名、排序和调整必填/附件/审批策略。
- 材料计划允许按用户认知分支生成询价单或采购申请：询价采购适合需要供应商比价的场景，直接采购申请适合用户已明确采购需求的场景；两个分支都必须保留来源计划和来源计划明细。
- 材料计划生成采购申请必须按来源计划幂等，已有未取消采购申请时打开原单，避免重复下游申请污染用户业务数据。
- 采购申请审批后允许按用户认知继续分支：生成询价单用于比价采购，直接生成采购订单用于已明确供应商的采购；两个分支都必须保留来源采购申请、来源申请明细、来源计划和来源计划明细。
- 采购申请生成询价单或采购订单必须按来源采购申请幂等，已有未取消下游单据时打开原单；直接生成采购订单前必须维护拟采购供应商，避免系统默认供应商替代真实业务判断。
- 库存统计表同时承载历史材料库存事实和新办理出入库明细；历史追溯入口继续保留，新办理事实通过正式模型进入汇总口径。
- 材料成本触发由 `sc.business.category.ledger_policy_json.cost_triggers` 控制，建筑行业模板默认：入库不直接计成本，领用出库和损耗写项目成本，退库和调拨只影响库存，结算确认写项目成本并生成付款申请。
- 材料出库按 `outbound_type` 映射到 `material.outbound` / `material.return` / `material.transfer` / `material.loss` 分类；确认后如该分类的 `issue_project_cost_ledger` 为真，则按出库明细金额写入 `project.cost.ledger`，来源模型、来源单据和来源明细必须可追溯。
- 退库、调拨、损耗复用 `sc.material.outbound` 正式模型，但必须通过 action domain/context、`outbound_type`、表单字段和业务分类字典保留用户可理解的办理边界；菜单可以整合，分类不能丢失。
- 材料调拨确认后必须生成调入侧 `sc.material.inbound` 事实，`source_transfer_outbound_id` 和 `transfer_inbound_id` 双向追溯；当前策略为出库确认后自动提交并确认调入入库，库存汇总按项目/材料聚合后入出净额为零，跨仓/往来单位维度可以拆行展示。
- 材料损耗默认可直接由物资负责人确认；启用 `sc.material.outbound` 审批策略后，仅 `outbound_type=loss` 的损耗确认进入统一审批，审批通过前不得写入项目成本台账，退库、调拨和领用出库不受该策略阻断。
- 材料结算确认后，如 `material.settlement` 的 `confirm_project_cost_ledger` / `confirm_payment_request` 为真，则分别写入 `project.cost.ledger` 和 `payment.request`；二者必须通过来源模型、来源记录、来源明细或 `material_settlement_id` 可追溯。
- 材料结算本身是材料付款依据；材料结算生成的付款申请允许不绑定通用合同，但必须绑定已确认材料结算、项目和供应商，并继续走付款申请审批、付款登记和付款台账。
- 材料结算允许多个付款申请承接分批付款；已提交、已审批、已完成等非草稿/非取消付款申请占用结算可付额度，提交、审批和强制批准时必须阻断累计金额超过结算含税金额。
- 材料结算的“生成剩余付款申请”优先打开已有草稿付款申请；没有草稿时才按剩余可付金额创建新草稿，剩余金额为零时必须阻断重复登记。
- 材料结算付款汇总字段用于办理提示和追溯，付款申请数量可以包含草稿，但额度硬校验只以非草稿/非取消申请作为占用口径。
- 材料结算付款执行已登记付款后允许财务撤销新系统付款执行：撤销时删除对应付款台账、将付款申请从完成退回已批准、恢复材料结算未付款余额，并保留付款执行取消状态和付款申请审计轨迹；历史迁移付款执行不允许在新系统撤销。
- 材料结算付款登记审批由 `sc.approval.policy` 的 `sc.payment.execution` 策略控制：默认可作为登记类业务免审批直接确认付款；启用审批后，付款执行必须先提交统一审批，未审批通过时不得登记付款，审批通过后才允许写付款台账并完成付款申请。
- 付款台账打开结算来源时必须优先识别 `material_settlement_id`，材料结算链路不能被强行解释为通用结算单。
- 采购订单生成验收时，后端 create 与前端 onchange 必须保持同一套默认带入规则；验收转入库时，若来源为采购订单，入库金额应优先使用采购订单成交单价。
- 材料办理角色边界以后端动作为准，前端按钮 `groups` 只用于减少误操作：物资只读不能执行办理动作；物资经办负责提交；物资审批/库管负责人负责验收、入库、出库和结算确认；采购经办负责发起询价；采购审批负责定价和生成采购订单；财务经办/审批继续承接材料结算生成的付款申请。
- 财务角色可以只读材料结算和结算明细以完成付款金额校验，但不能因此获得材料结算提交、确认或生成剩余付款申请等材料域办理动作。
- 跨域办理允许共享入口，但必须补齐 ACL 和 action groups，避免采购用户能看见按钮却读不到采购申请/RFQ，或业务动作完成后被 action 元数据权限阻断打开表单。
- 会写审计用户组或权限缓存的验证脚本必须串行执行；并行运行 Odoo shell 容易在 `res_users` 组更新处产生数据库死锁，不能误判为业务链路失败。

## Next Gates

材料域当前进入后续迭代计划，不再作为当前主线继续深挖。以下事项保留为 backlog、行业模板和交付抽样证据，不阻塞当前转向合同与结算域：

- 将直接采购、询价采购、框架采购的分支选择从按钮能力沉淀到 `sc.business.category` 或分类策略，支持客户维护默认路径。
- 材料结算付款后续策略：将分批、撤销、登记审批等付款策略继续沉淀到 `sc.business.category` 或行业模板默认策略。
- 退库、调拨、损耗后续深化：补来源单据、独立调拨接收确认、跨仓责任策略和损耗责任归集策略。
- 角色权限门禁继续扩展到退库来源确认、调拨接收和损耗责任归集等派生动作。
- 浏览器验收：抽样材料计划、验收、入库、出库、结算五个入口，产出页面级证据。

# 业务事实层与产品需求缺口对比分析

Date: 2026-05-02  
Scope: `项目建设-产品功能清单（0301 ）.xlsx` vs. 当前 Odoo 业务事实层、核心业务模型、原生视图与场景交付层。

## 1. 结论摘要

当前仓库已具备项目、合同、成本、付款、结算、发票、资金、物资、进度计量等基础业务对象，也通过 `sc.business.fact.mixin` 派生了一批轻量业务事实模型用于菜单覆盖和低成本承载。

但对需求清单中的计划管理、质量管理、安全管理、会议督办、移动端闭环、标准库/模板库/版本对比等能力，当前业务事实层仍偏“入口占位”和“通用记录”，不足以支撑实施层的真实业务规则、审批流、证据链、统计分析和移动端协同。

实施建议调整为“通用模型专业化改造路线”：以已经实现的 `sc.business.fact.mixin` 及其派生通用承载模型为资产和源模型，按需求清单把其中的业务类型、字段、状态和视图拆分、改造为专业业务模型。通用模型不再继续扩大承载范围，而应作为迁移来源、兼容层和少量低频事实的兜底层。

## 2. 当前承载证据

主要已存在模型：

- 通用事实层：`sc.business.fact.mixin`、`sc.project.document.fact`、`sc.construction.inspection`、`sc.construction.report`、`sc.fund.operation`、`sc.analysis.report.fact`
- 项目与进度：`project.project` 扩展、`project.task` 扩展、`project.progress.entry`、`project.boq.line`
- 成本：`project.budget`、`project.cost.code`、`project.cost.ledger`、`project.budget.cost.alloc`
- 合同：`construction.contract`、`construction.contract.line`
- 付款结算发票：`payment.request`、`sc.settlement.order`、`sc.invoice.registration`、`sc.payment.execution`
- 资金：`project.funding.baseline`、`sc.fund.account`、`sc.treasury.ledger`、`sc.fund.daily.summary`
- 审批与工作流：`sc.workflow.*`、`sc.approval.policy`、`tier.validation` 相关动作

主要已存在视图/菜单：

- `views/core/*_views.xml` 覆盖项目、合同、成本、付款、结算、资金、物资、进度计量等核心对象。
- `views/core/business_menu_fact_views.xml` 与 `views/menu_business_taxonomy.xml` 用于业务菜单覆盖。
- `smart_construction_scene/providers/*` 提供项目、合同、成本、财务、工作台等场景交付层。

## 3. 需求域覆盖矩阵

| 需求域 | 清单核心能力 | 当前覆盖判断 | 主要缺口 |
| --- | --- | --- | --- |
| 计划管理 | 关键节点计划、主项计划、专项计划、计划模板、Project/Excel 导入导出、版本对比、工作汇报、轨道图、预警、达成率分析 | 部分覆盖 | 当前只有项目任务、进度计量和项目进度指标，缺少计划主表、计划节点、版本、模板、汇报、预警日志、甘特/轨道视图 |
| 成本与合同 | 投资目标、合约规划、合同登记、变更、签证、认质认价、调差、索赔、结算、付款、发票、决算、资金计划 | 中等覆盖 | 合同、预算、付款、结算、发票已有基础；合同履约事件、合约规划、投资目标多版本、决算计划、供方协同仍需独立建模 |
| 质量管理 | 检查标准、随手拍、问题登记整改复验、工序验收、材料验收、巡检评估、实测实量、样板管理、统计分析 | 弱覆盖 | `sc.construction.inspection` 只适合轻量记录；缺少标准库继承、问题闭环、复验、部位/楼栋/房间/道路坐标、照片批次、验收流、统计投影 |
| 安全管理 | 施工方案、安全交底、危险源、风险分级、安全检查巡检、安全学习考试、设备台账、危大工程、安全晨会、考勤 | 弱覆盖 | 安全检查可临时复用通用检查，但缺少安全方案、交底、风险库、危险源、巡检任务、学习考试、设备合规、晨会和资质有效期模型 |
| 会议督办 | 会议室预定、会议日程、会议计划、会议监控、督办任务、跟踪分析 | 未覆盖/弱覆盖 | 当前待办和任务能力不足以表达会议资源、议程、纪要、纪要转任务、督办跟踪和统计 |
| 移动端协同 | APP 进度汇报、照片/语音、问题提醒、整改转发、现场验收、考勤打卡 | 弱覆盖 | 后端业务对象缺少移动采集字段、证据类型、提醒策略、离线/同步状态、移动端场景 contract |
| 标准体系 | 标准节点库、计划模板库、检查标准、合同模板、科目设置、预警强控、数据授权 | 部分覆盖 | 成本科目和审批配置已有基础；计划标准、质量/安全标准继承、模板版本、强控规则、项目级默认人员仍需补齐 |

## 4. 核心结构性缺口

### 4.1 通用事实模型过宽，业务规则表达不足

`sc.business.fact.mixin` 提供了名称、项目、往来单位、日期、金额、状态等通用字段，适合记录低频事实和菜单补位。但需求清单中的核心业务包含版本、模板、层级节点、整改复验、证据链、审批强控、统计口径、移动采集等差异化结构。

因此通用承载模型不应被视为继续扩展的目标层。第一阶段目标是识别已经在通用模型中实现或可复用的字段、状态、动作和视图，把它们按需求清单拆分到专业模型中。通用模型只保留兼容引用、历史记录迁移和低频事实兜底职责。

如果长期把计划、质量、安全、合同履约事件全部压到轻量事实层，会带来以下问题：

- 表单字段泛化，实施现场难以表达真实业务语义。
- 审批前置条件只能写在通用状态动作里，规则会快速膨胀。
- 统计分析缺少稳定口径，后续驾驶舱只能依赖弱结构数据。
- 移动端无法获得明确的采集字段和流程状态。
- 标准库、模板库、版本对比难以落地。

第一阶段应重点完成“通用模型到专业模型”的改造设计：哪些通用模型拆为哪些专业模型，哪些字段复用，哪些字段废弃，哪些记录需要迁移，哪些菜单和场景入口切换到新模型。

### 4.2 计划域缺少“计划-节点-版本-汇报”主干

需求中的关键节点计划、主项计划、专项计划、公司专项计划、组织计划，本质是一个计划体系，而不是普通任务清单。当前项目进度字段和 `project.progress.entry` 只能表达执行结果或进度计量，无法表达：

- 计划类型、分期/标段/专业分类。
- 计划节点层级、依赖、关键路径。
- 模板创建、Excel/Project 导入导出。
- 修订后自动版本化和版本对比。
- 工作汇报、成果文件、批量汇报。
- 计划预警、延误原因、达成率分析。

### 4.3 质量和安全缺少闭环对象

质量与安全需求都围绕“标准-检查/巡检-问题-整改-复验-提醒-统计”闭环。当前 `sc.construction.inspection` 可记录检查和整改，但没有拆出问题单、整改记录、复验记录、标准项、照片批次、提醒策略和超期统计。

这会影响：

- APP 端问题登记和整改复验。
- PC 端批量录入和会议回顾。
- 公司/项目维度整改率、按时整改率。
- 检查标准按集团、公司、项目逐级继承。
- 道路坐标、楼栋房间、建筑类型差异化字段。

### 4.4 合同履约事件模型不足

合同登记、付款、结算、发票已有较完整基础，但清单中大量合同履约事件仍缺少独立模型，包括设计变更、现场签证、认质认价、材料调差、争议索赔、产值申报、付款计划、决算计划。

这些不宜只作为合同备注或通用事实记录，因为它们会影响合同金额、成本归集、付款依据、结算依据和供应商协同。

### 4.5 视图覆盖偏列表/表单，业务工作台视角不足

当前原生视图覆盖较多基础列表和表单，但清单要求的计划轨道图、全景地图、统计分析、问题闭环看板、会议日历、督办跟踪、APP 场景入口仍缺少明确模型视图组合。

实施层需要补齐：

- `search` 视图中的项目、责任人、状态、逾期、风险等级、业务类型分组。
- `kanban` 用于问题闭环、审批待办、督办任务。
- `calendar` 用于会议、计划节点、巡检任务。
- `pivot/graph` 用于整改率、达成率、合同执行、资金计划执行监控。
- `gantt` 或等价场景 contract 用于计划节点和项目轨道。

## 5. 通用模型专业化改造方案

### 5.1 改造原则

通用模型专业化改造不是新增一批完全从零开始的模型，而是把已实现的通用承载模型作为源模型拆解。改造时应遵循：

- 以需求清单中的业务场景为模型边界，而不是以通用 `fact_type` 为边界。
- 复用通用模型中已经稳定的字段、状态按钮、审批接入、附件能力和视图经验。
- 专业模型必须拥有清晰业务语义、稳定状态机、专属字段和统计口径。
- 原通用模型中的历史数据通过 `legacy_fact_id`、`source_fact_model`、`source_fact_id` 等字段保留追溯。
- 原菜单、action、场景 contract 应逐步切换到专业模型，避免长期双轨。

不应继续投入扩大通用承载模型的场景：

- 计划、质量、安全、合同履约、会议督办等高频核心业务。
- 需要子表、版本、层级、闭环、金额联动或移动端采集的业务。
- 需要稳定报表口径和驾驶舱指标的业务。

### 5.2 通用模型到专业模型改造映射

| 当前通用模型 | 当前承载内容 | 建议改造出的专业模型 | 改造重点 |
| --- | --- | --- | --- |
| `sc.project.document.fact` | 安全资料、质量资料、归档资料、成果文件 | `sc.document.library`、`sc.document.template`、`sc.plan.deliverable`、`sc.settlement.archive` | 从“资料事实”改为“资料库/模板/成果”模型；补版本、生效期、适用范围、来源业务对象、附件分类 |
| `sc.construction.inspection` | 质量检查、安全检查、整改记录 | `sc.quality.issue`、`sc.quality.rectification`、`sc.quality.recheck`、`sc.safety.issue`、`sc.safety.rectification`、`sc.safety.recheck` | 从单表检查整改拆为问题、整改、复验闭环；补检查标准项、责任单位、复验人、超期状态、照片证据 |
| `sc.construction.report` | 日报、周报、月报、施工报表 | `sc.project.daily.report`、`sc.work.report`、`sc.safety.morning.meeting`、`sc.meeting.minutes` | 从通用报表拆为项目日报、工作报告、安全晨会、会议纪要；补上报范围、审批人、提交时间、纪要转任务 |
| `sc.workbench.item` | 我的待办、我的审批、最近访问 | 保留为聚合模型，不作为业务主数据；关联 `sc.supervision.task`、`sc.plan.report`、`sc.quality.issue`、`sc.safety.issue` | 从业务承载转为待办索引；待办来源必须指向专业模型 |
| `sc.fund.operation` | 资金计划汇总、资金日报、资金操作 | `sc.funding.plan`、`sc.funding.plan.line`、`sc.funding.execution`、`sc.urgent.payment.approval` | 从资金事实拆为资金计划和执行模型；补计划周期、组织层级、执行率、关联付款 |
| `sc.analysis.report.fact` | 轻量分析快照 | 保留为统计快照/projection；由专业模型生成 | 不再人工承载业务事实；指标来源指向专业模型和统计日期 |
| `sc.equipment.document` | 设备计划、设备申请、设备使用、设备台账 | `sc.equipment.ledger`、`sc.special.equipment.filing`、`sc.equipment.compliance.template`、`sc.equipment.usage` | 从设备单据拆为设备台账、特种设备报备、合规模板、使用记录 |
| `sc.labor.document` | 劳务计划、考勤记录、劳务用工 | `sc.attendance.checkin`、`sc.person.qualification`、`sc.labor.usage`、`sc.duty.fulfillment` | 从劳务事实拆为考勤、人员资质、履职和用工记录 |
| `sc.material.document` | 采购申请、入库、出库、材料结算 | `sc.material.acceptance`、`sc.material.inbound`、`sc.material.outbound`、`sc.material.settlement` | 从物资单据拆为材料验收、出入库和结算；与库存/采购对象建立真实关联 |
| `sc.subcontract.document` | 分包计划、分包登记、分包结算 | `sc.subcontract.plan`、`sc.subcontract.registration`、`sc.subcontract.settlement` | 从分包事实拆为分包业务主数据，关联合同和供应商 |

### 5.3 专业化改造的字段迁移策略

通用模型已有字段应优先迁移到专业模型，避免重复设计：

- `project_id`、`partner_id`、`requester_id`、`handler_id`、`department_id` 迁移为专业模型的组织与责任字段。
- `business_date`、`planned_date`、`due_date` 迁移为业务日期、计划日期、截止日期，并按专业模型补实际完成日期、复验日期、审批日期。
- `quantity`、`uom_id`、`amount`、`tax_amount` 只迁移到确有数量/金额语义的专业模型。
- `state` 不直接照搬，应按专业模型重定义，例如问题闭环需要 `draft/submitted/rectifying/rechecking/closed/cancel`。
- `description`、`result_note` 迁移为业务说明、处理结果、整改说明、复验意见等专业字段。
- 新增 `legacy_fact_model`、`legacy_fact_id`、`legacy_fact_type`，用于追溯来源通用记录。

### 5.4 专业化改造的视图策略

现有通用视图只能作为参考，不应继续作为核心入口。专业模型应建设专属视图：

- 列表视图围绕专业对象主字段，例如问题编号、检查标准、责任单位、整改期限、复验状态。
- 表单视图按业务流程分组，例如检查信息、问题描述、整改要求、整改反馈、复验结论、附件证据。
- 搜索视图按专业维度分组，例如风险等级、问题等级、检查类型、计划类型、会议状态、合同事件类型。
- 看板视图用于闭环状态推进，例如质量问题、安全问题、督办任务。
- pivot/graph 由专业模型或 projection 模型提供，不再依赖通用事实的弱分类。

### 5.5 专业化改造交付物

第一阶段应新增一份机器/人工都可读的改造映射表，建议路径：

- `docs/contract/business_fact_professionalization_mapping_v1.md`
- 可选 JSON：`docs/contract/exports/business_fact_professionalization_mapping.json`

映射字段至少包括：

- 需求 sheet、模块、场景功能。
- 当前通用源模型。
- 当前 `fact_type` 或业务类型。
- 目标专业模型。
- 字段迁移规则。
- 状态迁移规则。
- 原菜单/action XMLID。
- 新菜单/action XMLID。
- 迁移状态：not_started/design_ready/model_ready/view_ready/data_migrated/contract_switched。

## 6. 专业模型目标设计

以下专业模型是第一阶段改造设计的目标，不是遥远的后续补充。实施时可按优先级分批落地，但模型边界应先明确。

### 6.1 计划管理域

建议新增：

- `sc.plan`：计划主表，区分关键节点、主项、专项、公司计划、组织计划。
- `sc.plan.line`：计划节点，支持层级、依赖、责任人、计划/实际日期、完成标准。
- `sc.plan.version`：计划修订版本。
- `sc.plan.template`、`sc.plan.template.line`：计划模板和标准节点库。
- `sc.plan.report`：工作汇报、批量汇报、成果附件。
- `sc.plan.warning.log`：逾期、即将逾期、风险预警。
- `sc.delay.reason`：延误原因标准字典。

必要视图：

- 计划清单、计划表单、节点树、节点甘特/轨道、版本对比、我的汇报、项目汇报、计划达成率分析。

### 6.2 合同履约与成本事件域

建议新增：

- `sc.contract.change`：设计变更。
- `sc.site.instruction`：现场签证。
- `sc.material.price.adjustment`：材料调差。
- `sc.quality.price.approval`：认质认价。
- `sc.contract.claim`：争议索赔。
- `sc.output.value.report`：产值申报。
- `sc.payment.plan`：付款计划。
- `sc.final.account`、`sc.final.account.plan`：决算审核与计划。
- `sc.contract.plan`：合约规划，可关联成本科目和合同模板。
- `sc.investment.target`、`sc.investment.target.version`：投资目标及多版本测算。

必要视图：

- 合同履约事件台账、合同执行分析、成本动态监控、付款计划执行、决算资料库、供方协同入口。

### 6.3 质量管理域

建议新增：

- `sc.check.standard`、`sc.check.standard.item`：检查标准与标准项，支持集团/公司/项目继承。
- `sc.quality.issue`：质量问题单。
- `sc.quality.rectification`：整改记录。
- `sc.quality.recheck`：复验记录。
- `sc.site.photo`、`sc.site.photo.batch`：随手拍、云相册和批量录入。
- `sc.process.acceptance`：工序报验/验收。
- `sc.material.acceptance`：材料进场验收。
- `sc.measurement.record`：实测实量。
- `sc.sample.acceptance`：样板点评与验收。

必要视图：

- 检查标准库、问题闭环看板、整改复验列表、照片批次、工序验收明细、实测统计、材料报告统计。

### 6.4 安全管理域

建议新增：

- `sc.safety.plan`：施工方案、危大方案、环保、防疫等前置方案。
- `sc.safety.disclosure`：安全交底，关联施工方案。
- `sc.risk.library`、`sc.risk.item`：企业风险库和风险分级。
- `sc.hazard.source`：项目危险源清单。
- `sc.safety.issue`：安全问题闭环。
- `sc.safety.patrol.template`、`sc.safety.patrol.task`：安全巡检模板与任务。
- `sc.safety.training.content`、`sc.safety.question`、`sc.safety.exam`：学习、题库、考试。
- `sc.special.equipment`：特种设备报备与设备台账。
- `sc.safety.morning.meeting`：安全晨会。
- `sc.attendance.checkin`：考勤打卡。

必要视图：

- 履职一张图、风险库、危险源清单、安全问题闭环、安全巡检任务、考试统计、设备合规台账、晨会记录。

### 6.5 会议督办域

建议新增：

- `sc.meeting.room`：会议室。
- `sc.meeting`：会议日程/会议计划。
- `sc.meeting.agenda`：会议议程。
- `sc.meeting.minutes`：会议纪要。
- `sc.supervision.task`：督办任务。
- `sc.supervision.followup`：督办跟踪记录。

必要视图：

- 会议日历、会议室预定、会议纪要转任务、我的督办、督办跟踪看板、督办完成率分析。

## 7. 横切能力要求

新增核心域模型时应统一接入以下横切能力：

- 审批：复用 `sc.workflow.*`、`sc.approval.policy` 或 `tier.validation`，避免每个模型自建审批。
- 附件：统一使用 `ir.attachment`，并区分照片、文档、语音、导入文件、成果文件。
- 消息与待办：接入 `mail.thread`、`mail.activity.mixin`、`sc.workbench.item` 或现有待办聚合服务。
- 项目范围授权：所有项目级单据必须具备 `project_id`，并遵循项目/公司/部门权限边界。
- 状态机：统一草稿、审批中、执行中、待整改、待复验、已完成、已取消等状态命名口径。
- 统计投影：整改率、达成率、合同执行、资金计划执行等高频报表建议建设 projection 模型，而不是实时扫业务明细。
- 导入导出：计划、检查标准、模板库、产值申报等需预留 Excel/Project 导入导出 wizard。
- 场景 contract：新增模型后同步维护 `smart_construction_scene` provider、capability mapping、菜单目标和前端场景。

## 8. 分阶段落地建议

### P0：通用模型专业化改造设计

- 建立通用源模型到专业目标模型的映射文档/JSON。
- 明确每个通用模型的去向：保留为聚合/快照、拆为专业模型、废弃、或仅作历史兼容。
- 明确字段迁移规则、状态迁移规则、菜单/action 切换规则、场景 contract 切换规则。
- 确定第一批专业模型边界：计划、质量问题闭环、安全问题闭环、合同履约事件。
- 禁止继续通过新增 `fact_type` 扩大通用模型对核心业务的承载。

### P1：落地第一批专业模型

- 建立计划域最小主干：`sc.plan`、`sc.plan.line`、`sc.plan.version`、`sc.plan.report`。
- 建立质量/安全问题闭环主干：标准、问题、整改、复验、照片证据。
- 建立合同履约事件主干：变更、签证、认质认价、调差、索赔、产值申报。
- 为第一批专业模型补 `tree/form/search/kanban`、状态按钮、ACL、菜单和审批接入。
- 将原通用模型中的相关记录通过 `legacy_fact_*` 字段迁移或关联到专业模型。

### P2：切换入口与统计口径

- 计划模板库、标准节点库、版本对比、导入导出。
- 检查标准继承、项目默认复验人/抄送人、提醒日志。
- 合同执行分析、成本动态监控、付款计划执行监控投影。
- 移动端采集字段和 APP 场景 contract。
- 将原菜单/action/scene provider 从通用模型切换到专业模型。
- 将 `sc.analysis.report.fact` 改为由专业模型生成的统计快照，而不是人工录入事实。

### P3：补扩展业务

- 会议督办完整域。
- 安全学习、题库、考试。
- 特种设备、资质有效期、危大工程强控。
- 组织计划考核、自动考核、人工考核确认。

## 9. 实施风险

- 若继续通过新增 `fact_type` 扩大通用模型，短期看似覆盖更快，但会固化弱语义模型，后续审批、统计、移动端和二开都会返工。
- 若专业化改造不保留 `legacy_fact_*` 追溯关系，会导致已有通用记录与新模型之间断链。
- 若入口切换不完整，会出现同一业务既能从通用模型创建、又能从专业模型创建的双轨数据。
- 若一次性全量建模，范围过大，容易拖慢交付。建议按 P0 设计、P1 第一批核心模型、P2 入口统计切换逐步推进。
- 新增模型必须同步补 ACL、菜单、场景 provider 和 contract，否则会出现后端模型存在但前端/菜单无法稳定使用的断层。

## 10. 最小验收标准

通用模型专业化改造设计阶段至少满足：

- 每个当前通用模型有明确去向：保留、拆分、迁移、废弃或兼容。
- 每个需求场景功能有明确目标专业模型。
- 每个目标专业模型有字段迁移、状态迁移、菜单/action 切换和 contract 切换说明。
- 核心业务不得仅以新增 `fact_type` 作为最终交付。
- 数据迁移保留 `legacy_fact_model`、`legacy_fact_id`、`legacy_fact_type` 等追溯字段。

每个新增核心业务域至少满足：

- 有明确模型、状态机、项目关联、责任人和附件证据。
- 有 `tree/form/search` 视图和至少一个业务入口菜单。
- 有提交、审批/确认、完成、取消等核心动作。
- 有基础权限矩阵和项目范围过滤。
- 有最小统计口径或后续 projection 设计。
- 有与需求清单条目的可追溯映射。

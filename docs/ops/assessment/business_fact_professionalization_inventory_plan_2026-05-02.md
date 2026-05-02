# 通用业务模型专业化改造清单与计划

Date: 2026-05-02  
Scope: 基于 `项目建设-产品功能清单（0301 ）.xlsx`，对当前 `sc.business.fact.mixin` 及其派生通用模型进行专业化改造规划。

## 1. 判断

当前通用模型显然不满足业务需求，原因不是字段数量不够，而是模型边界不对。

`sc.business.fact.mixin` 及派生模型适合做低频事实、菜单补位、历史迁移缓冲；但产品清单要求的是计划、合同履约、质量闭环、安全闭环、会议督办、移动端采集和统计分析。这些业务有独立状态机、子表、版本、审批、证据链和统计口径，不能继续依赖 `fact_type` 加通用字段承载。

本计划的目标是：把已经实现的通用模型作为源资产，按需求改造为专业模型；通用模型只保留兼容、聚合、历史追溯和少量低频事实用途。

## 2. 当前通用模型清单

| 当前模型 | 当前定位 | 当前主要问题 | 改造结论 |
| --- | --- | --- | --- |
| `sc.business.fact.mixin` | 通用事实基类 | 字段过宽、状态过粗、无法表达专业流程 | 保留为低频事实基类，不再作为核心业务主模型 |
| `sc.dashboard.cockpit.fact` | 驾驶舱事实 | 手工事实口径弱，缺少业务来源稳定性 | 改为 projection/指标快照，指标来源指向专业模型 |
| `sc.workbench.item` | 工作台事项 | 不应承载业务主数据 | 保留为待办/入口聚合索引 |
| `sc.project.budget.fact` | 项目预算事实 | 已与 `project.budget`、成本科目体系重叠 | 迁移到预算/目标成本专业模型或废弃 |
| `sc.project.document.fact` | 施工资料事实 | 无资料库、模板、版本、生效范围 | 拆为资料库、模板库、成果/归档模型 |
| `sc.material.document` | 物资业务单据 | 与采购、库存、材料验收、材料结算边界混杂 | 拆为材料验收、入库、出库、结算、询价模型 |
| `sc.labor.document` | 劳务业务单据 | 考勤、资质、用工、结算混在一张表 | 拆为考勤、人员资质、劳务用工、劳务结算 |
| `sc.equipment.document` | 设备业务单据 | 设备台账、使用、合规、结算混杂 | 拆为设备台账、特种设备报备、合规模板、使用记录 |
| `sc.subcontract.document` | 分包业务单据 | 分包计划、登记、结算需要合约关系 | 拆为分包计划、分包登记、分包结算 |
| `sc.construction.inspection` | 施工检查整改 | 无标准项、问题单、整改单、复验单、照片批次 | 拆为质量闭环和安全闭环专业模型 |
| `sc.construction.report` | 施工报表 | 日报、工作报告、安全晨会、会议纪要语义不同 | 拆为项目日报、工作报告、安全晨会、会议纪要 |
| `sc.finance.expense.document` | 费用扩展单据 | 与现有 `sc.expense.claim`、付款模型重叠 | 合并到费用/付款专业模型，保留迁移映射 |
| `sc.fund.operation` | 资金账户操作 | 资金计划、资金日报、资金调拨混杂 | 拆为资金计划、执行、调拨、紧急付款呈批 |
| `sc.analysis.report.fact` | 分析报表事实 | 不应手工录入业务事实 | 保留为由专业模型生成的统计快照 |

## 3. 专业模型改造清单

### 3.1 计划管理

需求覆盖：

- 关键节点计划、项目主项计划、项目专项计划、公司专项计划。
- 我的工作汇报、项目工作汇报、工作报告收发。
- 项目全景地图、轨道图、形象进度监控、计划监控。
- 达成率、完成情况、标准工期、延误原因、统计报表。
- 标准节点库、计划模板库、工作预警日志。

当前问题：

- 当前只有 `project.task`、`project.progress.entry` 和项目进度字段，无法表达计划版本、节点层级、模板、汇报和预警。
- 不能用 `sc.construction.report` 替代计划汇报，因为计划汇报需要绑定计划节点、成果文件和完成标准。

目标模型：

| 目标模型 | 来源/复用 | 说明 |
| --- | --- | --- |
| `sc.plan` | 新建，复用通用模型日期/项目/责任字段 | 计划主表，区分关键节点、主项、专项、公司、组织计划 |
| `sc.plan.line` | 新建 | 计划节点，支持父子层级、前后置关系、责任人、计划/实际日期 |
| `sc.plan.version` | 新建 | 每次修订生成版本，支持版本对比 |
| `sc.plan.template`、`sc.plan.template.line` | 从 `sc.project.document.fact` 的模板类资料改造 | 计划模板库、标准节点库 |
| `sc.plan.report` | 从 `sc.construction.report` 中工作汇报语义拆出 | 绑定计划节点的工作汇报、批量汇报、成果文件 |
| `sc.plan.warning.log` | 新建 | 计划逾期、即将逾期、风险预警 |
| `sc.delay.reason` | 可复用 `sc.dictionary` | 延误原因标准字典 |

第一批视图：

- 计划清单、计划表单、计划节点树、我的计划汇报、项目计划汇报、计划预警日志。

### 3.2 合同履约与成本事件

需求覆盖：

- 投资目标、合约规划、成本归集、成本分摊。
- 事项呈批、合同登记、设计变更、现场签证、认质认价、材料调差、争议索赔。
- 结算计划、合同结算、合同台账、合同执行分析。
- 产值申报、付款计划、付款申请、发票、付款登记、收款登记、扣款管理。
- 决算计划、决算审核、决算资料库。

当前问题：

- 已有 `construction.contract`、`project.budget`、`payment.request`、`sc.settlement.order`、`sc.invoice.registration`，但合同履约事件缺模型。
- 不能把变更、签证、调差、索赔放入通用事实，因为它们会影响合同额、成本、结算和付款依据。

目标模型：

| 目标模型 | 来源/复用 | 说明 |
| --- | --- | --- |
| `sc.contract.plan` | 新建，关联 `project.cost.code` | 合约规划，指导合同订立 |
| `sc.investment.target`、`sc.investment.target.version` | 从 `sc.project.budget.fact` 专业化 | 投资目标和多版本测算 |
| `sc.contract.change` | 新建 | 设计变更 |
| `sc.site.instruction` | 新建 | 现场签证 |
| `sc.quality.price.approval` | 新建 | 认质认价 |
| `sc.material.price.adjustment` | 新建 | 材料调差 |
| `sc.contract.claim` | 新建 | 争议索赔 |
| `sc.output.value.report` | 新建 | 产值申报 |
| `sc.payment.plan` | 新建，关联 `payment.request` | 付款计划 |
| `sc.final.account`、`sc.final.account.plan` | 从 `sc.project.document.fact` 的决算资料语义拆出 | 决算计划、审核和资料库 |

第一批视图：

- 合同履约事件台账、合同变更/签证/索赔表单、产值申报、付款计划、合同执行分析。

### 3.3 质量管理

需求覆盖：

- 检查标准、随手拍与云相册、问题登记闭环、问题提醒、问题统计分析。
- 工序管理、验收留痕、材料进场验收、巡检评估、实测实量、样板管理。

当前问题：

- `sc.construction.inspection` 把检查和整改放在一张表里，没有问题、整改、复验的独立生命周期。
- 缺少检查标准项、默认复验人、抄送人、照片批次、楼栋房间/道路坐标、统计口径。

目标模型：

| 目标模型 | 来源/复用 | 说明 |
| --- | --- | --- |
| `sc.check.standard`、`sc.check.standard.item` | 新建 | 检查标准，支持集团/公司/项目继承 |
| `sc.quality.issue` | 从 `sc.construction.inspection` 的 `quality_check` 专业化 | 质量问题单 |
| `sc.quality.rectification` | 从 `sc.construction.inspection` 的整改字段拆出 | 整改记录 |
| `sc.quality.recheck` | 新建 | 复验记录 |
| `sc.site.photo.batch`、`sc.site.photo` | 新建，关联附件 | 随手拍、云相册、批量录入 |
| `sc.process.acceptance` | 新建 | 工序报验、监理验收、甲方抽验 |
| `sc.material.acceptance` | 从 `sc.material.document` 专业化 | 材料进场验收 |
| `sc.measurement.record` | 新建 | 实测实量 |
| `sc.sample.acceptance` | 新建 | 样板点评与验收 |

第一批视图：

- 检查标准库、质量问题闭环看板、整改复验列表、照片批次、工序验收明细、质量统计分析。

### 3.4 安全管理

需求覆盖：

- 施工方案、安全交底、风险分级管控、危险源清单。
- 安全检查、安全巡检、安全学习、题库、在线考试、安全培训。
- 设备台账、设备分类、危大工程、特种设备报备、安全晨会、项目日报、考勤打卡。

当前问题：

- 安全检查不能长期复用 `sc.construction.inspection`。
- 施工方案、交底、危险源、培训考试、设备合规、晨会和考勤都有独立对象和状态。

目标模型：

| 目标模型 | 来源/复用 | 说明 |
| --- | --- | --- |
| `sc.safety.plan` | 从 `sc.project.document.fact` 的安全资料专业化 | 施工方案、危大方案、环保、防疫等 |
| `sc.safety.disclosure` | 新建 | 安全交底，关联施工方案 |
| `sc.risk.library`、`sc.risk.item` | 新建 | 企业风险库和风险分级 |
| `sc.hazard.source` | 新建 | 项目危险源清单 |
| `sc.safety.issue`、`sc.safety.rectification`、`sc.safety.recheck` | 从 `sc.construction.inspection` 安全语义专业化 | 安全问题闭环 |
| `sc.safety.patrol.template`、`sc.safety.patrol.task` | 新建 | 巡检模板和任务 |
| `sc.safety.training.content`、`sc.safety.question`、`sc.safety.exam` | 新建 | 学习、题库、考试 |
| `sc.equipment.ledger`、`sc.special.equipment.filing` | 从 `sc.equipment.document` 专业化 | 设备台账、特种设备报备 |
| `sc.safety.morning.meeting` | 从 `sc.construction.report` 专业化 | 安全晨会 |
| `sc.attendance.checkin` | 从 `sc.labor.document` 的考勤记录专业化 | 考勤打卡 |

第一批视图：

- 施工方案、安全交底、危险源清单、安全问题闭环、安全巡检任务、设备台账、安全晨会。

### 3.5 会议督办

需求覆盖：

- 会议室预定、会议日程、会议计划、会议监控、会议分析、会议设置。
- 我的任务、督办任务跟踪、督办任务分析。

当前问题：

- `sc.workbench.item` 只能做待办索引，不能承载会议和督办主数据。
- `sc.construction.report` 不能替代会议纪要，因为缺少参会人、议题、决议、转任务和跟踪。

目标模型：

| 目标模型 | 来源/复用 | 说明 |
| --- | --- | --- |
| `sc.meeting.room` | 新建 | 会议室资源 |
| `sc.meeting` | 新建 | 会议日程、会议计划 |
| `sc.meeting.agenda` | 新建 | 会议议题 |
| `sc.meeting.minutes` | 从 `sc.construction.report` 会议语义专业化 | 会议纪要 |
| `sc.supervision.task` | 新建，生成 `sc.workbench.item` 待办 | 督办任务 |
| `sc.supervision.followup` | 新建 | 督办跟踪记录 |

第一批视图：

- 会议日历、会议室预定、会议纪要、纪要转任务、督办看板、督办分析。

## 4. 改造实施计划

### P0：专业化设计清单

交付物：

- `business_fact_professionalization_mapping_v1.md`
- `business_fact_professionalization_mapping.json`
- 第一批专业模型 ER 草图：计划、质量、安全、合同履约事件。
- 原通用模型去向表：保留、拆分、迁移、废弃、兼容。

验收：

- 每个当前通用模型都有明确去向。
- 每个需求模块至少有目标专业模型。
- 不再以新增 `fact_type` 作为核心业务交付方式。

### P1：第一批专业模型落地

优先级：

1. 质量/安全问题闭环：因为现场业务高频，且通用模型差距最大。
2. 计划主干：因为计划版本、节点、汇报是管理中枢。
3. 合同履约事件：因为会影响成本、付款、结算和供应商协同。

交付物：

- Python 模型、ACL、菜单、基础视图。
- 状态动作：提交、审批/确认、整改、复验、关闭、取消。
- `legacy_fact_model`、`legacy_fact_id`、`legacy_fact_type` 追溯字段。
- 第一批数据迁移脚本或迁移 wizard。

### P2：入口切换与统计投影

交付物：

- 原通用模型菜单切换到专业模型。
- `smart_construction_scene` provider 切换到专业模型。
- `sc.analysis.report.fact` 改为由专业模型生成统计快照。
- 质量整改率、安全闭环率、计划达成率、合同执行分析等 projection。

### P3：扩展域补齐

交付物：

- 会议督办完整域。
- 安全学习、题库、考试、培训。
- 特种设备合规、人员资质、危大工程强控。
- 组织计划与考核。

## 5. 第一批建议工作包

| 工作包 | 范围 | 文件建议 | 说明 |
| --- | --- | --- | --- |
| WP1 质量闭环 | `sc.check.standard`、`sc.quality.issue`、`sc.quality.rectification`、`sc.quality.recheck`、照片批次 | `models/core/quality_management.py`、`views/core/quality_management_views.xml` | 从 `sc.construction.inspection` 拆出质量语义 |
| WP2 安全闭环 | `sc.safety.plan`、`sc.safety.disclosure`、`sc.hazard.source`、`sc.safety.issue`、`sc.safety.rectification`、`sc.safety.recheck` | `models/core/safety_management.py`、`views/core/safety_management_views.xml` | 从安全资料和安全检查通用模型拆出 |
| WP3 计划主干 | `sc.plan`、`sc.plan.line`、`sc.plan.version`、`sc.plan.report`、`sc.plan.warning.log` | `models/core/plan_management.py`、`views/core/plan_management_views.xml` | 替代任务/报表对计划需求的弱承载 |
| WP4 合同履约事件 | 变更、签证、认质认价、调差、索赔、产值申报 | `models/core/contract_event.py`、`views/core/contract_event_views.xml` | 关联 `construction.contract`、`project.cost.code`、结算/付款 |
| WP5 映射与迁移 | 通用源模型到专业模型的映射、迁移 wizard | `docs/contract/*`、`wizard/*professionalization*` | 保证历史数据和菜单入口不断链 |
| WP6 材料采购/验收/询比价/出入库/结算/价格 | `sc.material.purchase.request`、`sc.material.purchase.request.line`、`sc.material.acceptance`、`sc.material.acceptance.line`、`sc.material.rfq`、`sc.material.rfq.line`、`sc.material.inbound`、`sc.material.inbound.line`、`sc.material.outbound`、`sc.material.outbound.line`、`sc.material.settlement`、`sc.material.settlement.line`、`sc.material.price` | `models/core/material_acceptance.py`、`models/core/material_catalog.py`、`views/core/material_acceptance_views.xml`、`views/support/product_extend_views.xml` | 从 `sc.material.document(purchase_request/rfq/inbound/outbound/settlement)` 拆出采购申请、询比价、到场验收、库存入库、库存出库、材料结算专业动作；材料价格库独立于材料档案/产品库，现有“采购申请/询比价/入库单/出库单/材料结算/材料价格库”入口只承载对应动作 |
| WP7 劳务考勤 | `sc.attendance.checkin` | `models/core/labor_management.py`、`views/core/labor_management_views.xml` | 从 `sc.labor.document(attendance_record)` 拆出考勤记录专业动作；现有“考勤记录”入口只承载班组、出勤人数、工时和作业内容，不再混入劳务计划、用工或结算 |
| WP8 劳务用工 | `sc.labor.usage` | `models/core/labor_management.py`、`views/core/labor_management_views.xml` | 从 `sc.labor.document(labor_employment)` 拆出劳务用工专业动作；现有“劳务用工”入口只承载实际用工发生、班组、劳务单位、人数和工时，不再混入考勤或结算 |
| WP9 劳务结算 | `sc.labor.settlement`、`sc.labor.settlement.line` | `models/core/labor_management.py`、`views/core/labor_management_views.xml` | 从 `sc.labor.document(labor_settlement)` 拆出劳务结算专业动作；现有“劳务结算”入口只承载劳务单位、结算日期、结算明细和金额确认，不再混入考勤或用工登记 |
| WP10 劳务申请 | `sc.labor.request`、`sc.labor.request.line` | `models/core/labor_management.py`、`views/core/labor_management_views.xml` | 从 `sc.labor.document(labor_request)` 拆出劳务申请专业动作；现有“劳务申请”入口只承载劳务需求发起、需用日期和申请明细，不再混入实际用工或结算 |
| WP11 劳务计划 | `sc.labor.plan`、`sc.labor.plan.line` | `models/core/labor_management.py`、`views/core/labor_management_views.xml` | 从 `sc.labor.document(labor_plan)` 拆出劳务计划专业动作；现有“劳务计划”入口只承载计划周期、负责人、计划人数和计划工时，不再混入申请、实际用工、考勤或结算 |
| WP12 劳务价格库 | `sc.labor.price` | `models/core/labor_management.py`、`views/core/labor_management_views.xml` | 从 `sc.labor.document(labor_price_library)` 拆出劳务价格标准；现有“劳务价格库”入口只维护班组、作业内容、计价单位、单价、税率和生效期，不再混入劳务计划、用工或结算单据 |
| WP13 设备计划 | `sc.equipment.plan`、`sc.equipment.plan.line` | `models/core/equipment_management.py`、`views/core/equipment_management_views.xml` | 从 `sc.equipment.document(equipment_plan)` 拆出设备计划专业动作；现有“设备计划”入口只承载计划周期、使用地点、计划设备、计划台时和负责人，不再混入设备申请、实际使用、结算或价格库 |
| WP14 设备申请 | `sc.equipment.request`、`sc.equipment.request.line` | `models/core/equipment_management.py`、`views/core/equipment_management_views.xml` | 从 `sc.equipment.document(equipment_request)` 拆出设备申请专业动作；现有“设备申请”入口只承载需求发起、需用日期、申请设备、申请台数和预计台时，不再混入设备计划执行、使用登记、结算或价格库 |
| WP15 设备使用登记 | `sc.equipment.usage` | `models/core/equipment_management.py`、`views/core/equipment_management_views.xml` | 从 `sc.equipment.document(equipment_usage)` 拆出设备实际使用专业动作；现有“设备使用登记”入口只承载使用日期、设备、地点、操作人员、使用台数和台时，不再混入设备计划、申请、结算或价格库 |
| WP16 设备结算 | `sc.equipment.settlement`、`sc.equipment.settlement.line` | `models/core/equipment_management.py`、`views/core/equipment_management_views.xml` | 从 `sc.equipment.document(equipment_settlement)` 拆出设备结算专业动作；现有“设备结算”入口只承载供应单位、结算日期、结算明细和金额确认，不再混入设备计划、申请、使用登记或价格库 |
| WP17 设备价格库 | `sc.equipment.price` | `models/core/equipment_management.py`、`views/core/equipment_management_views.xml` | 从 `sc.equipment.document(equipment_price_library)` 拆出设备价格标准；现有“设备价格库”入口只维护设备、供应单位、计价单位、单价、税率和生效期，不再混入设备计划、申请、使用登记或结算单据 |

## 6. 不再建议投入的方向

- 不建议继续给 `sc.business.fact.mixin` 增加大量跨域字段。
- 不建议继续通过 `fact_type` 增加计划、质量、安全、合同履约的核心功能。
- 不建议继续把质量/安全问题闭环放在 `sc.construction.inspection` 单表中。
- 不建议让 `sc.workbench.item` 承载督办业务主数据，它只应索引专业模型待办。
- 不建议让 `sc.analysis.report.fact` 人工承载业务事实，它应是专业模型汇总后的统计快照。

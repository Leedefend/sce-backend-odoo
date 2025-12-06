# 基线梳理：模型与蓝图字段对齐（Phase 0）

分支：feat/cost-kpi-core（示例）  
标签：phase-0, doc, backend/model, p0

## 模块-文档映射

- `project_core.py` ↔ 项目主表 / 阶段 / KPI 基础指标
- `boq.py` ↔ 工程量清单 & 五大清单
- `project_structure_views.xml` + `project_core.py` ↔ WBS / 工程结构
- `cost_domain.py` ↔ 预算
- `project_core.py` (`project.cost.ledger` part) ↔ 成本台账 / 科目
- `project_core.py` (`project.progress.entry`) ↔ 进度 / 计量记录
- 未见实现：变更/签证/结算/计量行/五算字段等（后续阶段补）

## 字段对齐表

| 模块/模型 | 字段 | 状态 | 备注 |
| --- | --- | --- | --- |
| project.project | project_code | 已实现 | 唯一约束，新增随机兜底生成；符合蓝图“项目编号唯一” |
| project.project | lifecycle_state | 已实现 | 阶段枚举：立项/在建/停工/竣工/结算中/保修/关闭，口径一致 |
| project.project | budget_total / cost_committed / cost_actual | 已实现 | 预算/承诺/实际成本字段，口径需与蓝图成本闭环确认 |
| project.project | progress_rate_latest | 已实现 | 取计量记录最大进度；后续需调整为基于计量产值的“产值进度” |
| project.project | dashboard_* | 已实现 | 收入/成本/毛利/开票/收付申请/资料/进度；口径需按第20章统一 |
| sc.project.structure | structure_type / biz_scope | 已实现 | WBS 层级+业务范畴；符合蓝图树形索引 |
| sc.project.structure | qty_total / amount_total | 已实现 | 清单汇总；后续需扩展五算/成本/产值/结算汇总 |
| project.boq.line | code/name/quantity/price/amount | 已实现 | 清单核心字段；amount compute |
| project.boq.line | section_type / boq_category / division_name 等 | 已实现 | 清单分类、分部名称、来源等；符合清单分类规范 |
| project.boq.line | 五算字段 | 缺失 | 需新增 estimate/budget/postbid/contract/final qty/price/amount |
| project.budget (+line) | 预算字段 | 已实现 | 目标收入/成本、版本、is_active；与 BOQ 一一对应 |
| project.progress.entry | progress_rate/amount_* | 已实现 | 计量批次；缺少计量行模型（progress.line）与 BOQ/WBS 绑定 |
| project.cost.ledger | amount/amount_total/amount_tax + structure_id/boq_line_id | 已实现 | 台账挂接 WBS/BOQ/合同/科目；满足台账要求 |
| project.cost.ledger | direction/state/tag | 已实现 | 成本发生/冲减；状态；标签；符合蓝图 |
| 变更/签证/结算 | 模型缺失 | 缺失 | 需新增 sc.change.order / sc.work.visa / sc.settlement 等 |
| 合同行（收入/成本/采购） | 模型缺失 | 缺失 | 需统一 contract line 模型，挂 WBS/BOQ |

## 差异总结

- 需新增：五算字段、计量行、变更/签证/结算、统一合同行、集团/项目健康指标（PHI/CFI/CVR/CER）。  
- 需校准口径：dashboard 指标计算、成本闭环（预算/承诺/动态/实际/结算）、进度口径改为产值驱动。  
- 需扩展汇总：WBS 汇总五算/成本/产值/结算，SSOT/DRM 原则写入代码或校验。  

验收：本文件与蓝图无明显冲突，完成现有模型与蓝图字段的对齐罗列，为后续阶段补齐提供清单。***

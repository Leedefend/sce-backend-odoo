# 业务表单结构统一优先级清单

## 摘要

- 运行态业务模型默认表单：172
- P0 可先做契约默认页签：51
- P0 已可作为基线样本：24
- P1 需补语义标注：40
- P2 需补 XML 主结构：0
- P3 legacy 承载低优先级：34
- P3 平台配置低优先级：13
- P4 wizard/setup 暂不纳入业务统一：10

## 执行顺序

1. `P0_contract_default_tabs`：不改业务事实视图，先在契约标准化层为这批表单生成项目式默认页签。
2. `P1_semantic_annotation`：补少量 group/page 标题或 `data-sc-anchor`，再进入同一标准化器。
3. `P2_xml_structure`：只对正式业务单据补最小 `sheet/group` 骨架；wizard/setup 不进入主线。
4. `P3`：legacy 承载和平台配置先保持低优先级，除非它们是当前业务验收入口。

## P0 契约默认页签队列

| domain_group | model | classification | structural_score | gaps |
| --- | --- | --- | --- | --- |
| finance | payment.ledger | contract_auto_with_default_tabs | 7 | missing_labelled_group;missing_notebook;missing_page;missing_labelled_page;missing_statusbar;missing_button_box;missing_chatter |
| finance | payment.request | contract_auto_with_default_tabs | 10 | missing_notebook;missing_page;missing_labelled_page;missing_chatter |
| finance | payment.request.line | contract_auto_with_default_tabs | 9 | missing_notebook;missing_page;missing_labelled_page;missing_statusbar;missing_chatter |
| material | sc.material.catalog | contract_auto_with_default_tabs | 8 | missing_notebook;missing_page;missing_labelled_page;missing_statusbar;missing_button_box;missing_chatter |
| material | sc.material.price | contract_auto_with_default_tabs | 8 | missing_notebook;missing_page;missing_labelled_page;missing_statusbar;missing_button_box;missing_chatter |
| material | sc.material.stock.summary | contract_auto_with_default_tabs | 8 | missing_notebook;missing_page;missing_labelled_page;missing_statusbar;missing_button_box;missing_chatter |
| project | project.budget.cost.alloc | contract_auto_with_default_tabs | 7 | missing_labelled_group;missing_notebook;missing_page;missing_labelled_page;missing_statusbar;missing_button_box;missing_chatter |
| project | project.cost.code | contract_auto_with_default_tabs | 7 | missing_labelled_group;missing_notebook;missing_page;missing_labelled_page;missing_statusbar;missing_button_box;missing_chatter |
| project | project.cost.ledger | contract_auto_with_default_tabs | 7 | missing_labelled_group;missing_notebook;missing_page;missing_labelled_page;missing_statusbar;missing_button_box;missing_chatter |
| project | project.funding.baseline | contract_auto_with_default_tabs | 7 | missing_labelled_group;missing_notebook;missing_page;missing_labelled_page;missing_statusbar;missing_button_box;missing_chatter |
| project | project.milestone | contract_auto_with_default_tabs | 8 | missing_labelled_group;missing_notebook;missing_page;missing_labelled_page;missing_statusbar;missing_chatter |
| project | project.profit.compare | contract_auto_with_default_tabs | 8 | missing_notebook;missing_page;missing_labelled_page;missing_statusbar;missing_button_box;missing_chatter |
| project | project.progress.entry | contract_auto_with_default_tabs | 7 | missing_labelled_group;missing_notebook;missing_page;missing_labelled_page;missing_statusbar;missing_button_box;missing_chatter |
| project | project.project.stage | contract_auto_with_default_tabs | 7 | missing_labelled_group;missing_notebook;missing_page;missing_labelled_page;missing_statusbar;missing_button_box;missing_chatter |
| project | project.tags | contract_auto_with_default_tabs | 7 | missing_labelled_group;missing_notebook;missing_page;missing_labelled_page;missing_statusbar;missing_button_box;missing_chatter |
| project | project.task.type | contract_auto_with_default_tabs | 7 | missing_labelled_group;missing_notebook;missing_page;missing_labelled_page;missing_statusbar;missing_button_box;missing_chatter |
| safety | sc.safety.patrol.task | contract_auto_with_default_tabs | 7 | missing_labelled_group;missing_notebook;missing_page;missing_labelled_page;missing_statusbar;missing_button_box;missing_chatter |
| sc_other | sc.account.income.expense.summary | contract_auto_with_default_tabs | 8 | missing_notebook;missing_page;missing_labelled_page;missing_statusbar;missing_button_box;missing_chatter |
| sc_other | sc.approval.scope | contract_auto_with_default_tabs | 8 | missing_notebook;missing_page;missing_labelled_page;missing_statusbar;missing_button_box;missing_chatter |
| sc_other | sc.check.standard | contract_auto_with_default_tabs | 8 | missing_notebook;missing_page;missing_labelled_page;missing_statusbar;missing_button_box;missing_chatter |
| sc_other | sc.check.standard.item | contract_auto_with_default_tabs | 7 | missing_labelled_group;missing_notebook;missing_page;missing_labelled_page;missing_statusbar;missing_button_box;missing_chatter |
| sc_other | sc.company.operation.summary | contract_auto_with_default_tabs | 8 | missing_notebook;missing_page;missing_labelled_page;missing_statusbar;missing_button_box;missing_chatter |
| sc_other | sc.comprehensive.cost.summary | contract_auto_with_default_tabs | 8 | missing_notebook;missing_page;missing_labelled_page;missing_statusbar;missing_button_box;missing_chatter |
| sc_other | sc.construction.diary | contract_auto_with_default_tabs | 9 | missing_notebook;missing_page;missing_labelled_page;missing_button_box;missing_chatter |
| sc_other | sc.dashboard.cockpit.fact | contract_auto_with_default_tabs | 9 | missing_notebook;missing_page;missing_labelled_page;missing_button_box;missing_chatter |
| sc_other | sc.dictionary | contract_auto_with_default_tabs | 7 | missing_labelled_group;missing_notebook;missing_page;missing_labelled_page;missing_statusbar;missing_button_box;missing_chatter |
| sc_other | sc.expense.claim | contract_auto_with_default_tabs | 9 | missing_notebook;missing_page;missing_labelled_page;missing_button_box;missing_chatter |
| sc_other | sc.expense.reimbursement.summary | contract_auto_with_default_tabs | 8 | missing_notebook;missing_page;missing_labelled_page;missing_statusbar;missing_button_box;missing_chatter |
| sc_other | sc.financing.loan | contract_auto_with_default_tabs | 9 | missing_notebook;missing_page;missing_labelled_page;missing_button_box;missing_chatter |
| sc_other | sc.fund.daily.summary | contract_auto_with_default_tabs | 8 | missing_notebook;missing_page;missing_labelled_page;missing_statusbar;missing_button_box;missing_chatter |
| sc_other | sc.history.todo | contract_auto_with_default_tabs | 9 | missing_notebook;missing_page;missing_labelled_page;missing_button_box;missing_chatter |
| sc_other | sc.invoice.category.summary | contract_auto_with_default_tabs | 8 | missing_notebook;missing_page;missing_labelled_page;missing_statusbar;missing_button_box;missing_chatter |
| sc_other | sc.invoice.registration | contract_auto_with_default_tabs | 9 | missing_notebook;missing_page;missing_labelled_page;missing_button_box;missing_chatter |
| sc_other | sc.operating.metrics.project | contract_auto_with_default_tabs | 8 | missing_notebook;missing_page;missing_labelled_page;missing_statusbar;missing_button_box;missing_chatter |
| sc_other | sc.payment.execution | contract_auto_with_default_tabs | 9 | missing_notebook;missing_page;missing_labelled_page;missing_button_box;missing_chatter |
| sc_other | sc.plan.report | contract_auto_with_default_tabs | 8 | missing_notebook;missing_page;missing_labelled_page;missing_statusbar;missing_button_box;missing_chatter |
| sc_other | sc.project.stage.requirement.item | contract_auto_with_default_tabs | 7 | missing_labelled_group;missing_notebook;missing_page;missing_labelled_page;missing_statusbar;missing_button_box;missing_chatter |
| sc_other | sc.project.structure | contract_auto_with_default_tabs | 8 | missing_notebook;missing_page;missing_labelled_page;missing_statusbar;missing_button_box;missing_chatter |
| sc_other | sc.receipt.income | contract_auto_with_default_tabs | 9 | missing_notebook;missing_page;missing_labelled_page;missing_button_box;missing_chatter |
| sc_other | sc.receipt.invoice.line | contract_auto_with_default_tabs | 9 | missing_notebook;missing_page;missing_labelled_page;missing_statusbar;missing_chatter |

## P1 语义标注队列

| domain_group | model | classification | structural_score | gaps |
| --- | --- | --- | --- | --- |
| contract | construction.work.breakdown | needs_semantic_annotation | 12 | missing_labelled_group;missing_statusbar;missing_button_box;missing_chatter |
| equipment | sc.equipment.plan | needs_semantic_annotation | 13 | missing_labelled_group;missing_button_box;missing_chatter |
| equipment | sc.equipment.price | needs_semantic_annotation | 13 | missing_labelled_group;missing_button_box;missing_chatter |
| equipment | sc.equipment.request | needs_semantic_annotation | 13 | missing_labelled_group;missing_button_box;missing_chatter |
| equipment | sc.equipment.settlement | needs_semantic_annotation | 13 | missing_labelled_group;missing_button_box;missing_chatter |
| equipment | sc.equipment.usage | needs_semantic_annotation | 13 | missing_labelled_group;missing_button_box;missing_chatter |
| labor | sc.labor.plan | needs_semantic_annotation | 13 | missing_labelled_group;missing_button_box;missing_chatter |
| labor | sc.labor.price | needs_semantic_annotation | 13 | missing_labelled_group;missing_button_box;missing_chatter |
| labor | sc.labor.request | needs_semantic_annotation | 13 | missing_labelled_group;missing_button_box;missing_chatter |
| labor | sc.labor.settlement | needs_semantic_annotation | 13 | missing_labelled_group;missing_button_box;missing_chatter |
| labor | sc.labor.usage | needs_semantic_annotation | 13 | missing_labelled_group;missing_button_box;missing_chatter |
| material | sc.material.rental.order | needs_semantic_annotation | 13 | missing_labelled_group;missing_button_box;missing_chatter |
| material | sc.material.rental.plan | needs_semantic_annotation | 13 | missing_labelled_group;missing_button_box;missing_chatter |
| material | sc.material.rental.settlement | needs_semantic_annotation | 13 | missing_labelled_group;missing_button_box;missing_chatter |
| project | project.dictionary | needs_semantic_annotation | 12 | missing_labelled_group;missing_statusbar;missing_button_box;missing_chatter |
| project | project.material.plan | needs_semantic_annotation | 14 | missing_labelled_group;missing_chatter |
| project | project.task | needs_semantic_annotation | 15 | missing_labelled_group |
| project | project.update | needs_semantic_annotation | 13 | missing_labelled_group;missing_statusbar;missing_button_box |
| quality | sc.quality.issue | needs_semantic_annotation | 13 | missing_labelled_group;missing_button_box;missing_chatter |
| quality | sc.quality.recheck | needs_semantic_annotation | 12 | missing_labelled_group;missing_statusbar;missing_button_box;missing_chatter |
| quality | sc.quality.rectification | needs_semantic_annotation | 12 | missing_labelled_group;missing_statusbar;missing_button_box;missing_chatter |
| safety | sc.safety.disclosure | needs_semantic_annotation | 12 | missing_labelled_group;missing_statusbar;missing_button_box;missing_chatter |
| safety | sc.safety.issue | needs_semantic_annotation | 13 | missing_labelled_group;missing_button_box;missing_chatter |
| safety | sc.safety.plan | needs_semantic_annotation | 13 | missing_labelled_group;missing_button_box;missing_chatter |
| safety | sc.safety.recheck | needs_semantic_annotation | 12 | missing_labelled_group;missing_statusbar;missing_button_box;missing_chatter |
| safety | sc.safety.rectification | needs_semantic_annotation | 12 | missing_labelled_group;missing_statusbar;missing_button_box;missing_chatter |
| sc_other | sc.attendance.checkin | needs_semantic_annotation | 13 | missing_labelled_group;missing_button_box;missing_chatter |
| sc_other | sc.contract.event | needs_semantic_annotation | 13 | missing_labelled_group;missing_button_box;missing_chatter |
| sc_other | sc.hazard.source | needs_semantic_annotation | 12 | missing_labelled_group;missing_statusbar;missing_button_box;missing_chatter |
| sc_other | sc.plan | needs_semantic_annotation | 13 | missing_labelled_group;missing_button_box;missing_chatter |
| sc_other | sc.project.document | needs_semantic_annotation | 13 | missing_labelled_group;missing_button_box;missing_chatter |
| sc_other | sc.site.photo.batch | needs_semantic_annotation | 12 | missing_labelled_group;missing_statusbar;missing_button_box;missing_chatter |
| sc_other | sc.workflow.def | needs_semantic_annotation | 13 | missing_labelled_group;missing_button_box;missing_chatter |
| sc_other | sc.workflow.instance | needs_semantic_annotation | 13 | missing_labelled_group;missing_button_box;missing_chatter |
| subcontract | sc.subcontract.plan | needs_semantic_annotation | 13 | missing_labelled_group;missing_button_box;missing_chatter |
| subcontract | sc.subcontract.price | needs_semantic_annotation | 13 | missing_labelled_group;missing_button_box;missing_chatter |
| subcontract | sc.subcontract.register | needs_semantic_annotation | 13 | missing_labelled_group;missing_button_box;missing_chatter |
| subcontract | sc.subcontract.request | needs_semantic_annotation | 13 | missing_labelled_group;missing_button_box;missing_chatter |
| subcontract | sc.subcontract.settlement | needs_semantic_annotation | 13 | missing_labelled_group;missing_button_box;missing_chatter |
| tender | tender.bid | needs_semantic_annotation | 14 | missing_labelled_group;missing_chatter |

## P2 XML 主结构队列



## P0 已可作为基线样本

| domain_group | model | classification | structural_score | gaps |
| --- | --- | --- | --- | --- |
| contract | construction.contract | auto_standardizable | 14 | missing_button_box;missing_chatter |
| contract | construction.contract.expense | auto_standardizable | 14 | missing_button_box;missing_chatter |
| contract | construction.contract.income | auto_standardizable | 14 | missing_button_box;missing_chatter |
| material | sc.material.acceptance | auto_standardizable | 14 | missing_button_box;missing_chatter |
| material | sc.material.inbound | auto_standardizable | 14 | missing_button_box;missing_chatter |
| material | sc.material.outbound | auto_standardizable | 14 | missing_button_box;missing_chatter |
| material | sc.material.purchase.request | auto_standardizable | 14 | missing_button_box;missing_chatter |
| material | sc.material.rfq | auto_standardizable | 14 | missing_button_box;missing_chatter |
| material | sc.material.settlement | auto_standardizable | 14 | missing_button_box;missing_chatter |
| project | project.boq.line | auto_standardizable | 13 | missing_statusbar;missing_button_box;missing_chatter |
| project | project.budget | auto_standardizable | 13 | missing_statusbar;missing_button_box;missing_chatter |
| project | project.project | auto_standardizable | 15 | missing_chatter |
| sc_other | sc.approval.policy | auto_standardizable | 13 | missing_statusbar;missing_button_box;missing_chatter |
| sc_other | sc.ar.ap.company.summary | auto_standardizable | 13 | missing_statusbar;missing_button_box;missing_chatter |
| sc_other | sc.ar.ap.project.summary | auto_standardizable | 13 | missing_statusbar;missing_button_box;missing_chatter |
| sc_other | sc.business.entity | auto_standardizable | 13 | missing_statusbar;missing_button_box;missing_chatter |
| sc_other | sc.document.admin.document | auto_standardizable | 14 | missing_button_box;missing_chatter |
| sc_other | sc.fund.account | auto_standardizable | 14 | missing_button_box;missing_chatter |
| sc_other | sc.fund.account.operation | auto_standardizable | 14 | missing_button_box;missing_chatter |
| sc_other | sc.general.contract | auto_standardizable | 14 | missing_button_box;missing_chatter |
| sc_other | sc.hr.payroll.document | auto_standardizable | 14 | missing_button_box;missing_chatter |
| sc_other | sc.office.admin.document | auto_standardizable | 14 | missing_button_box;missing_chatter |
| sc_other | sc.partner.import.review | auto_standardizable | 14 | missing_button_box;missing_chatter |
| sc_other | sc.settlement.order | auto_standardizable | 14 | missing_button_box;missing_chatter |

## P3 Legacy 承载队列

| domain_group | model | classification | structural_score | gaps |
| --- | --- | --- | --- | --- |
| legacy | sc.legacy.account.master | contract_auto_with_default_tabs | 8 | missing_notebook;missing_page;missing_labelled_page;missing_statusbar;missing_button_box;missing_chatter |
| legacy | sc.legacy.account.transaction.line | contract_auto_with_default_tabs | 8 | missing_notebook;missing_page;missing_labelled_page;missing_statusbar;missing_button_box;missing_chatter |
| legacy | sc.legacy.business.entity.map | contract_auto_with_default_tabs | 9 | missing_notebook;missing_page;missing_labelled_page;missing_button_box;missing_chatter |
| legacy | sc.legacy.business.fact.residual | contract_auto_with_default_tabs | 8 | missing_notebook;missing_page;missing_labelled_page;missing_statusbar;missing_button_box;missing_chatter |
| legacy | sc.legacy.deduction.adjustment.line | contract_auto_with_default_tabs | 8 | missing_notebook;missing_page;missing_labelled_page;missing_statusbar;missing_button_box;missing_chatter |
| legacy | sc.legacy.enterprise.business.fact | contract_auto_with_default_tabs | 8 | missing_notebook;missing_page;missing_labelled_page;missing_statusbar;missing_button_box;missing_chatter |
| legacy | sc.legacy.equipment.lease.fact | contract_auto_with_default_tabs | 8 | missing_notebook;missing_page;missing_labelled_page;missing_statusbar;missing_button_box;missing_chatter |
| legacy | sc.legacy.expense.deposit.fact | contract_auto_with_default_tabs | 7 | missing_labelled_group;missing_notebook;missing_page;missing_labelled_page;missing_statusbar;missing_button_box;missing_chatter |
| legacy | sc.legacy.expense.reimbursement.line | contract_auto_with_default_tabs | 8 | missing_notebook;missing_page;missing_labelled_page;missing_statusbar;missing_button_box;missing_chatter |
| legacy | sc.legacy.file.index | contract_auto_with_default_tabs | 8 | missing_notebook;missing_page;missing_labelled_page;missing_statusbar;missing_button_box;missing_chatter |
| legacy | sc.legacy.finance.auxiliary.fact | contract_auto_with_default_tabs | 7 | missing_labelled_group;missing_notebook;missing_page;missing_labelled_page;missing_statusbar;missing_button_box;missing_chatter |
| legacy | sc.legacy.financing.loan.fact | contract_auto_with_default_tabs | 7 | missing_labelled_group;missing_notebook;missing_page;missing_labelled_page;missing_statusbar;missing_button_box;missing_chatter |
| legacy | sc.legacy.fund.confirmation.line | contract_auto_with_default_tabs | 8 | missing_notebook;missing_page;missing_labelled_page;missing_statusbar;missing_button_box;missing_chatter |
| legacy | sc.legacy.fund.daily.line | contract_auto_with_default_tabs | 8 | missing_notebook;missing_page;missing_labelled_page;missing_statusbar;missing_button_box;missing_chatter |
| legacy | sc.legacy.fund.daily.snapshot.fact | contract_auto_with_default_tabs | 8 | missing_notebook;missing_page;missing_labelled_page;missing_statusbar;missing_button_box;missing_chatter |
| legacy | sc.legacy.income.invoice.fact | contract_auto_with_default_tabs | 8 | missing_notebook;missing_page;missing_labelled_page;missing_statusbar;missing_button_box;missing_chatter |
| legacy | sc.legacy.invoice.registration.line | contract_auto_with_default_tabs | 8 | missing_notebook;missing_page;missing_labelled_page;missing_statusbar;missing_button_box;missing_chatter |
| legacy | sc.legacy.invoice.tax.fact | contract_auto_with_default_tabs | 7 | missing_labelled_group;missing_notebook;missing_page;missing_labelled_page;missing_statusbar;missing_button_box;missing_chatter |
| legacy | sc.legacy.labor.subcontract.fact | contract_auto_with_default_tabs | 8 | missing_notebook;missing_page;missing_labelled_page;missing_statusbar;missing_button_box;missing_chatter |
| legacy | sc.legacy.material.detail | contract_auto_with_default_tabs | 8 | missing_notebook;missing_page;missing_labelled_page;missing_statusbar;missing_button_box;missing_chatter |
| legacy | sc.legacy.material.stock.fact | contract_auto_with_default_tabs | 8 | missing_notebook;missing_page;missing_labelled_page;missing_statusbar;missing_button_box;missing_chatter |
| legacy | sc.legacy.partner.map | contract_auto_with_default_tabs | 9 | missing_notebook;missing_page;missing_labelled_page;missing_button_box;missing_chatter |
| legacy | sc.legacy.payment.adjustment.fact | contract_auto_with_default_tabs | 8 | missing_notebook;missing_page;missing_labelled_page;missing_statusbar;missing_button_box;missing_chatter |
| legacy | sc.legacy.payment.residual.fact | contract_auto_with_default_tabs | 8 | missing_notebook;missing_page;missing_labelled_page;missing_statusbar;missing_button_box;missing_chatter |
| legacy | sc.legacy.project.map | contract_auto_with_default_tabs | 9 | missing_notebook;missing_page;missing_labelled_page;missing_button_box;missing_chatter |
| legacy | sc.legacy.purchase.contract.fact | contract_auto_with_default_tabs | 8 | missing_notebook;missing_page;missing_labelled_page;missing_statusbar;missing_button_box;missing_chatter |
| legacy | sc.legacy.receipt.income.fact | contract_auto_with_default_tabs | 7 | missing_labelled_group;missing_notebook;missing_page;missing_labelled_page;missing_statusbar;missing_button_box;missing_chatter |
| legacy | sc.legacy.report.inventory | contract_auto_with_default_tabs | 8 | missing_notebook;missing_page;missing_labelled_page;missing_statusbar;missing_button_box;missing_chatter |
| legacy | sc.legacy.scbs.fact.staging | contract_auto_with_default_tabs | 8 | missing_notebook;missing_page;missing_labelled_page;missing_statusbar;missing_button_box;missing_chatter |
| legacy | sc.legacy.scbs.material.map | contract_auto_with_default_tabs | 9 | missing_notebook;missing_page;missing_labelled_page;missing_button_box;missing_chatter |

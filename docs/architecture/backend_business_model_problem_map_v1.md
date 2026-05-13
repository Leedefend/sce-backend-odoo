# Backend Business Model Problem Map v1

Status: draft architecture audit

This map answers what each backend model family is for. It intentionally ignores customer-specific data repair and focuses on system design: what problem the model family solves, why native Odoo/OCA is or is not enough, and where the boundary should be.

It follows the business-object hierarchy in `backend_business_object_hierarchy_v1.md`: company is the management subject, business is the management object, income and expense are the primary economic directions, and project is the typical construction business carrier.

## Design Reading

The backend model set should be read as four cooperating layers:

| layer | problem solved | boundary |
| --- | --- | --- |
| native extension | reuse Odoo/OCA system-of-record models and add construction anchors | do not duplicate native ownership of partner, project, product, stock, account, purchase, user, company, approval |
| industry document model | represent construction-enterprise documents that native Odoo does not own | must have lifecycle, anchors, user-visible intent, access rules, and product vocabulary |
| projection/read model | make facts searchable, reportable, dashboard-ready, and rebuildable | must not become the only source of truth |
| legacy/replay carrier | preserve source-fidelity historical facts for replay and verification | must not become the primary user workflow |

## Native Extensions

| family | models | problem solved | boundary |
| --- | --- | --- | --- |
| partner identity | `res.partner`, `res.partner.bank` | reuse Odoo partner identity while adding customer/supplier semantic evidence, legacy identity, bank surface, and import review hooks | do not create a separate partner master unless the identity is not a legal/business counterparty |
| project identity | `project.project`, `project.task`, `project.project.stage` | reuse native project/task lifecycle while adding construction project anchors, financial fields, stage requirements, dashboards, scope filters, and legacy project identity | do not replace `project.project`; construction-specific facts should reference it |
| product/material identity | `product.template`, `product.category` | reuse native product/category identity for material catalog projection and procurement/stock compatibility | custom material documents may exist, but product identity should stay native |
| accounting | `account.move`, `account.move.line` | keep accounting integration in Odoo accounting models while adding project/business anchors | do not put accounting journal ownership into construction custom models |
| purchase and stock | `purchase.order`, `purchase.order.line`, `stock.move`, `stock.picking` | reuse procurement and inventory execution surfaces while construction models provide planning, acceptance, settlement, and traceability | native modules own stock/purchase execution; custom models own construction site semantics |
| security/runtime | `res.users`, `res.groups`, `res.company`, `res.config.settings` | reuse Odoo users, groups, company, settings while adding role/capability/runtime restrictions | do not create parallel user or company masters |
| approval | `tier.definition`, `tier.validation` | reuse OCA approval mechanism and bind construction policies to it | custom business models may request approval, but approval engine should stay shared |

## Industry Document Models

| family | representative models | problem solved | why custom |
| --- | --- | --- | --- |
| project cost and BOQ | `project.boq.line`, `project.budget`, `project.budget.line`, `project.cost.code`, `project.cost.ledger`, `project.cost.period`, `project.cost.compare`, `project.profit.compare` | make bid quantities, budget, actual cost, cost period, and cost comparison explicit at project level | native Odoo has analytic/accounting primitives, but not construction BOQ-to-cost-control semantics |
| contract execution | `construction.contract`, `construction.contract.income`, `construction.contract.expense`, `sc.general.contract`, `construction.contract.line`, `sc.contract.event`, `sc.contract.recon.summary` | carry construction contract registry, income/expense split, general procurement contracts, contract lines, events, and reconciliation | native contracts are not a complete construction contract lifecycle; Odoo sales/purchase/accounting do not own all contract semantics |
| payment, receipt, invoice, tax | `payment.request`, `payment.request.line`, `sc.payment.execution`, `sc.receipt.income`, `sc.receipt.invoice.line`, `sc.invoice.registration`, `sc.tax.deduction.registration`, `sc.expense.claim` | support project fund requests, actual payment, receipt/income, invoice registration, tax deduction, deposits, reimbursements, deductions, and repayments | native accounting records final ledgers; these models carry operational documents and approval workflow before/around accounting |
| treasury and accounts | `sc.fund.account`, `sc.fund.account.operation`, `sc.treasury.reconciliation`, `sc.treasury.ledger`, `sc.fund.daily.summary`, `sc.account.income.expense.summary` | manage fund account master data, account operations, daily/confirmation reconciliation, and cash ledger/reporting | native bank/accounting is not enough for project treasury daily reports and confirmation-style construction operations |
| material lifecycle | `project.material.plan`, `sc.material.catalog`, `sc.material.price`, `sc.material.purchase.request`, `sc.material.acceptance`, `sc.material.inbound`, `sc.material.outbound`, `sc.material.rfq`, `sc.material.settlement`, `sc.material.rental.*` | model site material planning, acceptance, inbound/outbound, inquiry, settlement, catalog, price, and rental lifecycle | native inventory and purchase own execution; construction needs site acceptance and settlement semantics |
| labor and equipment | `sc.labor.plan`, `sc.labor.request`, `sc.attendance.checkin`, `sc.labor.usage`, `sc.labor.settlement`, `sc.labor.price`, `sc.equipment.plan`, `sc.equipment.request`, `sc.equipment.usage`, `sc.equipment.settlement`, `sc.equipment.price` | represent labor/equipment planning, use, attendance, settlement, and price standards | native HR/fleet/project modules do not express construction site labor/equipment cost flows directly |
| subcontract lifecycle | `sc.subcontract.plan`, `sc.subcontract.request`, `sc.subcontract.register`, `sc.subcontract.settlement`, `sc.subcontract.price` | split subcontracting into plan, request, register, settlement, price library | this is a construction-specific lifecycle and should not be buried in generic contracts |
| safety, quality, risk | `sc.safety.plan`, `sc.safety.disclosure`, `sc.hazard.source`, `sc.safety.issue`, `sc.safety.rectification`, `sc.safety.recheck`, `sc.quality.issue`, `sc.quality.rectification`, `project.risk`, `project.risk.action` | carry site safety, quality, hazard, rectification, recheck, risk library, and risk actions | these are construction governance facts, not native project tasks alone |
| progress and planning | `sc.plan`, `sc.plan.line`, `sc.plan.version`, `sc.plan.report`, `project.progress.entry`, `project.wbs`, `construction.work.breakdown` | manage project plans, versions, progress measurement, and work breakdown | native tasks are too low-level for plan baseline/version/progress measurement semantics |
| tender chain | `tender.bid`, `tender.bid.line`, `tender.doc.purchase`, `tender.survey`, `tender.doc.review`, `tender.opening`, `tender.opening.competitor`, `tender.guarantee` | represent pre-contract bidding, document purchase, survey, review, bid opening, competitors, guarantees | tendering is a construction/business-development lifecycle outside native sales/purchase |
| document and admin | `sc.project.document`, `sc.document.admin.document`, `sc.office.admin.document`, `sc.hr.payroll.document` | make engineering documents, certificates, borrow/archive, office admin, leave/seal, payroll/social/bonus facts visible | native attachments/documents are storage; these models carry business state and approval |

## Projection And Analytics Models

| family | models | problem solved | boundary |
| --- | --- | --- | --- |
| cockpit/workbench | `sc.dashboard.cockpit.fact`, `sc.workbench.item` | provide role-facing dashboard and workbench facts from source documents | rebuild from source; do not own original workflow |
| finance reports | `sc.ar.ap.company.summary`, `sc.ar.ap.project.summary`, `sc.company.operation.summary`, `sc.comprehensive.cost.summary`, `sc.expense.reimbursement.summary`, `sc.invoice.category.summary`, `sc.salary.summary` | provide finance, AP/AR, operation, cost, reimbursement, invoice, salary summaries | derived and refreshable |
| inventory/material reports | `sc.material.stock.summary` | report stock/material facts for management | source remains material/stock documents |
| treasury reports | `sc.treasury.ledger`, `sc.fund.daily.summary`, `sc.account.income.expense.summary` | report cash movements, daily fund positions, account income/expense | source remains formal fund/account/payment/receipt facts |

## Legacy And Replay Carriers

| family | representative models | problem solved | boundary |
| --- | --- | --- | --- |
| source-fidelity finance facts | `sc.legacy.account.transaction.line`, `sc.legacy.payment.residual.fact`, `sc.legacy.receipt.residual.fact`, `sc.legacy.fund.confirmation.line`, `sc.legacy.fund.daily.line` | preserve old-system cash and account records so projection can be audited | not user workflow |
| source-fidelity tax/invoice facts | `sc.legacy.invoice.registration.line`, `sc.legacy.invoice.tax.fact`, `sc.legacy.tax.deduction.fact`, `sc.legacy.invoice.surcharge.fact` | preserve tax and invoice source details | project into formal invoice/tax models when user-facing |
| source-fidelity contract/project facts | `sc.legacy.purchase.contract.fact`, `sc.legacy.supplier.contract.pricing.fact`, `sc.legacy.construction.diary.line`, `sc.legacy.tender.registration.fact` | preserve contract, diary, tender, supplier pricing evidence | project into formal contract/diary/tender models where reusable |
| source-fidelity people/workflow facts | `sc.legacy.user.profile`, `sc.legacy.user.role`, `sc.legacy.user.project.scope`, `sc.history.todo`, `sc.legacy.workflow.audit`, `sc.legacy.workflow.detail.fact`, `sc.legacy.task.evidence` | preserve old users, roles, scopes, todos, approvals, workflow evidence | runtime user/account/workbench surfaces should be separate |
| mapping and staging | `sc.legacy.project.map`, `sc.legacy.partner.map`, `sc.legacy.business.entity.map`, `sc.legacy.scbs.fact.staging`, `sc.legacy.business.fact.residual` | isolate uncertain mappings, residual facts, and old source semantics from clean runtime models | never treat unresolved staging as accepted product semantics |

## Platform Governance And Extension Models

| family | models | problem solved | boundary |
| --- | --- | --- | --- |
| capability and scene governance | `sc.capability.group`, `sc.capability`, `sc.scene`, `sc.scene.tile`, `sc.scene.version`, `sc.scene.validation`, `sc.scene.audit.log`, `sc.capability.audit.log` | govern product capabilities, scene entry, visibility, validation, and audit | platform governance; industry content should plug in through providers/registry |
| pack and subscription | `sc.pack.registry`, `sc.pack.installation`, `sc.subscription.plan`, `sc.subscription`, `sc.entitlement`, `sc.usage.counter`, `sc.ops.job` | support platform/industry/customer pack installation, entitlement, usage, and ops jobs | customer-specific behavior should enter through packs, not core model drift |
| approval and roles | `sc.approval.policy`, `sc.approval.step`, `sc.approval.scope`, role/group extensions | provide business approval configuration mapped to OCA tier validation and Odoo groups | approval engine stays shared; business policy is configurable |
| dictionaries and defaults | `sc.dictionary`, `project.dictionary`, `sc.system.default.mixin`, `sc.material.system.default.mixin` | provide controlled defaults and vocabulary | do not encode one customer's vocabulary as immutable platform fields |
| audit and validation | `sc.audit.log`, `sc.data.validator`, `sc.delete.guard.mixin` | protect data quality, deletion boundaries, and auditability | platform/industry support, not business facts themselves |

## Boundary Conclusions

1. The model set is not too small; the strict 10-model count was a narrow formal migration-carrier metric.
2. The model set is large because the system owns a construction industry layer, not just a generic Odoo addon.
3. Native Odoo is being used for the right classes of objects: identity, accounting, stock, purchase, users, company, approval, product, project base.
4. Custom models are justified where the construction domain has first-class documents and lifecycles that native Odoo does not own.
5. The weakest boundary is not native-vs-custom. The weakest boundary is customer-specific migration semantics leaking into industry model shape.
6. The next audit step should classify every custom model family into platform, industry, customer, projection, or legacy carrier, then fail CI only when a new model lacks that classification.

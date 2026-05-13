# Backend Business Model Responsibility Matrix v1

Status: draft architecture audit

This matrix answers whether the current model responsibilities are clear enough for further backend iteration. It classifies each major model family by responsibility, source of truth, native dependency, and downstream consumers.

The matrix follows the business-object hierarchy in `backend_business_object_hierarchy_v1.md`: company manages business; business splits into income and expense; project is the typical construction business carrier.

The binding family-level registry is `backend_business_model_family_registry_v1.json`. The binding overlap-risk ownership specs are `backend_business_model_ownership_specs_v1.json`.

## Responsibility Types

| responsibility | definition | allowed writes | examples |
| --- | --- | --- | --- |
| native system-of-record | Odoo/OCA owns the canonical identity or transaction | normal native workflow plus construction extension fields | `res.partner`, `project.project`, `product.template`, `account.move`, `stock.picking` |
| industry source-of-truth | custom construction document owns a first-class business fact | normal construction workflow, approval, and controlled legacy anchor repair | `sc.payment.execution`, `sc.receipt.income`, `sc.material.acceptance`, `sc.subcontract.register` |
| projection/read model | derived model used for list, dashboard, report, ledger, or workbench | deterministic refresh only | `sc.treasury.ledger`, `sc.dashboard.cockpit.fact`, `sc.ar.ap.project.summary` |
| legacy source carrier | replay/source-fidelity table for historical evidence | replay/import only; no user workflow ownership | `sc.legacy.*`, `sc.history.todo` |
| governance/config | controls capability, approval, pack, role, dictionary, validation, audit | admin/config workflow | `sc.capability`, `sc.pack.registry`, `sc.approval.policy`, `sc.dictionary` |
| compatibility/bridge | keeps old/new model names, native hooks, or integration adapters aligned | restricted technical writes | `construction.contract.professional.mixin`, `project.wbs`, native `_inherit` shims |

## Family Responsibility Matrix

| family | primary responsibility | source of truth | native dependency | downstream consumers | current clarity |
| --- | --- | --- | --- | --- | --- |
| partner identity | native system-of-record | `res.partner` | native partner, bank, company | contracts, payments, receipts, supplier/customer views | clear |
| project identity | native system-of-record | `project.project` | native project/task | almost all project-scoped industry docs | clear |
| product/material identity | native system-of-record plus industry documents | `product.template` for identity; `sc.material.catalog` for construction catalog surface | product, category, purchase, stock | material plan, acceptance, stock, purchase, reports | mostly clear; catalog vs product should stay documented |
| accounting | native system-of-record | `account.move`, `account.move.line` | account module | finance reports and project anchors | clear |
| purchase/stock execution | native system-of-record | `purchase.order`, `stock.picking`, `stock.move` | purchase, stock | material procurement and inventory facts | clear |
| project cost and BOQ | industry source-of-truth plus projection | BOQ/budget/cost custom docs for construction cost control | project, accounting/analytic where integrated | cost ledgers, profit/cost reports | mostly clear |
| contract execution | mixed native/custom industry source-of-truth | `construction.contract` for project contracts; `sc.general.contract` for general/procurement contracts | project, partner, approval | payment, receipt, invoice, dashboards, reconciliation | needs explicit split between `construction.contract` and `sc.general.contract` |
| payment/receipt/invoice/tax | industry source-of-truth | formal docs such as `sc.payment.execution`, `sc.receipt.income`, `sc.invoice.registration`, `sc.tax.deduction.registration` | partner, project, contract, approval, accounting | treasury, reports, workbench, audit probes | clear enough after formal registry |
| treasury/account operations | mixed platform/industry | `sc.fund.account` for account master; reconciliation/ledger docs for treasury facts | accounting/bank concepts, project | treasury reports, cockpit | needs clearer account master vs reconciliation vs ledger boundary |
| material lifecycle | industry source-of-truth | material planning, acceptance, inbound/outbound, RFQ, settlement docs | product, purchase, stock, project | inventory, purchase, settlement, material reports | clear |
| labor/equipment | industry source-of-truth | labor/equipment plan/request/usage/settlement/price docs | project, partner/user where applicable | cost, settlement, reports | clear |
| subcontract lifecycle | industry source-of-truth | subcontract plan/request/register/settlement/price docs | project, partner, contract, approval | cost, payment, contract reports | clear and intentionally separate from generic contract |
| safety/quality/risk | industry source-of-truth | issue/rectification/recheck/risk docs | project, user, document attachment | workbench, dashboards, compliance reports | clear |
| progress/planning/WBS | industry source-of-truth | plans, plan lines, versions, progress entries, WBS | project/task | dashboards, progress reports, cost linkage | mostly clear |
| tender chain | industry source-of-truth | tender bid lifecycle docs | partner, project candidate, attachment | contract creation, business development reports | clear |
| document/admin/hr payroll | industry/admin source-of-truth | project documents and admin/payroll process docs | attachment, approval, users | workbench, document center, reports | mostly clear |
| projection/reporting | projection/read model | upstream formal/native/industry docs | source models only | list, report, cockpit, export | clear if refresh path remains deterministic |
| legacy replay/staging | legacy source carrier | old-system source facts and mapping tables | target anchors only | projection scripts, acceptance probes | clear conceptually; must stay out of user workflow |
| capability/scene/pack/subscription | governance/config | governance models | user/group/menu/action/runtime contracts | frontend scene/runtime, release packs | clear platform responsibility |
| approval/dictionary/audit/validation | governance/config | policy, dictionary, audit and validation records | Odoo groups/users, OCA tier | all industry docs and ops gates | clear |

## Company Business Direction Matrix

| direction | company-managed question | source-of-truth families | typical project relationship |
| --- | --- | --- | --- |
| income | What business did the company win, invoice, receive, or recognize? | tender chain, income/project contracts, receipt income, invoice registration, tax evidence, AR summaries | project is created or selected once income opportunity becomes execution scope |
| expense | What business did the company procure, consume, pay, reimburse, settle, or owe? | expense/general contracts, payment request/execution, expense claim, material/labor/equipment/subcontract, AP/cost summaries | project is the usual cost and execution carrier |
| bilateral/mixed | How do income and expense meet around one business scope? | project cost ledger, contract reconciliation, treasury reconciliation, partner semantic roles | project is the dominant join point |
| governance | Who can see, approve, execute, or install business capability? | users/groups, approval policy/scope, capability/scene, pack/subscription, dictionary/audit | project may scope access, but company/platform owns policy |
| projection | What does management need to see now? | dashboard, workbench, ledger, summary/read models | projections aggregate company and project facts |

## Fact Flow Matrix

| flow | source | formal/runtime target | derived/read target | responsibility boundary |
| --- | --- | --- | --- | --- |
| legacy finance replay | `sc.legacy.account.transaction.line`, payment/receipt residual facts | `sc.payment.execution`, `sc.receipt.income`, `sc.expense.claim`, `sc.treasury.reconciliation` | `sc.treasury.ledger`, finance summaries, cockpit facts | legacy carrier preserves old facts; formal docs own user workflow; projections are rebuildable |
| legacy invoice/tax replay | invoice/tax legacy facts | `sc.invoice.registration`, `sc.tax.deduction.registration` | invoice category summaries, finance probes | formal tax/invoice models own runtime semantics |
| legacy contract replay | purchase/supplier-pricing/contract facts | `construction.contract`, `sc.general.contract` | contract reconciliation, cost and finance summaries | contract split must be explicit |
| material operations | product/material master, material plans and site docs | material plan, acceptance, inbound/outbound, RFQ, settlement, rental docs | stock/material summaries | native stock/purchase owns execution; custom docs own site semantics |
| project governance | project, plan, WBS, progress, safety, quality, risk docs | industry documents | cockpit/workbench/report views | project remains native anchor |
| user workflow replay | legacy users, roles, workflow audits, todos | `res.users`, approval policies/scopes, workbench items | role/capability/scene surfaces | legacy workflow evidence is not approval engine |
| scene/capability runtime | capability/scene/pack registry | system.init and scene contracts | frontend runtime views and audit reports | platform governance owns entry semantics; industry content plugs in |

## Boundary Risks

| risk | why it matters | mitigation |
| --- | --- | --- |
| contract model split drift | `construction.contract`, `construction.contract.income/expense`, and `sc.general.contract` can overlap | define contract ownership: project contract vs professional income/expense vs general/procurement contract |
| treasury triple overlap | `sc.fund.account`, `sc.treasury.reconciliation`, and `sc.treasury.ledger` can be confused | account master, reconciliation document, and derived ledger must stay separate |
| material catalog vs product template | product identity and construction catalog surface can diverge | product is identity; catalog is construction-visible material surface and legacy projection carrier |
| payment request vs payment execution | request, approval, and actual payment can be conflated | request owns intent/approval; execution owns payment fact |
| legacy field promotion | customer migration fields may become permanent model fields accidentally | require solution layer and target problem before adding fields |
| projection source-of-truth drift | reports can become de facto writable facts | projections must have refresh scripts and no primary workflow writes |

## Current Architecture Verdict

The architecture is directionally sound because native ownership, industry custom documents, projections, and legacy carriers are distinguishable.

The responsibility model is directionally governed by the family registry and the current ownership specs, but it still needs code-level convergence before being called fully clean:

- contract ownership split
- treasury account/reconciliation/ledger split
- material product/catalog split
- payment request/execution split
- projection refresh ownership

The next implementation step should use the ownership specs as refactor guards: do not merge field/model changes in the risk families unless the change names the owning fact source and proves it does not turn projections, masters, or compatibility bridges into primary workflow facts.

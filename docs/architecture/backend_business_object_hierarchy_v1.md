# Backend Business Object Hierarchy v1

Status: draft architecture audit

This note records the business-object interpretation used to judge whether backend models are reasonable.

Binding registry: `backend_business_management_hierarchy_v1.json`
Universal abstraction: `platform_universal_business_abstraction_v1.md`

## Core Thesis

The universal platform hierarchy is:

```text
platform -> company -> business -> carrier -> fact -> projection
```

The construction binding of that hierarchy is:

```text
platform -> company -> business -> project
```

The platform manages companies. The company manages business. Business splits by economic direction into income and expense. Business then uses an industry-defined carrier. In construction, the typical concrete realization and main carrier of business is a project.

```text
platform
  -> company
      -> business
          -> income business
          -> expense business
          -> project as the typical construction business carrier
              -> contracts
              -> payment / receipt / invoice / tax
              -> cost / BOQ / budget
              -> material / labor / equipment / subcontract
              -> progress / safety / quality / document
              -> treasury / reconciliation / reporting
```

This hierarchy is not a UI menu tree. It is the domain ownership tree used for backend model responsibility.

## Object Definitions

| object | meaning | backend ownership |
| --- | --- | --- |
| platform | the product/runtime layer that manages tenants, companies, capabilities, policies, scenes, subscriptions, and native integrations | capability, scene, pack, subscription, approval, dictionary, audit, native extension boundaries |
| company | the management主体 that owns business, permissions, accounting boundaries, and operating responsibility | `res.company` plus business entity and role/capability governance |
| business | the economic activity the company manages | represented by contracts, projects, finance documents, tenders, and operational documents |
| carrier | the industry-defined object that carries business execution | construction binds this to `project.project`; other industries may bind it to order, case, shipment, loan, policy, batch, store, or asset |
| income business | activity that creates receivables, receipts, revenue, income contracts, invoices, and tax facts | income contracts, `sc.receipt.income`, invoice/tax models, AR projections |
| expense business | activity that creates payables, payments, procurement, cost, deposits, subcontract, materials, labor, equipment | expense contracts, `payment.request`, `sc.payment.execution`, `sc.expense.claim`, material/labor/equipment/subcontract docs |
| project | the most typical construction business carrier; a scoped container where income, expense, cost, progress, quality, safety, and treasury facts meet | native `project.project` extended with construction anchors; most industry docs reference it |
| fact | a dated, attributable business occurrence or state that changes management visibility | industry document models, legacy fact carriers, projections |
| projection | a derived view that helps management see and act on facts | dashboards, ledgers, summaries, workbench items |

## Why Project Is Central But Not The Root

The root is company, not project.

Project is central in construction because construction business is usually delivered through projects. It is not a universal platform root. Some business facts may be company-level or pre-project:

- tenders can precede a formal project
- fund accounts are company/project management infrastructure
- partner identity belongs to the company business network
- approval policies and capabilities are platform/company governance
- accounting, users, groups, company settings remain native platform ownership

Therefore, backend models should not force every fact into a project if the business object is truly company-level, pre-project, or platform-level. But when the fact is project execution, project should be the primary anchor.

## Binding Management Hierarchy

The architecture now has a machine-checked family hierarchy registry. Every model family must declare:

- management subject: `platform`, `company`, `business`, `project`, or `source_system`
- managed object: company, business, project, fact, identity, policy, visibility, evidence, or capability
- project carrier role: primary, optional, pre-project, company-level, not applicable, or derived
- hierarchy statement explaining the placement

Current enforced summary:

| dimension | count |
| --- | ---: |
| registered family hierarchy rows | 19 |
| platform-managed families | 4 |
| company-managed families | 9 |
| business-managed families | 5 |
| source-system evidence families | 1 |
| primary project-carried families | 8 |
| optional project-carried families | 4 |
| pre-project families | 1 |
| derived visibility families | 1 |
| not-project-applicable families | 5 |

This closes the earlier gap: the hierarchy is no longer only a prose assumption. It is an enforcement input for backend model review.

## Income And Expense Split

The income/expense split is the primary economic direction of business.

| direction | business questions | representative models |
| --- | --- | --- |
| income | What did the company win, invoice, receive, recognize, or reconcile as income? | `construction.contract.income`, income-side `construction.contract`, `sc.receipt.income`, income invoice/tax facts, AR summaries |
| expense | What did the company procure, pay, consume, reimburse, settle, deduct, or owe? | `construction.contract.expense`, `sc.general.contract`, `payment.request`, `sc.payment.execution`, `sc.expense.claim`, material/labor/equipment/subcontract docs |
| bilateral / mixed | What links income and expense around one project or counterparty? | project cost ledgers, contract reconciliation, treasury reconciliation, partner semantic roles |

This means a model is reasonable when its responsibility can be located in one of these directions, or when it is clearly a platform/governance/projection/legacy support model.

## Model Reasonableness Test

Before adding a backend model or field, answer these questions:

1. Which company-managed business object does it represent?
2. Is it income, expense, bilateral/mixed, project execution, governance, projection, or legacy evidence?
3. Is `project.project` the correct carrier, or is the fact company-level, pre-project, or platform-level?
4. Does native Odoo already own the identity or transaction?
5. If custom, is it a reusable construction-industry fact, or only one customer's data repair?
6. If derived, why is it not rebuildable from upstream facts?

If a proposed model cannot answer these questions, it should not enter the core industry model layer.

## Current Model Interpretation

| family | hierarchy position | interpretation |
| --- | --- | --- |
| partner/project/product/account/user/company native extensions | company/platform primitives | identities and governance anchors that should stay native |
| project/cost/BOQ/progress/WBS | project business carrier | project-centered management of scope, budget, progress, and cost |
| contract execution | business commitment | income or expense commitment attached to company/project/partner |
| payment/receipt/invoice/tax | economic direction facts | income/expense realization, tax evidence, and cash movement around contracts/projects |
| treasury/account operations | company/project fund management | accounts and reconciliation supporting business execution |
| material/labor/equipment/subcontract | expense/project execution facts | construction resource consumption and settlement |
| safety/quality/risk/document/admin | project and company governance facts | management controls around execution |
| tender chain | pre-project income/business-development fact | business opportunity before project/contract formalization |
| projection/reporting | management visibility | derived views for company and project management |
| legacy/replay carriers | historical evidence | source-fidelity replay layer, not business ownership |
| capability/scene/pack/subscription/approval | platform and company governance | controls what users can see, open, approve, and install |

## Boundary Consequence

This hierarchy changes the audit conclusion:

- The question is not whether there are many models.
- The question is whether every custom model has a clear place under company-managed business.
- Income and expense should be first-class classification dimensions.
- Project should be the typical execution carrier, not a forced universal root.
- Customer data repair should never define the hierarchy.

# Backend Business Model Overlap Analysis v1

Status: draft architecture audit

This note checks the five overlap families against the actual backend model code. It focuses on whether the model surface is reasonable, where boundaries are clear, and where patches should be consolidated before further iteration.

The projection implementation registry is `backend_business_projection_registry_v1.json`.

## Summary

The current model shape is still reasonable, but not all overlap families have the same maturity.

| overlap family | current state | consolidation priority |
| --- | --- | --- |
| contract ownership | usable but split across base contract, professional wrappers, and formal general contract | high |
| treasury account/reconciliation/ledger | workable but terminology must separate master, document, and controlled ledger | high |
| product/material catalog | reasonable native/custom split, with legacy product promotion risk | medium |
| payment request/execution | clear intent-vs-fact split, but request still carries receive compatibility | medium |
| projection refresh | mixed SQL views, physical refresh tables, and controlled ledgers need a registry | high |

## Contract Ownership

Models checked:

- `construction.contract`
- `construction.contract.income`
- `construction.contract.expense`
- `sc.general.contract`
- `sc.contract.event`
- `sc.contract.recon.summary`

Current code shape:

- `construction.contract` is the project contract root. It has `type = out/in`, project/partner anchors, tax, amount, settlement, invoice, received, and paid computed fields.
- `construction.contract.income` and `construction.contract.expense` are wrapper models using `_inherits = {"construction.contract": "contract_id"}`. They do not own a separate contract fact; they specialize entry and enforce type.
- `sc.general.contract` is a formal runtime fact model with legacy provenance, immutability guard, project/company/partner anchors, amount fields, invoice/receipt/payment amount fields, and approval workflow.

Boundary verdict:

- Reasonable: professional income/expense models are wrappers, not duplicate facts.
- Reasonable: `sc.general.contract` is needed for migrated/general/procurement contracts that do not cleanly fit the project contract center.
- Risk: `construction.contract` and `sc.general.contract` both carry contract amounts, invoice amounts, received amounts, paid amounts, partner, project, and workflow state. Without an explicit direction/type policy, later patches can duplicate the same contract commitment in both roots.

Consolidation rule:

- Keep `construction.contract` as the source for project income/expense commitments.
- Keep income/expense wrappers as typed entry surfaces only.
- Keep `sc.general.contract` for general/procurement/legacy contracts that are not project contract-center commitments.
- Do not add a new contract field unless it declares which root owns it: project contract, income wrapper, expense wrapper, general contract, event, or reconciliation.

## Treasury Account Reconciliation Ledger

Models checked:

- `sc.fund.account`
- `sc.fund.account.operation`
- `sc.treasury.reconciliation`
- `sc.treasury.ledger`
- `sc.fund.daily.summary`
- `sc.account.income.expense.summary`

Current code shape:

- `sc.fund.account` is account master data. It has account name, account number, account type, bank, project/company, opening balance, active/state, and legacy account anchors.
- `sc.treasury.reconciliation` is a formal runtime document. It has source kind, state, project/company, account name, bank account, account/bank balances, daily income/expense, confirmation amount, ledger link, legacy provenance, and a legacy immutability guard.
- `sc.treasury.ledger` is not a normal SQL projection. It is a physical ledger model with `create()` blocked unless context contains `allow_ledger_auto`. It is therefore a controlled derived/runtime ledger, not a user-editable workflow document and not a passive SQL view.

Boundary verdict:

- Reasonable: account master, reconciliation document, and ledger are separate concepts.
- Risk: calling all derived surfaces "projection/read model" hides an important difference between read-only SQL views and controlled physical ledgers.
- Risk: `sc.fund.account` currently has no static legacy-confirmed write guard, which is why it remains a declared formal standard exception.

Consolidation rule:

- `sc.fund.account` owns account identity and opening state only.
- `sc.treasury.reconciliation` owns auditable reconciliation.
- `sc.treasury.ledger` owns controlled ledger rows generated from business actions or replay/projection writers.
- Summaries read from these facts; they must not become transaction owners.

## Product Material Catalog

Models checked:

- `product.template`
- `product.category`
- `sc.material.catalog`
- `sc.material.price`
- material plan/acceptance/inbound/outbound/rental/settlement models

Current code shape:

- Native product/category remains the identity and integration root.
- `sc.material.catalog` carries construction-visible material name/code/category/company/project/spec/unit/prices and legacy material anchors.
- `sc.material.catalog` has `promoted_product_tmpl_id` and `promoted_product_id`, explicitly indicating that some legacy material rows are promoted into native product identity.
- `sc.material.price` points to `sc.material.catalog`, optionally to `product.product`, and carries supplier/project/type/unit price/tax/effective date.

Boundary verdict:

- Reasonable: product identity stays native while construction catalog provides industry search and legacy surface.
- Risk: `promoted_product_tmpl_id`, `promoted_product_id`, and `sc.material.price.product_id` can create ambiguity if future code treats catalog as an independent product master.

Consolidation rule:

- Native `product.template` remains identity root.
- `sc.material.catalog` is construction-visible catalog and replay bridge.
- Material operational documents should reference catalog for construction semantics and native product when stock/purchase integration requires it.
- New material identity fields must state whether they belong to native product, catalog surface, or historical mapping.

## Payment Request Execution

Models checked:

- `payment.request`
- `payment.request.line`
- `payment.ledger`
- `sc.payment.execution`
- `sc.expense.claim`
- `sc.treasury.ledger`

Current code shape:

- `payment.request` owns intent and approval. It has project/company/contract/settlement/partner/currency/amount/state, settlement compliance fields, ledger lines, and `action_create_payment_execution`.
- `sc.payment.execution` owns confirmed payment execution facts. It has source kind, state, payment request link, payment accounts, planned/paid/invoice amounts, provenance, immutability guard, and approval actions.
- `sc.expense.claim` is the formal claim/reimbursement/deposit/deduction surface.
- `payment.request.type` still allows `receive`, and `sc.treasury.ledger.payment_request_id` is named "付款/收款申请", so income-side compatibility still exists.

Boundary verdict:

- Reasonable: request and execution are distinct enough to keep.
- Risk: receive-compatible request semantics can overlap with `sc.receipt.income` if future work uses payment request as income workflow.
- Risk: `paid_amount_total` and ledger lines on request can make request look like the actual payment fact if review rules are loose.

Consolidation rule:

- `payment.request` owns intent and approval only.
- `sc.payment.execution` owns actual expense payment facts.
- `sc.receipt.income` owns income receipt facts.
- `sc.treasury.ledger` is a controlled ledger derived from approved actions or replay, not the place where request semantics are invented.

## Projection Refresh

Models checked:

- SQL/view-like projections: `sc.ar.ap.project.summary`, `sc.ar.ap.company.summary`, `sc.material.stock.summary`, `project.cost.compare`, `project.profit.compare`, `sc.salary.summary`
- physical/controlled derived models: `sc.treasury.ledger`, some migration-generated summary tables
- migration writers: formal projection and replay scripts under `scripts/migration`

Current code shape:

- Some projections are `_auto = False` and explicitly reject create/write/unlink, such as `sc.ar.ap.project.summary`.
- Some projections are created as SQL views.
- Some projections are physical tables refreshed by scripts or `init()` logic.
- `sc.treasury.ledger` is a controlled physical ledger with business protection, not a pure projection.

Current registry split:

- `sql_view`: 9
- `physical_refresh_table`: 3
- `controlled_generated_ledger`: 3
- `runtime_workbench_fact`: 2
- `computed_runtime_summary`: 1

Boundary verdict:

- Reasonable: management visibility requires multiple derived surfaces.
- Risk: "projection" currently covers at least three implementation modes: SQL view, physical refresh table, and controlled generated ledger.
- Risk: refresh ordering still lives partly in scripts instead of a typed dependency registry.

Consolidation rule:

- Split projection specs by implementation mode: SQL view, physical refresh table, controlled generated ledger.
- Each projection must declare upstream models, refresh owner, idempotency key, write policy, and acceptance probe.
- Do not merge projection logic into source-of-truth models until the refresh registry exists.

## Code-Level Refactor Order

1. Add projection implementation mode to the family/ownership registry.
2. Add contract ownership tags for new fields and views: project contract, income wrapper, expense wrapper, general contract, event, reconciliation.
3. Add treasury ledger language to distinguish controlled generated ledger from read-only summary projection.
4. Add material identity policy for product/catalog/legacy promotion fields.
5. Add payment direction policy so income receipts do not drift into payment request workflow.

## Decision

Do not delete or merge model families yet.

The correct next step is to tighten ownership metadata and write-policy checks around the overlap families. Once those checks hold, implementation duplication can be reduced safely through mixins or shared helpers.

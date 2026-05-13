# Backend Business Fact Model Audit v1

Status: draft audit baseline
Branch: `audit/backend-business-fact-models`
Generated evidence: `make verify.backend_business_fact.model_audit`
Standard registry: `docs/architecture/backend_business_fact_model_standard_registry_v1.json`
Problem map: `docs/architecture/backend_business_model_problem_map_v1.md`
Responsibility matrix: `docs/architecture/backend_business_model_responsibility_matrix_v1.md`
Business object hierarchy: `docs/architecture/backend_business_object_hierarchy_v1.md`
Family registry: `docs/architecture/backend_business_model_family_registry_v1.json`
Ownership specs: `docs/architecture/backend_business_model_ownership_specs_v1.json`
Audit findings: `docs/architecture/backend_business_model_audit_findings_v1.md`

## Audit Scope

This audit covers backend business fact models in `addons/smart_construction_core/models`, plus the replay and projection entrypoints that decide how legacy facts become user-usable runtime documents.

The audit separates four layers:

- Legacy fact carriers: immutable or near-immutable source facts replayed from old systems.
- Formal runtime facts: user-facing operational models that carry business semantics after projection.
- Projection/read models: summary, cockpit, workbench, ledger, and reporting surfaces derived from facts.
- Master/support models: partner, project, contract, material, approval, and mapping surfaces that anchor facts.

It also classifies model purpose by solution layer:

- `platform`: cross-industry platform primitives and reusable runtime infrastructure.
- `industry`: construction-enterprise business semantics that should be reusable across customers in this industry.
- `customer`: customer-specific facts, acceptance patches, or one-off semantics that must not be promoted without product review.

The current static inventory reports:

| category | count | meaning |
| --- | ---: | --- |
| total model classes | 263 | all Python model classes under smart construction core |
| native model extensions | 25 | models that extend existing Odoo/OCA models through `_inherit` without a new `_name` |
| custom models | 150 | new models defined by this module without mixin inheritance |
| custom models with mixin/inherit | 88 | new models that reuse mail, approval, delete guard, business fact, or compatibility mixins |
| legacy fact models | 50 | `sc.legacy.*` source-fact and mapping carriers |
| formal fact models | 10 | runtime models with `source_origin`, `legacy_source_model`, and `legacy_record_id` |
| projection/read models | 18 | summary, ledger, cockpit, and workbench models |
| traceable models | 132 | models with legacy or source trace fields |
| stateful models | 77 | models with a `state` field |
| registered formal models | 10 | formal runtime facts declared in the standard registry |
| undeclared standard gaps | 0 | standard gaps not covered by a registry exception |
| platform formal facts | 1 | formal runtime facts currently classified as platform-level |
| industry formal facts | 9 | formal runtime facts currently classified as construction-industry-level |
| customer formal facts | 0 | no formal runtime fact is currently classified as customer-specific |
| registered model families | 19 | family-level responsibilities mapped to company/business/income/expense/project hierarchy |
| platform model families | 5 | native/platform/governance/compatibility families |
| industry model families | 13 | reusable construction-industry business families |
| customer model families | 1 | legacy replay/evidence only; not core runtime ownership |
| ownership specs | 5 | explicit boundary specs for the highest-risk overlapping families |
| unclassified models | 0 | every detected model class is mapped to one model family |

## What The Models Carry

## Corrected Audit Boundary

The earlier `formal_fact_model_count=10` is not the total backend model count. It is only the narrow count of formal migration/runtime carriers that have `source_origin`, `legacy_source_model`, and `legacy_record_id`.

The broader backend model design surface is:

- 25 native model extensions: reuse Odoo/OCA as the system-of-record where it already has strong semantics.
- 238 custom model classes: define construction-industry documents, projections, governance, staging, and migration carriers where native Odoo does not provide the right business object.
- 50 legacy fact models: source-fidelity carriers for historical data and migration evidence.
- 18 projection/read models: rebuildable reporting and cockpit surfaces.

So the audit answer is not "we only have 10 models." The correct answer is: we have 263 backend model classes, and 10 of them currently qualify as formal legacy-to-runtime fact carriers under the strict provenance standard.

## What Problem Are We Solving?

The current formal business fact model layer is not primarily a platform kernel. It is a construction-industry runtime fact layer built on top of platform primitives.

The target problems are:

- Treat company as the management subject and business as the management object.
- Classify business by income and expense, while treating project as the typical construction execution carrier.
- Preserve old-system business facts without turning raw legacy tables into user workflow tables.
- Promote reusable construction-enterprise facts into formal runtime documents that users can directly search, open, approve, reconcile, and report on.
- Keep platform primitives small: accounts, provenance, source identity, states, projection registry, audit/probe framework.
- Prevent customer-specific acceptance patches from silently becoming product model definitions.

The practical boundary is:

| layer | model responsibility | example in current registry |
| --- | --- | --- |
| platform | reusable primitives, provenance, account/master anchors, projection governance | `sc.fund.account` |
| industry | construction finance, contract, project execution, tax, treasury semantics | `sc.payment.execution`, `sc.receipt.income`, `sc.general.contract`, `sc.construction.diary` |
| customer | one-off labels, mapping decisions, acceptance repair, local classification | none in formal model registry; should stay in mapping/projection/extension until reviewed |

This means future backend model changes should first answer: is the requested field or model a platform primitive, a construction-industry reusable concept, or a customer-specific repair?

If it is customer-specific, the default implementation should be a projection rule, mapping artifact, extension pack, or registry exception, not a new core model field.

## Native Reuse Vs Custom Definition

The system should use native Odoo/OCA when the target concept is already a mature platform primitive:

- partner identity and business role: `res.partner`, `res.partner.bank`
- project master and tasks: `project.project`, `project.task`
- accounting integration: `account.move`, `account.move.line`
- purchasing and inventory hooks: `purchase.order`, `purchase.order.line`, `stock.move`, `stock.picking`
- products and categories: `product.template`, `product.category`
- users, groups, settings, company: `res.users`, `res.groups`, `res.config.settings`, `res.company`
- approval framework hooks: `tier.definition`, `tier.validation`

The system should extend native models, not replace them, when:

- the native model owns identity, access, chatter, accounting, stock, or project lifecycle.
- the construction-specific semantics are additional fields, entry filters, UI actions, or projection anchors.
- integration with Odoo modules matters more than owning an independent workflow.

The system should define custom models when:

- the construction domain has a first-class document not represented by native Odoo, such as payment execution, receipt income, construction diary, treasury reconciliation, material acceptance, subcontract plan/register/settlement, safety/quality issue flows.
- the model is a projection/read surface, not a native transaction.
- the model is a source-fidelity legacy fact carrier and must preserve old-system identifiers, states, and raw labels.
- the model is governance infrastructure such as capability, scene, pack, approval scope, or audit logs.

The system should not define core custom models for:

- one customer's label preference.
- one customer's legacy mapping exception.
- temporary acceptance repair.
- fields that can be calculated, projected, or placed in an extension pack.

## Is The Current Shape Reasonable?

Directionally yes, but with a clear caveat.

It is reasonable that the core module has many custom construction models because Odoo's native modules do not directly model construction-enterprise facts such as subcontract lifecycle, material site acceptance, project treasury reconciliation, construction diary, tender chain, and historical replay evidence.

It is also reasonable that we extend native project, partner, product, account, stock, purchase, user/group, and approval models instead of replacing them.

The caveat is that the boundary needs stronger governance. The current model set grew through product work, migration work, visible-surface repair, and acceptance patches. Without classification, customer-specific migration needs can look like product models. This branch now starts closing that gap by adding:

- implementation kind audit: native extension vs custom model vs custom model with mixin/inherit.
- solution layer audit: platform vs industry vs customer.
- formal fact registry: target problem, business logic, projection scripts, probes, and promotion policy.
- family registry: company/business/income/expense/project ownership for the major model families.

The family registry extends the audit beyond the 10 formal migration carriers. It classifies 19 major model families by source-of-truth responsibility, business object, solution layer, target problem, and boundary rule. The companion problem map explains what each family solves, and the responsibility matrix records the highest-risk overlaps that still need explicit ownership specs before broad refactoring.

## Boundary Rules

Use this decision order before adding or changing a backend model:

1. Native first: if Odoo/OCA has the system-of-record model, extend it.
2. Industry custom second: if construction semantics require an independent document, define a custom industry model with explicit lifecycle and anchors.
3. Projection third: if the data is derived, use a projection/read model and make it rebuildable.
4. Legacy carrier only for replay: if the purpose is preserving old-system facts, use `sc.legacy.*` and do not expose it as the primary user workflow.
5. Customer-specific last: if the rule exists only for one acceptance dataset or one customer's vocabulary, keep it in mapping/projection/pack/exception until product review promotes it.

Promotion from customer to industry requires:

- at least one reusable target problem beyond the original customer.
- explicit business domain vocabulary.
- source/projection/probe coverage.
- no dependency on one legacy table's accidental labels unless documented as industry evidence.

Promotion from industry to platform requires:

- cross-industry semantics.
- no construction-only anchors in the required field set.
- compatibility with native Odoo ownership boundaries.
- a migration path for existing industry records.

### Legacy Fact Carriers

Legacy fact models preserve historical source semantics, not final user workflow semantics. They should remain replay-safe and source-faithful. Examples include:

- finance and cash-flow facts: `sc.legacy.account.transaction.line`, `sc.legacy.payment.residual.fact`, `sc.legacy.receipt.income.fact`, `sc.legacy.fund.confirmation.line`, `sc.legacy.fund.daily.line`
- invoice and tax facts: `sc.legacy.invoice.registration.line`, `sc.legacy.invoice.tax.fact`, `sc.legacy.tax.deduction.fact`, `sc.legacy.deduction.adjustment.line`
- contract and project facts: `sc.legacy.purchase.contract.fact`, `sc.legacy.supplier.contract.pricing.fact`, `sc.legacy.construction.diary.line`, `sc.legacy.tender.registration.fact`
- master and mapping facts: `sc.legacy.project.map`, `sc.legacy.partner.map`, `sc.legacy.scbs.fact.staging`, `sc.legacy.user.profile`

These models are the replay/input boundary. They should not absorb new-system business workflow unless a source fact has no better target yet and is explicitly marked as residual or staging.

### Formal Runtime Facts

The current formal fact models are:

| model | business logic carried |
| --- | --- |
| `sc.expense.claim` | expense, deposit, deduction, repayment, and related inflow/outflow claims |
| `sc.payment.execution` | payable execution, actual outflow, payment application residuals |
| `sc.receipt.income` | receipt, income, arrival confirmation, and residual receipt facts |
| `sc.invoice.registration` | invoice registration and invoice tax runtime surface |
| `sc.tax.deduction.registration` | tax deduction registration promoted from legacy tax-deduction facts |
| `sc.financing.loan` | financing and loan facts |
| `sc.general.contract` | procurement/general/supplier contract facts that are not native `construction.contract` income contracts |
| `sc.treasury.reconciliation` | treasury reconciliation from fund daily and confirmation lines |
| `sc.fund.account` | legacy fund account master data |
| `sc.construction.diary` | construction diary runtime facts |

These models are user-facing business carriers. They should be writable through normal workflows for new records and mostly immutable for `source_origin='legacy'` records after `legacy_confirmed`, except for anchor repair fields such as partner, project, ledger, active flag, and notes.

### Projection And Read Models

Projection/read models are not source-of-truth workflow documents. They should be rebuildable from formal facts or legacy facts. Examples:

- cockpit/workbench: `sc.dashboard.cockpit.fact`, `sc.workbench.item`
- finance summary: `sc.treasury.ledger`, `sc.fund.daily.summary`, `sc.ar.ap.company.summary`, `sc.ar.ap.project.summary`
- cost/material/reporting: `sc.comprehensive.cost.summary`, `sc.material.stock.summary`, `sc.account.income.expense.summary`

They need deterministic refresh scripts and probes, but should not become the only place where business facts exist.

## Patch Integration Assessment

The latest iterations moved in the right direction: replay/import is distinct from user-usable initialization, and `history.business.usable.init` now calls formal projections, partner semantic normalization, projection probes, and the formal business backfill audit.

The integration pain is now visible in three places:

- `history_business_usable_init.sh` is a long serial script. It has become the operational truth for projection order but not a typed dependency graph.
- Multiple formal models duplicate the same migration fields and protections: `source_origin`, `legacy_source_model`, `legacy_record_id`, `legacy_confirmed`, unique source constraint, sequence creation, context project default, and legacy write guards.
- Some late projection patches are semantically cohesive but implemented as many single-purpose scripts. This is acceptable for migration safety, but the model layer should define the stable contract so future patches do not invent new field names or state policies.

## Redundancy And Drift Risks

### High Priority

- Introduce one formal migration fact mixin for runtime documents. The codebase already has `sc.business.fact.mixin`, but most high-value formal models do not inherit it because they need richer approval and domain-specific fields. A smaller `sc.formal.legacy.fact.mixin` should standardize only migration provenance and immutability.
- Keep legacy carriers and formal runtime facts separate. Do not turn `sc.legacy.*` models into user workflow models, and do not make projections the only runtime surface.
- Convert `history_business_usable_init.sh` from an append-only shell sequence into a documented projection registry with stage, source models, target models, idempotency key, and probe.

### Medium Priority

- Normalize naming across `source_kind`, `claim_type`, `receipt_type`, `expense_type`, and ad hoc text categories. Use typed selection fields for stable business taxonomy and text fields only for legacy labels.
- Standardize immutable legacy write policy. Some models allow anchor repair after `legacy_confirmed`; `sc.fund.account` currently has no static write guard signal in the audit.
- Standardize monetary fields and required anchors. Some formal models require `project_id`; account/master style models may not. The rule should be explicit by model archetype.

### Lower Priority

- Existing specialized document families such as subcontract, labor, equipment, material, safety, quality, and office documents share a plan/request/register/settlement pattern. They can be converged later with abstract helpers, but this should not block the formal migration fact standard.

## Current Standard Gaps

The static audit reports three raw formal fact standard gaps. All three are currently declared in `backend_business_fact_model_standard_registry_v1.json`; therefore the governance status is `undeclared_standard_gap_count=0`.

| model | gap |
| --- | --- |
| `sc.construction.diary` | lacks `company_id`, `partner_id`, and `currency_id`; this may be acceptable if classified as non-monetary project diary, but the exception must be explicit |
| `sc.fund.account` | lacks `partner_id` and `legacy_document_state`; no static legacy-confirmed write guard was detected |
| `sc.treasury.reconciliation` | lacks `partner_id`; this may be acceptable if it is account/project centered rather than counterparty centered |

These should be resolved by either adding the fields or registering explicit archetype exceptions.

## Standard Registry

The standard registry is now the binding audit input for formal runtime facts. It declares:

- model name and archetype
- solution layer: `platform`, `industry`, or `customer`
- target problem solved by the model
- promotion policy for when the model may move between layers
- business domain and business logic carried by the model
- projection scripts responsible for creating or refreshing the model
- runtime probes and formal probes that protect the projection
- standard field exceptions and their reason

The current registry covers all 10 detected formal runtime fact models and has no missing script/probe paths.
It currently classifies `sc.fund.account` as platform-level, and the other 9 formal runtime facts as construction-industry-level. No customer-specific formal fact is accepted into the core registry.

The static audit distinguishes two gap types:

- `raw_standard_gap_count`: physical mismatch against the default formal runtime field set.
- `undeclared_standard_gap_count`: raw gaps not covered by registry exceptions.
- `registry_shape_gap_count`: missing or invalid registry metadata such as `solution_layer`, `target_problem`, or `promotion_policy`.

Only undeclared gaps should block future CI. The enforcement target is:

```bash
make verify.backend_business_fact.model_standard
```

It fails when any of these are present:

- formal runtime fact model detected by source scan but missing from the registry
- registry model not detected in source
- raw standard gap without a declared exception
- registry projection/probe path that no longer exists
- registry entry without a valid solution layer, target problem, business logic, business domain, or promotion policy
- family registry entry with invalid/missing responsibility, business object, solution layer, target problem, source of truth, or representative model references
- detected model class that cannot be mapped to a model family

## Family Registry

The family registry is the binding audit input for the broader 263-class model surface. It follows the hierarchy:

```text
company -> business -> income/expense -> project as the typical construction carrier
```

Current family-level classification:

| dimension | count |
| --- | ---: |
| total families | 19 |
| platform families | 5 |
| industry families | 13 |
| customer families | 1 |
| native system-of-record families | 3 |
| industry source-of-truth families | 10 |
| projection/read families | 1 |
| legacy source carrier families | 1 |
| governance/config families | 3 |
| compatibility/bridge families | 1 |

The important design decision is that the only `customer` family is `legacy replay and historical evidence`. This is intentional: customer-specific old-data repair can be preserved and replayed, but it must not define the core company/business/income/expense/project hierarchy.

The family registry answers "what does this model family solve?" at the system-design layer:

- company/platform families solve governance, visibility, installability, identity, and compatibility.
- income families solve tenders, income contracts, receipts, invoices, and tax evidence.
- expense families solve procurement, payment, reimbursement, material/labor/equipment/subcontract cost, and settlement.
- project families solve the construction execution carrier: budget, BOQ, progress, quality, safety, risk, diary, and WBS.
- projection families solve management visibility and must remain rebuildable.
- legacy families solve historical evidence and replay, not future runtime workflow ownership.

The static audit now also assigns every detected model class to one family. Current coverage is complete:

| family | detected model classes |
| --- | ---: |
| company and business governance | 7 |
| compatibility bridges and native extensions | 9 |
| document admin payroll and office operations | 5 |
| expense contract and procurement commitment | 3 |
| income contract and tender business | 14 |
| labor equipment and subcontract lifecycle | 26 |
| legacy replay and historical evidence | 51 |
| material lifecycle | 25 |
| partner and counterparty identity | 4 |
| payment request and payment execution | 4 |
| product and material identity | 4 |
| progress quality safety risk and diary | 24 |
| project budget BOQ and cost control | 15 |
| project identity and execution carrier | 20 |
| projection summaries and management visibility | 18 |
| receipt income invoice and tax realization | 5 |
| scene capability subscription and frontend contract runtime | 13 |
| treasury account reconciliation and ledger | 3 |
| workflow approval dictionary audit and validation | 13 |

The enforcement rule is simple: a new backend model may be added only if it can be classified into one of these families or the family registry is deliberately extended.

## Ownership Specs For Overlap Risks

Five overlap areas are now explicit ownership specs:

| spec | decision |
| --- | --- |
| `contract_ownership_split` | keep project contracts, professional income/expense contracts, and general contracts, but require new fields to declare the commitment direction they describe |
| `treasury_account_reconciliation_ledger_split` | keep account master, reconciliation document, and derived ledger separate |
| `material_product_catalog_split` | `product.template` remains identity root; `sc.material.catalog` is construction-industry surface |
| `payment_request_execution_split` | payment request owns intent/approval; payment execution owns confirmed payment fact |
| `projection_refresh_ownership` | projection models stay deterministic read/refresh surfaces, not primary workflow owners |

These specs answer the "current state reasonable?" question more concretely:

- reasonable: the system is not trying to replace native company, project, partner, product, account, stock, purchase, user, or approval roots.
- reasonable: construction-specific business facts are custom because native Odoo does not own these document lifecycles.
- not fully clean yet: overlapping families are acceptable only under the declared ownership splits; future changes should fail review if they blur those boundaries.

## Proposed Unified Model Standard

### Standard Archetypes

| archetype | purpose | required traits |
| --- | --- | --- |
| legacy source fact | source-faithful replay carrier | `legacy_*` identity, source table, source state, raw labels, idempotent replay key, no user workflow mutation |
| formal runtime fact | user-facing business document | project/company anchor when applicable, partner/contract/account anchors when applicable, typed business category, amount/currency when monetary, state machine, source provenance, legacy immutability |
| projection/read model | rebuildable derived view | source model/res id or deterministic aggregate key, refresh script, probe, no unique business workflow ownership |
| master/support model | anchor and governance surface | stable identity, semantic rank/classification, mapping evidence, explicit business acceptance state |

### Required Formal Runtime Fields

Formal runtime facts should default to:

- identity: `name`, `document_no` or equivalent source document number
- source: `source_origin`, `source_kind` or typed business category, `legacy_source_model`, `legacy_source_table`, `legacy_record_id`, `legacy_document_state`
- anchors: `project_id`, related stored `company_id`, `partner_id` where counterparty exists, `contract_id` where contract exists
- people and time: creator/handler fields, `creator_legacy_user_id`, `creator_name`, `created_time`, business date
- money: amount fields with `currency_id` and non-negative constraints when semantically non-negative
- state: normal workflow states plus `legacy_confirmed`; legacy records cannot be cancelled by normal new-system actions
- traceability: SQL uniqueness on legacy source, active flag, note, optional attachment reference
- verification: projection write script, runtime probe, and formal projection probe coverage

### Exception Policy

If a model intentionally lacks a standard field, the exception should be documented in a registry with:

- model
- missing standard field
- reason
- replacement field or proof that the concept does not apply
- probe that protects the decision

Examples likely needing explicit exceptions: `sc.construction.diary`, `sc.fund.account`, `sc.treasury.reconciliation`.

## Recommended Next Iterations

1. Stop treating specific customer data repair as the main design driver for this branch. Keep customer-specific facts in mapping/projection/pack layers unless promoted by product review.
2. Add explicit ownership specs for the risk families already called out by the responsibility matrix:
   - contract ownership split
   - treasury account/reconciliation/ledger split
   - material product/catalog split
   - payment request/execution split
   - projection refresh ownership
3. Add a small `sc.formal.legacy.fact.mixin` only after the registry shows repeated implementation duplication worth extracting.
4. Refactor one low-risk formal model first, preferably `sc.tax.deduction.registration` or `sc.financing.loan`, to prove any mixin does not disturb approval-heavy models.
5. Split `history_business_usable_init.sh` into a projection registry runner while preserving the current shell target for operational compatibility.

## Verification

Run:

```bash
make verify.backend_business_fact.model_audit
make verify.backend_business_fact.model_standard
```

Outputs:

- `artifacts/backend/backend_business_fact_model_audit.json`
- `artifacts/backend/backend_business_fact_model_audit.md`

Current summary:

- `formal_fact_model_count=10`
- `registered_formal_model_count=10`
- `raw_standard_gap_count=3`
- `undeclared_standard_gap_count=0`
- `registry_path_gap_count=0`
- `registry_shape_gap_count=0`
- `solution_layer_counts={"industry": 9, "platform": 1}`
- `family_registry_count=19`
- `family_solution_layer_counts={"customer": 1, "industry": 13, "platform": 5}`
- `family_registry_shape_gap_count=0`
- `family_registry_reference_gap_count=0`
- `ownership_spec_count=5`
- `ownership_spec_shape_gap_count=0`
- `ownership_spec_reference_gap_count=0`
- `unclassified_model_count=0`
- `implementation_counts={"custom_model": 150, "custom_model_with_mixin_or_inherit": 88, "native_model_extension": 25}`

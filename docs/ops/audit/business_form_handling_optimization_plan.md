# Business Form Handling Optimization Plan

Date: 2026-06-12

## Objective

Deliver business handling forms that let users complete daily work through list + create/view forms, while preserving old business cognition through `sc.business.category` and keeping the frontend as a generic contract renderer.

## Architecture Boundary

- `sc.business.category` owns business semantics: category code, old aliases, default values, required fields, form sections, and downstream ledger policy.
- Odoo models own persistence, defaults, validation, state transitions, and compatibility with migrated data.
- `smart_core` contract assembly owns projection: it reads backend facts and emits field groups, field policies, validation rules, and form structure contracts.
- The frontend only renders the contract and carries navigation context. It must not encode construction business rules, category-specific field order, or legacy field visibility.

## Current Audit Result

- Business categories: 58.
- Categories with `form_policy_json`: 4, all in invoice/tax.
- Contract, finance, material, and site business categories mostly still depend on raw Odoo form order.
- Many raw forms mix handling fields with ledger/view-only fields: legacy numbers, source trace, audit users, state, pushed document numbers, execution totals, and migrated labels appear too early in create forms.
- Several actions already carry `default_business_category_code`; models mostly resolve `business_category_id` on create. Contract forms still need category default support in `default_get` and supplement-contract category eligibility.

## Delivery Strategy

1. Standardize one business domain at a time.
2. For each domain, define create/edit/readonly profiles:
   - create: only fields needed to start or submit the business.
   - edit: handling fields plus controlled status fields when still actionable.
   - readonly: execution, legacy trace, source, audit, downstream totals, and closure evidence.
3. Keep list-first workflow:
   - menu opens a list.
   - create opens the same model form.
   - category context decides defaults and form policy.
4. Use browser and contract verification for each domain:
   - action context includes category.
   - `business_form_policy` exists.
   - `form_structure_contract` groups fields in expected order.
   - hidden create-only noise does not appear on the visible form.

## Priority Order

1. Contract domain: income contract, expense contract, supplement contract.
2. Settlement domain: income settlement, expense settlement.
3. Finance handling domain: payment/receipt, expense claim, loan, fund operation, self-funding.
4. Invoice/tax completion: tax certificate, deduction registration, verify existing four policies.
5. Material domain: plan, purchase request, RFQ, acceptance, inbound/outbound derivatives, settlement.
6. Site domain: diary, quality/safety issue, rectification, recheck.

## Acceptance Criteria

- A user can understand what they are creating from the first section of the form.
- Create forms do not show system trace, migrated-only fields, pushed-result fields, or computed ledger totals unless required to make the business decision.
- View forms preserve old data cognition and show source trace without forcing users to fill it.
- Required fields are driven by backend category policy and model validation.
- No frontend category-specific business branches are added.

# Finance Project Visibility Permission Governance v1

## Purpose

Imported legacy projects can carry usable contract and payment facts even when
the old system did not provide complete project member or finance contact facts.
Finance operation in the new system must use those existing business facts
without fabricating ownership data.

## Decision

Finance user authority is extended only through record-rule visibility for
projects that already have contract facts.

This batch does not change:

- ACL CSV files.
- Project membership or finance contact data.
- Payment amount, approval, settlement, or accounting rules.
- Frontend behavior.

## Scope

The authority bridge applies to:

- `project.project` read visibility for finance users when `contract_ids` exist.
- `payment.request` finance read/user rules when the linked project has
  contract facts.
- `payment.ledger` finance read/user rules when the linked project has contract
  facts.

## Rationale

This is a permission-governance correction, not a data-repair batch. Assigning
finance users as project members would fabricate business ownership facts. The
contract-backed project condition uses facts already present in the imported
business domain.

## Verification

Required checks:

- Task contract validation.
- XML parse check.
- `smart_construction_core` module upgrade.
- Restricted verification.
- Finance user rollback-only operational check for contract-backed imported
  project payment handling.

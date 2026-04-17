# Settlement Optional Backend Implementation v1

## Status

Blocked before code changes.

The user has approved the business decision and requested immediate execution,
but the repository execution rules still require an immediate stop when
touching `*payment*` or `*settlement*` files unless a matching narrow exception
exists.

No current exception covers optional payment/settlement business semantics.

## Intended Implementation

When the repo rule exception is added or the task is otherwise authorized at the
repository governance level, the implementation should change only these
surfaces:

- `addons/smart_construction_core/models/core/payment_request.py`
- `addons/smart_construction_core/models/core/payment_ledger.py`
- `addons/smart_construction_core/models/core/settlement_order.py`
- `addons/smart_construction_core/tools/validator/rule_3way_link_integrity.py`

## Required Semantics

Payment request without settlement:

- can submit when contract, funding, attachment, project lifecycle, and approval
  requirements pass
- can approve through tier validation
- can register ledger after approval
- can complete after ledger registration

Payment request with settlement:

- must keep current settlement state checks
- must keep consistency checks
- must keep settlement compliance checks
- must keep settlement payable balance and overpay checks

Settlement submit/approve:

- must validate the target settlement order and its linked records
- must not scan all historical payment requests and fail because old imported
  payments have no `settlement_id`

## Verification Required

The later implementation batch must verify:

- rollback-only no-settlement payment: create, submit, approve, ledger, done
- rollback-only settlement-linked payment: strict settlement balance and state
  checks still pass/fail correctly
- new settlement submit/approve is not blocked by unrelated historical orphan
  payments
- `make verify.restricted`
- `DB_NAME=sc_demo make mod.upgrade MODULE=smart_construction_core`

## Reason For Stop

AGENTS.md Section 6 currently says the agent must stop if any `*payment*` or
`*settlement*` file is touched.

The available exception for payment/settlement is limited to orchestration
boundary recovery and does not cover changing business validation semantics.

This document records the ready implementation boundary but does not bypass the
repo stop rule.

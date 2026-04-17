# No-Contract Payment Submit Governance Block v1

## Decision

The user explicitly authorized fixing the no-contract payment operation gap:

```text
这个已经是新系统能力缺口了，授权完善
```

The requested fix is correct from the business-continuity perspective, but code
implementation is blocked by the current repository governance rules.

## Architecture Position

- Layer Target: Business Fact Rule
- Backend sub-layer: business-fact layer
- Module: no-contract payment submit semantics
- Reason: whether `payment.request` can be submitted without `contract_id` is a
  payment business rule. It cannot be implemented in frontend rendering or scene
  orchestration.

## Required Code Scope

The implementation must touch payment business semantics:

```text
addons/smart_construction_core/models/core/payment_request.py
addons/smart_construction_core/handlers/payment_request_available_actions.py
```

Required behavior:

- allow submit when `contract_id` is empty and no `settlement_id` is selected
  for daily/non-contract outflows
- keep the existing canceled-contract block when `contract_id` is selected
- keep settlement consistency and settlement amount checks when `settlement_id`
  is selected
- keep attachment, project lifecycle, funding, data-validator, tier-validation,
  and audit/evidence behavior intact
- align `payment.request.available_actions` precheck with `action_submit`

## Governance Block

The current AGENTS stop rules require an immediate stop if any `*payment*` file
is touched.

The only existing narrow payment/settlement exception is:

```text
Dedicated Payment-Settlement Orchestration Boundary-Recovery Batches
```

That exception is scoped to orchestration-boundary recovery and explicitly does
not allow changing payment or settlement business/financial semantics.

This no-contract submit fix is a payment business-semantics change, so it is
outside the existing exception.

## Required Next Governance Action

Add a new narrow exception before code implementation, for example:

```text
Dedicated No-Contract Payment Business-Continuity Batches
```

Minimum exception constraints:

- active task must explicitly declare no-contract payment business-continuity
  objective
- allowed paths must exactly include:
  - `addons/smart_construction_core/models/core/payment_request.py`
  - `addons/smart_construction_core/handlers/payment_request_available_actions.py`
- user explicit authorization must be present
- changes must only relax mandatory contract requirement for no-settlement
  daily/non-contract payments
- settlement-selected, contract-selected, funding, attachment, validation,
  audit, ACL, account, ledger, and manifest semantics remain outside scope
- verification must include rollback-only submit flows and existing continuity
  guards

## Stop Result

Status: `BLOCKED_BY_GOVERNANCE`

No payment code was changed in this batch.

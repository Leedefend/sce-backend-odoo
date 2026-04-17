# No-Contract Payment Governance Exception v1

## Purpose

This batch adds a narrow high-risk execution exception for the authorized
no-contract payment business-continuity fix.

## Added Exception

`AGENTS.md` now includes:

```text
6.9 Narrow Exception For Dedicated No-Contract Payment Business-Continuity Batches
```

## Allowed Implementation Scope

The exception allows only these files in a dedicated task:

```text
addons/smart_construction_core/models/core/payment_request.py
addons/smart_construction_core/handlers/payment_request_available_actions.py
```

The allowed behavior is limited to:

- allowing `payment.request` submit without `contract_id` when no
  `settlement_id` is selected for daily or non-contract outflows
- keeping `available_actions` prechecks consistent with `action_submit`

## Explicitly Out Of Scope

- settlement-selected consistency relaxation
- settlement amount rule changes
- selected-contract rule relaxation
- funding gate changes
- attachment requirement changes
- project lifecycle changes
- data-validator changes
- tier-validation changes
- audit/evidence changes
- ACL / record rules / security
- account / ledger semantics
- manifest / migration
- frontend behavior

## Verification Required By The Exception

Any implementation batch using this exception must verify:

- rollback-only no-contract submit
- selected-contract submit
- selected-settlement consistency
- imported business continuity guard

## Result

Status: `PASS`

The governance exception is now in place. The implementation still requires a
separate high-risk task contract with the exact two-file allowlist.

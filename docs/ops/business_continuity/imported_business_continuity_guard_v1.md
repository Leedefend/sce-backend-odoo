# Imported Business Continuity Guard v1

## Purpose

Verify that the system can carry real imported business facts and continue a
new daily payment operation on top of an imported project and contract carrier.

## Command

```bash
DB_NAME=sc_demo make verify.imported_business_continuity.v1
```

## Checks

- Imported project carriers exist.
- Imported contract carriers exist.
- Payment request facts exist.
- Completed and validated payment facts exist.
- Payment ledger facts are uniquely linked to payment requests.
- Existing payment requests still have project and partner carriers.
- A rollback-only payment request can be created, submitted, approved, paid,
  and completed against an imported project/contract carrier without selecting
  a settlement order.

## Classification

- `FAIL`: imported fact carriers are absent, ledger linkage is inconsistent, or
  the rollback-only daily payment probe cannot complete.
- warning: deterministic contract linkage is still incomplete for some imported
  payment requests.
- warning: missing settlement is accepted under the optional-settlement
  semantics and is not a failure.

## Rollback Guarantee

The operability probe creates temporary records in the Odoo transaction and
calls `env.cr.rollback()` before writing artifacts. No business records from the
probe persist.

## Artifacts

```text
artifacts/backend/imported_business_continuity_guard.json
artifacts/backend/imported_business_continuity_guard.md
```

## Current Result

Against `sc_demo`, the guard passed with these facts:

- imported projects: `755`
- funding-ready imported projects: `642`
- imported contracts: `6793`
- payment requests: `30102`
- done and validated payment requests: `12194`
- payment ledgers: `12194`
- ledger-linked payment requests: `12194`
- payment requests missing project: `0`
- payment requests missing partner: `0`
- payment requests missing deterministic contract linkage: `17994`
- payment requests without settlement: `30102`

Rollback-only operability probe:

- project carrier: `2`
- contract carrier: `2012`
- operator: `admin`
- final payment state: `done`
- validation status: `validated`
- settlement selected: `false`
- persisted payment request after rollback: `false`
- persisted ledger after rollback: `false`
- persisted attachment count after rollback: `0`

Warnings:

- Some imported payment requests still lack deterministic contract linkage.
- Payment requests without settlement are accepted by current
  optional-settlement semantics.

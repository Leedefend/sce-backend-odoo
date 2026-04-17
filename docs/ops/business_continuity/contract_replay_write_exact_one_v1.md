# Contract Replay Write Exact-One v1

## Scope

- Database: `sc_demo`
- Mode: high-risk business-data replay
- Target field: `payment.request.contract_id`
- Code changes: none
- Business data writes: `2744` parent payment requests

## Architecture Decision

- Layer Target: Business Fact Replay
- Backend sub-layer: business-fact layer
- Reason: the replay synchronizes imported payment parent records with already
  resolved line-level contract facts. It does not change payment semantics,
  settlement semantics, accounting rules, ACLs, views, or frontend behavior.

## Authorization

- User authorization: received
- Authorization message: `同意执行`
- Task: `ITER-2026-04-18-CONTRACT-REPLAY-WRITE-EXACT-ONE`

## Replay Rule

The write was limited to:

```text
payment.request.contract_id is empty
AND payment.request.line.contract_id is already resolved
AND all resolved line contracts under the same payment request collapse to
    exactly one construction.contract
AND candidate count before write == 2744
```

Excluded:

- unresolved `legacy_supplier_contract_id`
- text-only contract-number evidence
- multiple line contracts under one payment
- no line-level resolved contract
- settlement/account/ledger facts

## Write Result

| Metric | Count |
| --- | ---: |
| Expected candidates before write | 2744 |
| Updated `payment.request` records | 2744 |
| Done-state records updated | 2735 |
| Draft-state records updated | 9 |
| Multi-line-contract records excluded | 143 |
| No-line-contract records excluded | 15107 |

Runtime evidence:

```text
artifacts/business_continuity/contract_replay_write_exact_one_20260418.log
```

The runtime log records the updated payment IDs and sample payment/contract
pairs for rollback and audit.

## Post-Write Verification

Read-only Odoo shell verification:

| Metric | Count |
| --- | ---: |
| Remaining parent missing `contract_id` | 15250 |
| Remaining exact-one line contract candidates | 0 |
| Remaining multi-line-contract excluded | 143 |
| Remaining no-line-contract | 15107 |
| Payment requests with `contract_id` after replay | 14852 |

Guard verification:

| Command | Result | Notes |
| --- | --- | --- |
| `DB_NAME=sc_demo make verify.imported_business_continuity.v1` | PASS | Existing warnings remain: some imported payments still lack deterministic contract linkage; optional-settlement semantics accept no-settlement payments. |
| `DB_NAME=sc_demo make verify.business_fact_consistency.v1` | SKIP_ENV | Existing demo-project fixtures are absent in real data; command exits OK. |

## Business Continuity Impact

The new system can now carry the deterministic contract-basis payment facts
that were already resolved at line level.

The remaining imported payment records are intentionally not forced into a
contract:

- `15107` have no resolved line contract and may represent daily expenses,
  invoice payments, deductions, or other non-contract outflows.
- `143` have multiple line contracts and require a separate allocation or
  manual-resolution policy before any parent contract can be set.

This preserves the business distinction between contract-based payments and
enterprise daily spending.

## Rollback Boundary

Rollback is data-only and should clear `contract_id` only for the recorded
updated IDs in:

```text
artifacts/business_continuity/contract_replay_write_exact_one_20260418.log
```

No code rollback is required for the replay itself.

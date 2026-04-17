# Contract Replay Dry-Run Screen v1

## Scope

- Database: `sc_demo`
- Mode: read-only dry-run
- Target: imported `payment.request` records whose parent `contract_id` is
  still empty
- No payment, contract, settlement, ledger, account, ACL, manifest, frontend, or
  migration records were changed.

## Architecture Decision

- Layer Target: Business Fact Screening
- Backend sub-layer: business-fact layer
- Reason: copying a resolved line contract to an imported payment parent is a
  business-fact replay decision. It must be derived from exact resolved facts,
  not from UI semantics or unresolved legacy IDs.

## Dry-Run Rule

Candidate rule:

```text
payment.request.contract_id is empty
AND payment.request.line.contract_id is already resolved
AND all resolved line contracts under the same payment request collapse to
    exactly one construction.contract
```

Excluded:

- no line-level resolved `contract_id`
- more than one resolved line-level `contract_id`
- residual `legacy_supplier_contract_id` values that do not resolve to
  target `construction.contract`
- text-only contract-number evidence

## Result

| Classification | Payment requests |
| --- | ---: |
| Parent missing `contract_id` | 17994 |
| Exact-one line contract candidate | 2744 |
| Multi line contract excluded | 143 |
| No line contract | 15107 |

State split for the exact-one candidate group:

| State | Payment requests |
| --- | ---: |
| done | 2735 |
| draft | 9 |

The candidate group overlaps with unresolved legacy line IDs in `2251` payment
requests, but the replay rule does not depend on those unresolved IDs. It uses
only the already resolved target `payment.request.line.contract_id`.

## Candidate Samples

| Payment | State | Candidate Contract |
| --- | --- | --- |
| `PRQ2617636` | done | `CONOUT2600154` |
| `PRQ2617635` | done | `CONOUT2603045` |
| `PRQ2617625` | done | `CONOUT2603966` |
| `PRQ2617624` | done | `CONOUT2602279` |
| `PRQ2617623` | done | `CONOUT2603481` |
| `PRQ2617619` | done | `CONOUT2601676` |
| `PRQ2617618` | done | `CONOUT2603115` |
| `PRQ2617617` | done | `CONOUT2604097` |
| `PRQ2617616` | done | `CONOUT2603750` |
| `PRQ2617615` | done | `CONOUT2602398` |

## Interpretation

This dry-run confirms one safe replay lane:

```text
line exact-one resolved contract -> parent payment contract
```

It also confirms that most imported payments with empty parent `contract_id`
should remain contractless unless stronger business evidence is found:

- `15107` have no resolved line contract
- `143` have multiple resolved line contracts and need manual or future
  allocation logic
- the residual `1556` unresolved old IDs are not contract source-table keys

## Decision

Do not write in this screen.

A later dedicated high-risk replay batch may update only the `2744` exact-one
candidate records, with rollback and verification in the same batch.

## Business Continuity Boundary

This keeps the new system aligned with the old business facts:

- contract-basis payments can receive a parent contract when the line contract
  is already exact and deterministic
- daily expense, invoice payment, deduction, and other non-contract outflows can
  continue without forced contract or settlement
- ambiguous multi-contract payments are not silently collapsed

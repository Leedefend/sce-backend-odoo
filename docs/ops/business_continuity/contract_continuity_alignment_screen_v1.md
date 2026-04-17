# Contract Continuity Alignment Screen v1

Task: `ITER-2026-04-17-CONTRACT-CONTINUITY-ALIGNMENT-SCREEN`

Mode: screen only

Runtime:
- profile: daily
- database: `sc_demo`
- timestamp: `2026-04-17T21:02:25+08:00`

## Boundary

This screen classifies imported `construction.contract` records for continuity
alignment. It does not update contract state.

## Evidence

### Current imported contract facts

- total contracts: 6793
- all contracts have `legacy_contract_id`
- all contracts are `state=draft`
- all contracts have project/partner/company links
- all linked projects are now `lifecycle_state=in_progress`

Current state/type distribution:

| type | state | total | zero amount |
| --- | --- | ---: | ---: |
| in | draft | 5313 | 237 |
| out | draft | 1480 | 50 |

### Downstream evidence coverage

| Evidence | Count |
| --- | ---: |
| has payment request | 658 |
| has payment request line | 4125 |
| has workflow audit | 6616 |
| has approved workflow audit | 6616 |
| has any downstream fact | 6685 |

### Candidate lanes

| type | current state | candidate lane | count |
| --- | --- | --- | ---: |
| in | draft | running_candidate | 4137 |
| in | draft | confirmed_candidate | 1083 |
| in | draft | no_downstream_fact | 93 |
| out | draft | running_candidate | 646 |
| out | draft | confirmed_candidate | 819 |
| out | draft | no_downstream_fact | 15 |

Totals:

- running candidates: 4783
- confirmed candidates: 1902
- keep draft: 108

## Screened Rules

### Rule B1: running candidate

If an imported contract has payment request or payment request line evidence,
then the contract has moved beyond draft and should align to:

- `state=running`

Reason:

- payment/request-line evidence proves execution has begun.
- existing model action allows draft/confirmed contracts to enter running.

### Rule B2: confirmed candidate

If an imported contract has approved workflow audit evidence but no payment
request/request-line evidence, align to:

- `state=confirmed`

Reason:

- audit evidence proves approval/effectiveness, but does not prove execution
  payment activity.

### Rule B3: no-downstream contract remains draft

If an imported contract has no approved audit and no execution evidence, keep:

- `state=draft`

Reason:

- no business fact proves the contract is effective or running.

### Rule B4: zero amount is exception metadata, not global blocker

Zero amount records exist but should not block all continuity alignment.

Treatment:

- include zero amount records in candidate lanes if downstream evidence exists.
- track zero amount as data-quality exception for later reporting/operation
  guidance.

## First Implement Batch Recommendation

Create:

`ITER-2026-04-17-CONTRACT-CONTINUITY-DOWNSTREAM-FACT-STATE-SYNC`

Objective:

- sync only imported contracts that are currently `draft`
- set running candidates to `running`
- set confirmed candidates to `confirmed`
- keep no-downstream contracts as `draft`
- produce snapshot/rollback artifacts

Implementation notes:

- do not touch payment states
- do not create contract lines
- do not infer amount
- do not infer approval beyond existing workflow audit evidence
- use ORM write or model actions with explicit imported-continuity evidence

Stop conditions:

- target count drifts from screen evidence
- state sync requires payment/settlement/account file changes
- implementation would create new approval records
- implementation would fabricate amount or line facts

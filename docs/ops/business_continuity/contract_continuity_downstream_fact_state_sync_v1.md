# Contract Continuity Downstream Fact State Sync v1

Task: `ITER-2026-04-17-CONTRACT-CONTINUITY-DOWNSTREAM-FACT-STATE-SYNC`

Runtime:
- profile: daily
- database: `sc_demo`
- timestamp: `2026-04-17T21:07:29+08:00`

## Objective

Align imported contract states with existing business facts so contracts can
continue daily processing in the new system.

## Implemented Rule

Only imported contracts with `legacy_contract_id` were considered.

Rules:

- payment request or request-line evidence -> `state=running`
- approved workflow audit evidence without execution evidence -> `state=confirmed`
- no downstream evidence -> remain `state=draft`

Non-goals:

- no payment state update
- no settlement state update
- no new approval creation
- no contract line creation
- no amount inference

## Runtime Result

Before write:

- target contracts: 6685
- running target: 4783
- confirmed target: 1902

After write:

- already synced: 6685
- needs sync: 0

Final distribution:

| type | state | count |
| --- | --- | ---: |
| in | confirmed | 1083 |
| in | draft | 93 |
| in | running | 4137 |
| out | confirmed | 819 |
| out | draft | 15 |
| out | running | 646 |

## Artifacts

- snapshot: `/mnt/artifacts/migration/contract_continuity_downstream_fact_state_sync_snapshot_v1.csv`
- rollback: `/mnt/artifacts/migration/contract_continuity_downstream_fact_state_sync_rollback_v1.csv`
- result: `/mnt/artifacts/migration/contract_continuity_downstream_fact_state_sync_result_v1.json`

## Verification

- task validation: PASS
- Python compile: PASS
- dry-run check: PASS
- write: PASS
- post-write check: PASS
- final SQL distribution check: PASS

## Next

Payment continuity remains a separate high-risk track.

The next implementation should not mix payment state writes into contract
continuity.

# Fresh DB Replay Adapter Plan v1

Status: PASS

Task: `ITER-2026-04-15-FRESH-DB-REPLAY-ADAPTER-PLAN`

## Scope

Convert replay manifest gaps into adapter implementation tasks. This batch does
not create a database, execute write scripts, or mutate business data.

## Summary

- manifest lanes: `7`
- adapter lanes: `3`
- blocked high-risk lanes: `1`
- database operations: `0`

## Adapter Plan

### partner_l4_anchor_completed

- status: `needs_adapter`
- adapter task: `FRESH-DB-REPLAY-PARTNER-L4-ADAPTER`
- adapter type: `consolidated_anchor_replay`
- write policy: `idempotent_create_only_by_legacy_partner_key`
- batch size: `500-1000 anchors per low-risk batch after dry-run`
- required outputs: `single partner anchor replay payload, rollback targets, aggregate source/target review, discard/hold ledger`

### project_anchor_completed

- status: `needs_adapter`
- adapter task: `FRESH-DB-REPLAY-PROJECT-ANCHOR-ADAPTER`
- adapter type: `consolidated_project_replay`
- write policy: `idempotent_create_only_by_legacy_project_id`
- batch size: `500-1000 projects when precheck is clean`
- required outputs: `single project anchor replay payload, rollback targets, aggregate source/target review, source-missing contract blocker ledger`

### contract_partner_source_12_anchor_design

- status: `design_only`
- adapter task: `FRESH-DB-REPLAY-CONTRACT-PARTNER-12-ANCHOR-ADAPTER`
- adapter type: `new_anchor_recovery_replay`
- write policy: `idempotent_create_only_by company::counterparty_text`
- batch size: `single 12-anchor batch`
- required outputs: `12 partner anchor write payload, rollback targets, post-write partner anchor review, 57 contract retry readiness packet`

## Execution Order

1. Implement partner L4 consolidated replay adapter.
2. Implement project anchor consolidated replay adapter.
3. Implement 12-anchor contract partner recovery adapter.
4. Re-run manifest dry-run and mark certified adapters as `replay_ready_candidate`.
5. Open fresh database operation contract only after adapter dry-run passes.

## Stop Rules

- Do not include payment, settlement, accounting, ACL, manifest, or module
  install lanes.
- Do not run write scripts from adapter planning.
- Do not create/drop databases from adapter planning.

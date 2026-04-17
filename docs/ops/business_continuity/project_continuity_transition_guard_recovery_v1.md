# Project Continuity Transition Guard Recovery v1

Task: `ITER-2026-04-17-PROJECT-CONTINUITY-TRANSITION-GUARD-RECOVERY`

Runtime:
- profile: daily
- database: `sc_demo`
- timestamp: `2026-04-17T21:00:03+08:00`

## Objective

Allow imported projects with proven downstream business facts to leave draft
through an auditable continuity path, without weakening normal new-project
transition validation.

## Implemented Rule

Normal projects still require the existing transition prerequisites for
`draft -> in_progress`.

Imported continuity path is enabled only when:

- context contains `sc_imported_project_continuity_sync`
- project has `legacy_project_id`
- current lifecycle is `draft`
- target lifecycle is `in_progress`
- at least one downstream business fact exists:
  - contract
  - payment request
  - payment ledger
  - legacy receipt/income fact
  - legacy expense/deposit fact
  - legacy invoice/tax fact
  - legacy financing/loan fact
  - legacy fund daily snapshot fact

## Data Sync

Script:

`scripts/migration/project_continuity_downstream_fact_state_sync.py`

Modes:

- `SYNC_MODE=check`: validate target set and produce evidence files
- `SYNC_MODE=write`: update eligible imported projects through ORM

Updated fields:

- `lifecycle_state`: `in_progress`
- `phase_key`: `execution`
- `sc_execution_state`: `in_progress`

Fields intentionally not inferred:

- `company_id`
- `partner_id`
- `owner_id`
- `location`

## Runtime Result

Before write:

- target projects: 701
- needs sync: 701
- already synced: 0

After write:

- target projects: 701
- needs sync: 0
- already synced: 701

Final project distribution:

| lifecycle_state | phase_key | sc_execution_state | count |
| --- | --- | --- | ---: |
| draft | initiation | ready | 55 |
| in_progress | execution | in_progress | 701 |

## Artifacts

- snapshot: `/mnt/artifacts/migration/project_continuity_downstream_fact_state_sync_snapshot_v1.csv`
- rollback: `/mnt/artifacts/migration/project_continuity_downstream_fact_state_sync_rollback_v1.csv`
- result: `/mnt/artifacts/migration/project_continuity_downstream_fact_state_sync_result_v1.json`

## Verification

- task validation: PASS
- Python compile: PASS
- dry-run check: PASS
- write: PASS
- post-write check: PASS
- final SQL distribution check: PASS
- `make verify.contract.native_integrity_guard`: PASS
- backend dev restart: PASS

## Next

Continue to Lane B: contract continuity alignment.

Contract continuity should use the same principle:

- do not treat imported records with downstream facts as newly drafted work
- do not fabricate missing business facts
- do not trigger new approvals for historically completed facts

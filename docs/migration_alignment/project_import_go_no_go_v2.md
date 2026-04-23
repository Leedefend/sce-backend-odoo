# Project Import GO/NO-GO v2

## Decision

- GO: continue non-write project skeleton rehearsal with a real existing
  identity export.
- NO-GO: do not start database write-mode project import yet.

## Evidence

| Check | Result |
| --- | ---: |
| safe-slice sample rows | 30 |
| safe-slice fields | 22 |
| simulated existing identities | 10 |
| create | 20 |
| update | 10 |
| error rows | 0 |
| header errors | 0 |
| no DB / no ORM check | PASS |

## GO Scope

The next allowed step is a non-write rehearsal that replaces
`data/migration_samples/project_existing_identity_snapshot_v1.csv` with a
controlled existing-identity export containing only approved identity columns:

- `legacy_project_id`
- optionally `other_system_id`
- optionally `other_system_code`

## NO-GO Scope

Do not run write-mode import until all of the following are true:

- Existing project identity export is produced from the target environment and
  reviewed.
- Duplicate identity behavior is rehearsed and documented.
- Test-project inclusion/exclusion rule is confirmed.
- Company, specialty, lifecycle/state, user, and partner formal mappings either
  remain explicitly excluded or are separately approved for write-mode handling.
- A dedicated write-mode task contract is created with rollback and validation
  rules.

## Current Conclusion

The importer logic now has dry-run evidence for both create and update
classification. It is ready for a stricter non-write rehearsal, not for database
write import.

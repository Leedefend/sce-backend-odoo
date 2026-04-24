# History Continuity Server Replay Runbook v1

Status: READY

## Goal

Use the same one-click history continuity contract on a server database without
introducing any server-only replay script.

## Preconditions

- target branch is already deployed
- target DB already exists
- server environment is `dev` or `test-like`, not production-danger mode
- migration assets are present in the deployed repo

## One-Click Commands

Rehearse first:

```bash
DB_NAME=<target_db> make history.continuity.rehearse
```

Replay:

```bash
DB_NAME=<target_db> make history.continuity.replay
```

Resume from a failed step:

```bash
DB_NAME=<target_db> HISTORY_CONTINUITY_START_AT=<step_name> make history.continuity.replay
```

Use an explicit artifact root if needed:

```bash
DB_NAME=<target_db> RUN_ID=<run_id> MIGRATION_ARTIFACT_ROOT=/tmp/history_continuity/<target_db>/<run_id> make history.continuity.replay
```

## Current Included Scope

The one-click path now covers:

- users / partner / project / project-member carrier
- contract / contract line / supplier contract / supplier contract line
- receipt / outflow request / actual outflow / outflow request line
- receipt invoice line / receipt invoice attachment
- legacy attachment backfill
- legacy receipt income
- legacy expense deposit
- legacy invoice tax
- legacy financing loan
- legacy fund daily snapshot
- legacy workflow audit

## Expected Validation

Successful rehearse should produce:

- `FRESH_DB_REPLAY_RUNNER_DRY_RUN = PASS`
- `FRESH_DB_REPLAY_PAYLOAD_PRECHECK = PASS`
- `HISTORY_CONTINUITY_USABILITY_PROBE = PASS`
- `zero_critical_counts = 0`

## Failure Handling

If replay stops:

1. keep the generated `RUN_ID`
2. inspect the artifact directory for the failing step output
3. resume with:

```bash
DB_NAME=<target_db> HISTORY_CONTINUITY_START_AT=<failed_step> RUN_ID=<same_run_id> make history.continuity.replay
```

Do not create ad-hoc server-only importer scripts.

## Operational Rule

The canonical server entry remains:

```bash
DB_NAME=<target_db> make history.continuity.replay
```

Any future lane addition must be merged back into:

- `scripts/migration/history_continuity_oneclick.sh`
- `Makefile`
- `docs/migration_alignment/history_continuity_replay_contract_v1.md`

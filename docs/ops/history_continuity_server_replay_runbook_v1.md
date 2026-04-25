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

Post-replay user-surface probe:

```bash
DB_NAME=<target_db> make history.business.usable.probe
```

If the configured artifact root is not writable from Odoo shell, the probe will
fall back to:

```bash
/tmp/history_continuity/<db>/adhoc
```

Replay:

```bash
DB_NAME=<target_db> make history.continuity.replay
```

The default replay chain now includes historical outflow-request state
activation:

- `outflow_request_core` rows with workflow audit evidence are promoted
  `draft -> submit`
- `tier.review` remains untouched
- `validation_status` remains untouched

The chain now also includes historical approved-state recovery:

- downstream-approved `outflow_request_core` rows are promoted
  `submit -> approved`
- approval judgment comes from the frozen downstream-fact artifacts
- live approval runtime is still untouched

The chain now also includes historical done-state recovery:

- downstream-paid `outflow_request_core` rows are promoted
  `approved -> done`
- `validation_status` is restored to `validated`
- one minimal `payment.ledger` fact is materialized per recovered request
- settlement runtime is still not reconstructed

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
- `HISTORY_BUSINESS_USABLE_PROBE = PASS`
- `history_business_usable_ready`

Business-usable probe decisions:

- `history_business_usable_ready`
  - runtime list/form surfaces exist and actionable todo/approval surfaces are present
- `history_business_usable_visible_but_promotion_gaps`
  - runtime records are visible but one or more continuity gaps still block real user business continuation
- `history_business_usable_runtime_gap`
  - even the core runtime list/form surfaces are not yet present

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

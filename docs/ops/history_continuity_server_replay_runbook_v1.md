# History Continuity Server Replay Runbook v1

Status: READY

## Goal

Use the same one-click history continuity contract on a server database without
introducing any server-only replay script.

For a brand-new production database, the goal is historical fact continuity:

- old-system facts must be visible and traceable in the new system
- old-system gaps are allowed when they are true historical facts
- new-system rules apply to new actions after go-live
- historical gaps must not globally block unrelated new business actions

## Preconditions

- target branch is already deployed
- target DB already exists
- target production DB is brand-new when using the production initialization path
- migration assets are present in the deployed repo
- platform baseline initialization has not been bypassed

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

For a fresh production database, use the auditable production entry:

```bash
ENV=prod ENV_FILE=.env.prod DB_NAME=<target_db> PROD_DANGER=1 \
  RUN_ID=prod_history_init_$(date +%Y%m%dT%H%M%S) \
  BASE_URL=https://<production-host> FRONTEND_BASE_URL=https://<production-host> \
  make history.production.fresh_init
```

This production entry runs:

1. start the compose stack
2. install the production module set with `--without-demo=all`
3. apply extension module registry
4. restart Odoo
5. platform initialization preflight
6. history continuity replay
7. business usable probe
8. full business smoke
9. role matrix smoke
10. frontend smoke

If modules have already been installed by an external release job, set:

```bash
HISTORY_PRODUCTION_INSTALL_MODULES=0
```

The default replay chain includes historical outflow-request runtime facts:

- `outflow_request_core` runtime headers are materialized
- actual outflow runtime carriers are materialized
- legacy attachments linked to actual outflow are backfilled when anchors exist

The default replay chain also includes historical outflow-request state
recovery:

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

Detail fact lanes are included by default because production cutover prioritizes
historical fact continuity over forcing old data to satisfy new workflow rules:

- revenue contract lines
- supplier contract headers
- supplier contract summary lines
- outflow request lines
- actual outflow child lines
- residual actual outflow parent carriers for line facts that strict core rules
  excluded; these carriers are marked as non-ledger/non-settlement history facts

The default replay chain also includes the legacy material catalog archive:

- 2,279,734 old material detail facts are preserved as searchable neutral facts
- 130,624 category facts are preserved from cost categories, global material
  categories, and orphan category keys referenced by details
- no `product.product` records are created from the old catalog

The default replay chain also includes the legacy file index archive:

- 178,931 old file metadata rows are preserved from `BASE_SYSTEM_FILE` and
  `T_BILL_FILE`
- file names, paths, sizes, bill keys, upload users, delete flags, encryption
  flags, and source table identity are retained
- binary file transfer is intentionally not performed by this lane

The default replay chain preserves old user-project scope evidence:

- 20,000 current rows and 70,871 removed/history rows are retained from
  `T_System_UserAndXXGL` and `T_System_UserAndXXGL_History`
- rows are linked to historical users and project anchors when possible
- these records are evidence only and do not grant new-system access

The default replay chain preserves old task/todo evidence:

- 78,822 old `T_BASE_TASKDONE` rows are retained as historical evidence
- executor, read, done, source, business, URL, and timeline fields are retained
- no `mail.activity`, approval, or active workflow todo is created from old rows

If a rehearsal needs to isolate only core headers, set:

```bash
HISTORY_CONTINUITY_INCLUDE_DETAIL_FACTS=0
```

If a limited rehearsal must skip the large material archive, set:

```bash
HISTORY_CONTINUITY_INCLUDE_MATERIAL_CATALOG=0
```

If a limited rehearsal must skip the file index archive, set:

```bash
HISTORY_CONTINUITY_INCLUDE_FILE_INDEX=0
```

The old `HISTORY_CONTINUITY_INCLUDE_BLOCKED_GROUP_B` flag is deprecated for the
production path.

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
- legacy user project scope evidence
- legacy task/todo evidence
- legacy attendance/check-in evidence is privacy-restricted and skipped by
  default; include only with `HISTORY_CONTINUITY_INCLUDE_ATTENDANCE_CHECKIN=1`
- legacy personnel movement evidence is privacy-restricted and skipped by
  default; include only with `HISTORY_CONTINUITY_INCLUDE_PERSONNEL_MOVEMENT=1`
- contract / contract line / supplier contract / supplier contract line
- receipt / outflow request / actual outflow / outflow request line
- receipt invoice line / receipt invoice attachment
- legacy attachment backfill
- legacy receipt income
- legacy expense deposit
- legacy invoice tax
- legacy invoice registration lines from `C_JXXP_ZYFPJJD_CB`; this is a
  neutral historical archive and does not create `account.move` invoices
- legacy deduction/settlement adjustment lines from `T_KK_SJDJB_CB`; this is a
  neutral historical archive and does not update native settlement states
- legacy fund confirmation lines from `ZJGL_SZQR_DKQRB_CB`; this is a neutral
  historical archive and does not update native fund or receipt states
- legacy financing loan
- legacy fund daily snapshot
- legacy material catalog archive
- legacy file index archive
- legacy workflow audit

## Expected Validation

Successful rehearse should produce:

- `FRESH_DB_REPLAY_RUNNER_DRY_RUN = PASS`
- `FRESH_DB_REPLAY_PAYLOAD_PRECHECK = PASS`
- `HISTORY_CONTINUITY_USABILITY_PROBE = PASS`
- `zero_critical_counts = 0`
- `HISTORY_BUSINESS_USABLE_PROBE = PASS`
- either `history_business_usable_ready` or
  `history_business_usable_visible_but_promotion_gaps`

For production cutover, `history_business_usable_visible_but_promotion_gaps` is
acceptable when the remaining gaps are old workflow/todo promotion only
(`mail.activity` / `tier.review`) and the following smokes pass:

- `scripts/audit/smoke_business_full.sh`
- `scripts/audit/smoke_role_matrix.sh`
- `scripts/diag/fe_smoke.sh`

Business-usable probe decisions:

- `history_business_usable_ready`
  - runtime list/form surfaces exist and actionable todo/approval surfaces are present
- `history_business_usable_visible_but_promotion_gaps`
  - runtime records are visible, but old workflow/todo promotion is incomplete
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

## Production Boundary

Do not copy a simulated-production database into production as the default
cutover method. For a brand-new production DB, run the committed replay chain on
the server so the production database has its own `RUN_ID`, artifacts, logs, and
validation evidence.

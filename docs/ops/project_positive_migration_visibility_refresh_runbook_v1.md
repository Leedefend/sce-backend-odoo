# Project Positive Migration Visibility Refresh Runbook v1

Status: `ready_for_dev_and_server_replay`

## Purpose

This runbook makes the user-approved project alignment rule reproducible after
the branch enters main:

- keep projects positively identified by contract or runtime business facts;
- keep already separated direct projects;
- archive all other in-database projects from user visibility;
- do not delete projects;
- do not rewrite project names;
- do not rewrite contracts, receipts, payments, or other business facts.

The implementation writes only `project.project.active`.

## Inputs

Required files inside the Odoo container:

- `PROJECT_POSITIVE_MIGRATION_EXCEL_PATH`
  - default: `/mnt/tmp/001/672施工合同项目名称去重统计.xlsx`
  - user-recognized unique construction-contract project names
- `PROJECT_POSITIVE_MIGRATION_RAW_CONTRACT_CSV`
  - default: `$(CONSTRUCTION_CONTRACT_RAW_CSV)`
  - raw construction contract export used to link historical names to canonical project anchors

Recommended artifact root:

- `MIGRATION_ARTIFACT_ROOT=/tmp/project_positive_migration_visibility/<target_db>/<run_id>`

If the artifact root is not writable in the container, the scripts fall back to
`/tmp/project_positive_migration_visibility_refresh` or
`/tmp/project_contract_fact_alias_reconciliation`.

## Commands

Read-only reconciliation probe:

```bash
ENV=dev ENV_FILE=.env.dev DB_NAME=<target_db> \
MIGRATION_ARTIFACT_ROOT=/tmp/project_positive_migration_visibility/<target_db>/<run_id> \
PROJECT_POSITIVE_MIGRATION_EXCEL_PATH=/mnt/tmp/001/672施工合同项目名称去重统计.xlsx \
PROJECT_POSITIVE_MIGRATION_RAW_CONTRACT_CSV=/mnt/tmp/raw/contract/contract.csv \
make project.positive_migration.reconcile.probe
```

Write the visibility refresh:

```bash
ENV=dev ENV_FILE=.env.dev DB_NAME=<target_db> \
MIGRATION_REPLAY_DB_ALLOWLIST=<target_db> \
MIGRATION_ARTIFACT_ROOT=/tmp/project_positive_migration_visibility/<target_db>/<run_id> \
PROJECT_POSITIVE_MIGRATION_EXCEL_PATH=/mnt/tmp/001/672施工合同项目名称去重统计.xlsx \
PROJECT_POSITIVE_MIGRATION_RAW_CONTRACT_CSV=/mnt/tmp/raw/contract/contract.csv \
make project.positive_migration.visibility.refresh.write
```

For production-supervised execution, follow the production command policy and
use the production runbook's environment wrapper. Do not run with `ENV=prod`
under autonomous Codex mode.

## Acceptance

The write command must print
`PROJECT_POSITIVE_MIGRATION_VISIBILITY_REFRESH=...` with:

- `visibility_exact_match: true`
- `missing_expected_active_ids: []`
- `unexpected_active_ids: []`
- `archived_kept_ids: []`

Development baseline observed on `sc_demo`:

- `excel_unique_names`: `672`
- `positive_excel_names_after_user_discard`: `669`
- `positive_resolved_name_count`: `669`
- `positive_unresolved_name_count`: `0`
- `user_discard_names`: `3`
- `direct_project_exemptions`: `43`
- `kept_project_count`: `711`
- `archived_project_count`: `183`
- `active_project_count_after`: `711`
- `inactive_project_count_after`: `183`

Different target databases may have different direct-project counts or total
project counts if their project master replay baseline differs. The invariant is
the exact active-set check above.

## Outputs

The reconciliation probe writes:

- `project_contract_fact_alias_reconciliation_v1.csv`
- `project_contract_fact_alias_reconciliation_v1.json`

The write command writes:

- `project_positive_migration_visibility_refresh_v1.csv`
- `project_positive_migration_visibility_refresh_v1.json`

The CSV includes retained and archived project ids, names, legacy project ids,
operation strategy, reason, source name, and fact counts.

## Rollback

This refresh is a visibility-only migration. To roll back a specific run, use
the output CSV to restore the previous visibility decision manually, or restore
the database snapshot taken before the write target. Business facts are not
deleted by this flow.

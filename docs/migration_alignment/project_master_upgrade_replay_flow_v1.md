# Project Master Upgrade Replay Flow v1

Status: `ready_for_acceptance_replay`

Task: `ITER-2026-05-07-PROJECT-MASTER-UPGRADE-REPLAY`

## Purpose

This flow turns the project master cleanup from two historical passes into one bounded replay entry:

1. regenerate the project anchor payload from the current raw project and visible contract facts;
2. write the project anchors into a guarded replay database by `legacy_project_id`;
3. run a read-only acceptance postcheck against the target database.

It is intended for acceptance/prod-sim replay. Adapter mode is file-only. Write mode is protected by the replay DB allowlist in `fresh_db_project_anchor_replay_write.py`.

## Current Business Facts

The accepted project master payload currently has `798` rows:

| Lane | Rows | Source |
| --- | ---: | --- |
| `project_master` | 754 | `tmp/raw/project/project.csv` |
| `project_master_contract_enriched` | 1 | project master row enriched by visible contract facts |
| `contract_visible_project_anchor` | 43 | visible contract facts whose `XMID` is absent from project master |

The current raw source `operation_strategy` distribution is:

| Strategy | Rows |
| --- | ---: |
| `joint` | 760 |
| `direct` | 36 |
| `unspecified` | 2 |

`project.project.operation_strategy` is required in the current model and defaults to `direct`, so replay normalizes the two unspecified source rows to `direct` at write time. The model-normalized acceptance distribution is `direct=38`, `joint=760`.

## Command

Full acceptance replay:

```bash
PROJECT_MASTER_REPLAY_MODE=all \
DB_NAME=sc_partner_acceptance \
MIGRATION_REPLAY_DB_ALLOWLIST=sc_partner_acceptance \
PROJECT_ANCHOR_EXPECTED_ROWS=798 \
bash scripts/migration/project_master_upgrade_replay_flow.sh
```

File-only adapter refresh:

```bash
PROJECT_MASTER_REPLAY_MODE=adapter \
bash scripts/migration/project_master_upgrade_replay_flow.sh
```

Read-only postcheck:

```bash
PROJECT_MASTER_REPLAY_MODE=postcheck \
DB_NAME=sc_partner_acceptance \
MIGRATION_REPLAY_DB_ALLOWLIST=sc_partner_acceptance \
PROJECT_ANCHOR_EXPECTED_ROWS=798 \
bash scripts/migration/project_master_upgrade_replay_flow.sh
```

## Outputs

The adapter still writes the canonical project replay assets:

- `artifacts/migration/fresh_db_project_anchor_replay_payload_v1.csv`
- `artifacts/migration/fresh_db_project_anchor_replay_gap_matrix_v1.csv`
- `artifacts/migration/fresh_db_project_anchor_replay_adapter_result_v1.json`
- `docs/migration_alignment/fresh_db_project_anchor_replay_adapter_report_v1.md`

The write and postcheck phases write under `MIGRATION_ARTIFACT_ROOT`:

- `fresh_db_project_anchor_replay_write_result_v1.json`
- `fresh_db_project_anchor_replay_rollback_targets_v1.csv`
- `fresh_db_project_master_replay_postcheck_result_v1.json`
- `fresh_db_project_master_replay_postcheck_report_v1.md`

## Acceptance Contract

The postcheck passes only when:

- payload rows equal the expected row count;
- each payload row has one non-empty `legacy_project_id`;
- no payload identity is duplicated;
- every payload `legacy_project_id` maps to exactly one `project.project`;
- matched project rows equal the expected row count;
- database `operation_strategy` distribution matches the model-normalized payload distribution;
- visible contract-derived project anchors have linked visible `construction.contract` rows when those fields exist.

Decision marker:

`project_master_replay_acceptance_passed`

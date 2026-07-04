# Project Master Replay Postcheck Report v1

Status: PASS

Task: `ITER-2026-05-07-PROJECT-MASTER-UPGRADE-REPLAY`

## Scope

Read-only acceptance check after the project master replay flow.

## Replay Facts

- database: `sc_partner_acceptance`
- payload rows: `798`
- expected rows: `798`
- matched project rows: `798`
- duplicate payload identities: `0`
- duplicate target identities: `0`
- missing target identities: `0`

## Source Lanes

```json
{
  "contract_visible_project_anchor": 43,
  "project_master": 754,
  "project_master_contract_enriched": 1
}
```

## Operation Strategy

```json
{
  "payload": {
    "direct": 36,
    "joint": 760,
    "unspecified": 2
  },
  "database": {
    "direct": 38,
    "joint": 760
  }
}
```

## Contract Linkage

```json
{
  "model_present": true,
  "missing_fields": [],
  "contract_visible_project_anchor_keys": 43,
  "visible_contract_rows": 48,
  "linked_visible_contract_rows": 48,
  "unlinked_visible_contract_rows": 0,
  "unlinked_samples": []
}
```

## Decision

`project_master_replay_acceptance_passed`

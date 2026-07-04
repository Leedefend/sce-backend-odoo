# Project Master Replay Postcheck Report v1

Status: PASS

Task: `ITER-2026-05-07-PROJECT-MASTER-UPGRADE-REPLAY`

## Scope

Read-only acceptance check after the project master replay flow.

## Replay Facts

- database: `sc_acceptance_audit_20260510`
- payload rows: `818`
- expected rows: `818`
- matched project rows: `818`
- duplicate payload identities: `0`
- duplicate target identities: `0`
- missing target identities: `0`

## Source Lanes

```json
{
  "contract_project_business_fact_anchor": 20,
  "contract_visible_project_anchor": 43,
  "project_master": 754,
  "project_master_contract_enriched": 1
}
```

## Operation Strategy

```json
{
  "payload_raw": {
    "direct": 36,
    "joint": 780,
    "unspecified": 2
  },
  "payload_model_normalized": {
    "direct": 38,
    "joint": 780
  },
  "database": {
    "direct": 38,
    "joint": 780
  },
  "unspecified_default": "direct"
}
```

## Contract Linkage

```json
{
  "model_present": true,
  "missing_fields": [],
  "contract_visible_project_anchor_keys": 43,
  "visible_contract_rows": 7,
  "linked_visible_contract_rows": 7,
  "unlinked_visible_contract_rows": 0,
  "unlinked_samples": []
}
```

## Decision

`project_master_replay_acceptance_passed`

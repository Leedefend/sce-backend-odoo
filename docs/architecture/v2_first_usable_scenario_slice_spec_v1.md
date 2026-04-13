# v2 First Usable Scenario Slice Spec v1

## Scope

This slice assembles the first user-usable scenario by composing migrated v2 chains.

Intent:

- `app.init`

Composed chain order:

1. `session.bootstrap`
2. `meta.describe_model`
3. `ui.contract`

## Runtime chain

`dispatcher -> app.init -> first scenario service -> chained intents -> scenario builder -> envelope`

## Output contract skeleton

- `session`
- `model_meta`
- `ui_contract`
- `chain_status`

This slice returns a single scenario initialization payload for frontend bootstrap.

## Guard rails

- Snapshot:
  - `artifacts/v2/first_scenario_contract_snapshot_v1.json`
- Dedicated audit:
  - `scripts/verify/v2_first_scenario_contract_audit.py`
- Governance gate integration:
  - `scripts/verify/v2_app_governance_gate_audit.py`

## Out of scope

- no `execute_button` write-path integration
- no deep XML/parser expansion
- no `api.data` read/write action chain

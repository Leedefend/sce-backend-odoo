# Unified Page Contract v2+ ActionContract Batch-D

Date: 2026-05-01
Status: Batch-D implementation note

## Layer Target

Contract Governance / ActionContract Consolidation

## Module

- `addons/smart_core/core/unified_page_contract_v2_action.py`
- `docs/architecture/unified_page_contract_v2/fixtures/action_contract_source.json`
- `docs/architecture/unified_page_contract_v2/fixtures/action_patch_source.json`
- `docs/architecture/unified_page_contract_v2/snapshots/action_contract_snapshot_v1.json`
- `scripts/verify/unified_page_contract_v2_action_guard.py`
- `Makefile`

## Reason

Existing interaction semantics are spread across onchange, page action schema, action policies, form save/validate/delete, and patch responses. v2+ requires these sources to be normalized into `ActionContract` so frontend runtimes dispatch stable `actionId` values and never implement business linkage logic.

## Source Mapping

| Source | v2+ output |
| --- | --- |
| `onchange_fields` / `changed_fields` | `triggerType=change`, `dispatchMode=serverDebounced` or `server`, `targetScope=widget`. |
| `action_schema.actions` | click action rules with server dispatch and target scope derived from intent category. |
| `action_policies` | button action rules using backend-governed availability as input, without executing business logic. |
| `form_actions.save` | `action.form.save` with `triggerType=submit` and `dispatchMode=serverBlocking`. |
| `form_actions.validate` | `action.form.validate` with `triggerType=confirm` and no refresh by default. |
| `delete_policy.allowed` | `action.record.delete` with `triggerType=delete` and server blocking dispatch. |
| `chain_actions` | dependency graph edges between action IDs, not executable client logic. |
| action result patch | `UnifiedPagePatch v2+` partial envelope with `layoutPatch/statusPatch/dataPatch/runtimePatch/meta`. |

## Anti-DSL Boundary

The normalizer does not emit:

- scripts
- expressions
- JSON logic
- BPMN
- workflow VM instructions
- frontend executable code

`ActionContract` remains a dispatch declaration. Semantic evaluation remains backend-owned.

## Upgrade Assessment

No Odoo model field, view, security, data XML, cron, or manifest dependency is added.

Result:

- `-u smart_core`: not required for this batch.
- service restart: not required for static validation; required only if a live Odoo worker must import the new module without process reload.

## Verification

Primary restricted target:

```bash
make verify.unified_page_contract.v2
```

Action-only target:

```bash
make verify.unified_page_contract.v2.action
```

## Rollback

Revert:

- `addons/smart_core/core/unified_page_contract_v2_action.py`
- `scripts/verify/unified_page_contract_v2_action_guard.py`
- `docs/architecture/unified_page_contract_v2/fixtures/action_contract_source.json`
- `docs/architecture/unified_page_contract_v2/fixtures/action_patch_source.json`
- `docs/architecture/unified_page_contract_v2/snapshots/action_contract_snapshot_v1.json`
- `Makefile` action target changes

No database rollback is required.

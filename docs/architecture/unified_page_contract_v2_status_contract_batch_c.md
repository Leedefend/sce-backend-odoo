# Unified Page Contract v2+ StatusContract Batch-C

Date: 2026-05-01
Status: Batch-C implementation note

## Layer Target

Contract Governance / StatusContract Consolidation

## Module

- `addons/smart_core/core/unified_page_contract_v2_status.py`
- `docs/architecture/unified_page_contract_v2/fixtures/status_contract_source.json`
- `docs/architecture/unified_page_contract_v2/snapshots/status_contract_snapshot_v1.json`
- `scripts/verify/unified_page_contract_v2_status_guard.py`
- `Makefile`

## Reason

Existing status semantics are spread across field metadata, field policies, action policies, modifiers, validation surfaces, permission surfaces, and access policies. v2+ requires these sources to be normalized into one terminal-neutral `StatusContract` so frontend runtimes do not infer role, permission, readonly, required, visibility, or action availability.

## Source Priority

The normalizer uses this precedence:

1. `permission_surface` / `access_policy` / `permissions` determine `globalStatus`.
2. field metadata supplies base `readonly` and `required`.
3. `field_policies` applies profile-aware visibility, readonly, required, disabled, and reason code.
4. `validation_surface` and `validation_rules` force required fields.
5. `modifiers` / `modifiers_patch` override dynamic visible, readonly, and required state.
6. `action_policies` generate `buttonStatus`.
7. `container_policies` generate `containerStatus`.
8. `selector_status` generates `selectorStatus` for batch and inherited status.

## Output Boundary

The normalizer emits only:

- `globalStatus`
- `containerStatus`
- `widgetStatus`
- `buttonStatus`
- `selectorStatus`

It does not execute actions, change business workflow, mutate permissions, or infer role in the frontend.

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

Status-only target:

```bash
make verify.unified_page_contract.v2.status
```

## Rollback

Revert:

- `addons/smart_core/core/unified_page_contract_v2_status.py`
- `scripts/verify/unified_page_contract_v2_status_guard.py`
- `docs/architecture/unified_page_contract_v2/fixtures/status_contract_source.json`
- `docs/architecture/unified_page_contract_v2/snapshots/status_contract_snapshot_v1.json`
- `Makefile` status target changes

No database rollback is required.

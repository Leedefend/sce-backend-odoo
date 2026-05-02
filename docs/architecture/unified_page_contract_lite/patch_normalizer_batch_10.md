# Unified Semantic Page Contract Lite - Patch Normalizer Batch 10

Date: 2026-05-02
Status: Phase 1 offline patch normalizer

## 1. Boundary

Layer Target: Contract Governance / Patch Source Normalizer

Module:

- `addons/smart_core/core/unified_page_contract_lite_patch_normalizer.py`
- `docs/architecture/unified_page_contract_lite/fixtures`
- `docs/architecture/unified_page_contract_lite/snapshots`
- `scripts/verify`
- `Makefile`

Reason:

Batch-9 normalized raw page sources. Batch-10 adds the equivalent offline normalizer for raw onchange/x2many patch payloads.

## 2. Responsibility

The patch normalizer owns raw onchange compatibility before the Lite patch adapter.

It may read:

- `value`
- `values`
- `modifiers`
- `button_status`
- `buttons`
- `x2many_changes`
- `x2many_patches`
- `relation_patches`
- `warning`
- `changed_fields`

It must output only:

```text
schema_version / patch / modifiers_patch / button_status_patch
line_patches / warnings / applied_fields
```

## 3. Guard

Batch-10 adds:

```text
scripts/verify/unified_page_contract_lite_patch_normalizer_guard.py
```

The guard verifies:

- the normalizer is side-effect-free
- legacy raw patch fixture output matches a normalized patch source snapshot
- normalized output is also accepted by the Batch-7 source guard

Fixture:

```text
docs/architecture/unified_page_contract_lite/fixtures/legacy_onchange_raw_patch_source_v1.json
```

Snapshot:

```text
docs/architecture/unified_page_contract_lite/snapshots/legacy_onchange_normalized_patch_source_snapshot_v1.json
```

## 4. Still Not Connected

This batch still does not:

- import the normalizer from handlers
- change `api.onchange`
- change `login`
- change `system.init`
- change `ui.contract` default output
- modify frontend runtime
- introduce `runtimeContract`

## 5. Decision

Future onchange integration must use this boundary:

```text
raw onchange/x2many patch
  -> patch normalizer
  -> normalized patch source
  -> Lite patch adapter
```

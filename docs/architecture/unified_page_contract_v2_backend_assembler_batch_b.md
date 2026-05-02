# Unified Page Contract v2+ Backend Assembler Batch-B

Date: 2026-05-01
Status: Batch-B implementation note

## Layer Target

Contract Governance / Backend Assembler

## Module

- `addons/smart_core/core/unified_page_contract_v2_assembler.py`
- `docs/architecture/unified_page_contract_v2/fixtures`
- `docs/architecture/unified_page_contract_v2/snapshots`
- `scripts/verify/unified_page_contract_v2_assembler_guard.py`
- `Makefile`

## Reason

Batch-A froze the v2+ protocol assets. Batch-B adds a backend-side canonical assembler so existing contract sources can be normalized into `UnifiedPageContract v2+` without changing the current public startup chain or frontend payload.

## Source Mapping

| Source | v2+ output |
| --- | --- |
| `scene_contract_v1` | Full `UnifiedPageContract v2+` with scene blocks mapped into `LayoutContract`, state mapped into `StatusContract`, actions mapped into `ActionContract`, and legacy source retained under `meta.compat.scene_contract_v1`. |
| `page_orchestration_v1` | Full `UnifiedPageContract v2+` with zones/blocks mapped into container/widget structure, action schema mapped into action rules, data sources mapped into `DataContract.dataSource`, and legacy source retained under `meta.compat.page_orchestration_v1`. |
| `ui.contract` | Full `UnifiedPageContract v2+` with model/view/fields mapped into page/layout/status contracts, and legacy source retained under `meta.compat.ui_contract`. |
| `api.onchange` | `UnifiedPagePatch v2+` partial patch with value changes mapped into `dataPatch`, modifiers mapped into `statusPatch`, and legacy source retained under `meta.compat.api_onchange`. |

## Compatibility Strategy

- No public intent name is changed.
- No controller default response is changed.
- Legacy payloads are never emitted at top level in v2+ output.
- Legacy sources are retained only in `meta.compat`.
- Invalid or unsupported `clientType` falls back to `web_pc`.

## Upgrade Assessment

No Odoo model field, view, security, data XML, cron, or manifest dependency is added.

Result:

- `-u smart_core`: not required for this batch.
- service restart: not required for static validation; required only if a live Odoo worker must import the new assembler without process reload.

## Verification

Primary restricted target:

```bash
make verify.unified_page_contract.v2
```

This target runs:

- schema/example guard
- assembler `py_compile`
- assembler mapping guard
- fixture-to-snapshot baseline checks

## Rollback

Revert:

- `addons/smart_core/core/unified_page_contract_v2_assembler.py`
- `scripts/verify/unified_page_contract_v2_assembler_guard.py`
- `docs/architecture/unified_page_contract_v2/fixtures`
- `docs/architecture/unified_page_contract_v2/snapshots/assembler_mapping_snapshot_v1.json`
- `Makefile` v2 assembler targets

No database rollback is required.

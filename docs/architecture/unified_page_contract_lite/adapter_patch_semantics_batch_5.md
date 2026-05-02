# Unified Semantic Page Contract Lite - Adapter Patch Semantics Batch 5

Date: 2026-05-01
Status: Phase 1 patch semantics expansion

## 1. Boundary

Layer Target: Contract Governance / Patch Semantics Expansion

Module:

- `addons/smart_core/core/unified_page_contract_lite_adapter.py`
- `docs/architecture/unified_page_contract_lite/fixtures`
- `docs/architecture/unified_page_contract_lite/snapshots`
- `scripts/verify/unified_page_contract_lite_adapter_guard.py`
- `Makefile`

Reason:

Batch-4 hardened patch layering. Batch-5 expands patch semantics while keeping the same layering rule:

```text
statusPatch owns status
dataPatch owns data
```

## 2. Added Patch Coverage

### Button Status Patch

Source:

```json
{
  "button_status_patch": {
    "save": {"visible": true, "disabled": false},
    "submit": {"visible": true, "disabled": true}
  }
}
```

Target:

```json
{
  "statusPatch": {
    "buttonStatus": [
      {"btnId": "btn.save", "visible": true, "disabled": false},
      {"btnId": "btn.submit", "visible": true, "disabled": true}
    ]
  }
}
```

### Relation Row Widget Status Patch

Source:

```json
{
  "line_patches": [
    {
      "field": "task_ids",
      "row_key": "row.10",
      "modifiers_patch": {
        "planned_hours": {"readonly": false, "required": true, "invisible": false}
      }
    }
  ]
}
```

Target:

```json
{
  "statusPatch": {
    "widgetStatus": [
      {
        "widgetId": "field.task_ids.row.10.planned_hours",
        "visible": true,
        "readonly": false,
        "required": true,
        "disabled": false
      }
    ]
  }
}
```

### Relation Row Data Patch

Row data remains in `dataPatch.relationData`:

```json
{
  "dataPatch": {
    "relationData": {
      "task_ids": {
        "linePatches": [
          {
            "field": "task_ids",
            "row_key": "row.10",
            "row_id": 10,
            "patch": {"planned_hours": 8},
            "row_state": "update",
            "command_hint": [1]
          }
        ]
      }
    }
  }
}
```

`dataPatch` still must not carry `modifiers_patch`, `readonly`, `required`, `invisible`, or `disabled`.

## 3. New Assets

Fixture:

```text
docs/architecture/unified_page_contract_lite/fixtures/onchange_patch_complex_source_v1.json
```

Snapshot:

```text
docs/architecture/unified_page_contract_lite/snapshots/onchange_patch_complex_lite_adapter_snapshot_v1.json
```

## 4. Guard Expansion

`scripts/verify/unified_page_contract_lite_adapter_guard.py` now supports repeated patch cases:

```text
--patch-case SOURCE SNAPSHOT
```

Coverage report now includes:

```json
{
  "patch_case_count": 2,
  "patch_has_button_status": true,
  "patch_has_relation_status": true,
  "patch_has_data": true,
  "patch_has_status": true
}
```

## 5. Still Not Connected

This batch still does not:

- modify `login`
- modify `system.init`
- modify `ui.contract` default output
- register an Odoo model
- add controller/intent routes
- modify frontend runtime
- introduce `runtimeContract`

## 6. Next Batch

Recommended next batch:

```text
Lite Phase 1 / Batch-6 - Adapter Runtime Readiness Audit
```

Focus:

- read-only audit of where adapter could be inserted later
- explicit no-touch list for startup chain
- candidate integration points and required gates
- no runtime connection yet

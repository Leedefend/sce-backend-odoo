# Unified Semantic Page Contract Lite - Adapter Governance Hardening Batch 4

Date: 2026-05-01
Status: Phase 1 guard hardening

## 1. Boundary

Layer Target: Contract Governance / Adapter Guard Hardening

Module:

- `scripts/verify/unified_page_contract_lite_adapter_guard.py`
- `addons/smart_core/core/unified_page_contract_lite_adapter.py`
- `docs/architecture/unified_page_contract_lite/snapshots`
- `Makefile`

Reason:

Before any runtime delivery connection, the Lite adapter needs hard guardrails for ID stability, side-effect-free behavior, patch layering, and coverage evidence.

## 2. Added Guardrails

### Stable ID Guard

The adapter guard now checks IDs across:

- `pageInfo.pageId`
- `pageInfo.sceneKey`
- `containerId`
- `widgetId`
- `fieldCode`
- `btnId`
- `actionId`
- `sourceWidgetId`

It blocks role/client/status drift suffixes such as:

```text
.admin / .user / .role / .web_pc / .wx_mini / .harmony_h5 / .readonly / .editable / .hidden / .visible
```

### Side-Effect-Free Adapter Guard

The adapter guard scans the adapter module and blocks public-runtime or ORM-side-effect tokens:

- `BaseIntentHandler`
- `INTENT_TYPE`
- `request`
- `from odoo`
- `env[`
- `.sudo(`
- `.search(`
- `.write(`
- `.create(`
- `.unlink(`

The adapter remains a pure helper, not a runtime handler.

### Patch Layering Guard

The guard enforces:

- `statusPatch` only contains `widgetStatus/buttonStatus`
- `dataPatch` only contains `mainData/relationData/dictData`
- `dataPatch` must not carry `readonly/required/invisible/disabled/modifiers_patch`
- `statusPatch` must not carry `mainData/relationData/dictData/linePatches`

The adapter now strips row-level `modifiers_patch` from `dataPatch.relationData.linePatches`.

### Coverage Report

`make verify.unified_page_contract.lite` writes:

```text
artifacts/backend/unified_page_contract_lite_adapter_coverage.json
```

Current coverage:

```json
{
  "contract_case_count": 3,
  "view_types": ["form", "search", "tree"],
  "patch_has_data": true,
  "patch_has_status": true,
  "side_effect_free": true
}
```

## 3. Still Not Connected

This batch still does not:

- modify `login`
- modify `system.init`
- modify `ui.contract` default output
- register an Odoo model
- add controller/intent routes
- modify frontend runtime
- introduce `runtimeContract`

## 4. Next Batch

Recommended next batch:

```text
Lite Phase 1 / Batch-5 - Adapter Patch Semantics Expansion
```

Focus:

- relation row status patch mapping, without leaking status into dataPatch
- buttonStatus patch examples
- full/partial patch compatibility rules
- no runtime delivery connection yet

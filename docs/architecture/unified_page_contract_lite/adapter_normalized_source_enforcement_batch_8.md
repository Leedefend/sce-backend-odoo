# Unified Semantic Page Contract Lite - Normalized Source Enforcement Batch 8

Date: 2026-05-02
Status: Phase 1 normalized source enforcement

## 1. Boundary

Layer Target: Contract Governance / Normalized Source Enforcement

Module:

- `addons/smart_core/core/unified_page_contract_lite_adapter.py`
- `scripts/verify/unified_page_contract_lite_adapter_guard.py`
- `docs/architecture/unified_page_contract_lite`

Reason:

Batch-7 froze the normalized source shape. Batch-8 enforces that shape inside the adapter implementation.

The adapter must no longer accept legacy/raw input aliases as a convenience fallback.

## 2. Removed Input Aliases

The adapter no longer reads these raw source aliases:

- `head.model`
- `head.view_type`
- `head.scene_key`
- `head.render_profile`
- `meta.semantic_page`
- root `model`
- root `view_type`
- `values`
- `mainData`
- `relationData`
- `dictData`
- `options`

Allowed normalized input remains:

- `semantic_page.model`
- `semantic_page.view_type`
- `page_id`
- `scene_key`
- `render_profile`
- `record`
- `relation_rows`
- `dict_data`

## 3. Guard Enforcement

`scripts/verify/unified_page_contract_lite_adapter_guard.py` now blocks adapter source code from reintroducing direct reads of:

```text
source.get("head")
source.get("meta")
source.get("model")
source.get("view_type")
source.get("values")
source.get("mainData")
source.get("relationData")
source.get("dictData")
source.get("options")
```

This is intentionally stricter than runtime compatibility. Compatibility must live before the adapter in a future normalization layer.

## 4. Still Not Connected

This batch still does not:

- import the adapter from handlers
- modify `login`
- modify `system.init`
- modify `ui.contract` default output
- modify frontend runtime
- add controller/model registration
- introduce `runtimeContract`

## 5. Decision

The Lite adapter is now a normalized-source-only transformer.

Future integration must provide a separate semantic source normalizer if it needs to translate legacy Odoo/native payloads.

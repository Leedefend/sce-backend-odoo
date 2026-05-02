# Unified Semantic Page Contract Lite - Adapter Source Shape Batch 7

Date: 2026-05-02
Status: Phase 1 normalized source shape

## 1. Boundary

Layer Target: Contract Governance / Adapter Source Shape

Module:

- `docs/architecture/unified_page_contract_lite`
- `scripts/verify`
- `Makefile`

Reason:

Batch-6 froze the runtime boundary. Batch-7 freezes the normalized source shape consumed by the offline Lite adapter.

The goal is to prevent future integration code from passing arbitrary Odoo/native payloads directly into Lite generation.

## 2. Contract Source Shape

Source schema:

```text
docs/architecture/unified_page_contract_lite/lite_adapter_source.schema.json
```

Required keys:

- `page_id`
- `scene_key`
- `client_type`
- `semantic_page`
- `fields`

Allowed normalized source areas:

- page identity: `page_id`, `scene_key`, `client_type`, `etag`, `trace_id`
- render mode: `render_profile`
- semantic page: `semantic_page`
- field metadata: `fields`
- backend semantic status inputs: `field_policies`, `modifiers`, `field_modifiers`, `access_policy`
- backend action inputs: `action_policies`, `onchange_fields`
- renderable data: `record`, `relation_rows`, `dict_data`

## 3. Patch Source Shape

Patch source schema:

```text
docs/architecture/unified_page_contract_lite/lite_adapter_patch_source.schema.json
```

Required keys:

- `schema_version`
- `patch`
- `modifiers_patch`
- `line_patches`

Allowed patch source areas:

- main field deltas: `patch`
- field status deltas: `modifiers_patch`
- button status deltas: `button_status_patch`
- x2many line deltas: `line_patches`
- diagnostics-only source context: `warnings`, `applied_fields`

## 4. Guard

Batch-7 adds:

```text
scripts/verify/unified_page_contract_lite_source_guard.py
```

It validates:

- source schemas keep the frozen required keys
- all current contract fixtures follow the normalized source shape
- all current patch fixtures follow the normalized patch source shape
- forbidden runtime-heavy keys stay out of source input

Forbidden examples:

- `runtimeContract`
- `componentRegistry`
- `capabilities`
- `dependencyGraph`
- `selectorStatus`
- `dataSource`
- `actionType`
- `chainAction`
- `jsonLogic`
- `workflowDsl`

## 5. Still Not Connected

This batch still does not:

- import the adapter from handlers
- change `login`
- change `system.init`
- change `ui.contract` default output
- modify frontend runtime
- add controller/model registration
- introduce `runtimeContract`

## 6. Decision

Future runtime integration must first normalize Odoo/native/page/onchange payloads into the source shapes defined here.

It must not pipe raw source payloads directly into the Lite adapter.

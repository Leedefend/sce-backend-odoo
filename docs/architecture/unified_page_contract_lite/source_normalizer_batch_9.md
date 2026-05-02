# Unified Semantic Page Contract Lite - Source Normalizer Batch 9

Date: 2026-05-02
Status: Phase 1 offline source normalizer

## 1. Boundary

Layer Target: Contract Governance / Source Normalizer

Module:

- `addons/smart_core/core/unified_page_contract_lite_source_normalizer.py`
- `docs/architecture/unified_page_contract_lite/fixtures`
- `docs/architecture/unified_page_contract_lite/snapshots`
- `scripts/verify`
- `Makefile`

Reason:

Batch-8 made the Lite adapter normalized-source-only. Batch-9 adds the offline normalizer that can translate legacy/raw Odoo/native page input into the Batch-7 normalized source shape.

## 2. Responsibility

The normalizer owns legacy/raw input compatibility before the adapter.

It may read:

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

It must output only:

```text
page_id / scene_key / client_type / semantic_page / fields
field_policies / action_policies / access_policy / modifiers / field_modifiers
onchange_fields / record / relation_rows / dict_data
```

## 3. Guard

Batch-9 adds:

```text
scripts/verify/unified_page_contract_lite_source_normalizer_guard.py
```

The guard verifies:

- the normalizer is side-effect-free
- the normalizer does not import or call the Lite adapter
- legacy raw fixture output matches a normalized source snapshot

Fixture:

```text
docs/architecture/unified_page_contract_lite/fixtures/legacy_project_form_raw_source_v1.json
```

Snapshot:

```text
docs/architecture/unified_page_contract_lite/snapshots/legacy_project_form_normalized_source_snapshot_v1.json
```

## 4. Still Not Connected

This batch still does not:

- import the normalizer from handlers
- import the adapter from handlers
- modify `login`
- modify `system.init`
- modify `ui.contract` default output
- modify frontend runtime
- add controller/model registration
- introduce `runtimeContract`

## 5. Decision

Future runtime integration must use this boundary:

```text
raw Odoo/native source
  -> source normalizer
  -> normalized source
  -> Lite adapter
```

The adapter remains normalized-source-only.

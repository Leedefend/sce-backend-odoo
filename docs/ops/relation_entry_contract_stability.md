# Relation Entry Contract Stability Guide

## Why
- Relation-field create behavior must be contract-driven and deterministic.
- Frontend must not guess `action/menu` or dictionary type from field name.

## Contract Fields
- `relation_entry.action_id`: create/maintain page entry action id.
- `relation_entry.menu_id`: optional menu id for route context.
- `relation_entry.can_create`: backend create ACL result.
- `relation_entry.create_mode`: `page | quick | disabled`.
- `relation_entry.default_vals`: default values for quick create.
- `relation_entry.reason_code`: explain why current mode is chosen.

## Expected UX Mapping
- `create_mode=page` and `action_id>0`:
  - option label: `+ 新建并维护...`
  - click -> route to model form `id=new`, and pass `default_*` from `relation_entry.default_vals`.
- `create_mode=quick`:
  - option label: `+ 快速新建...`
  - click -> prompt + create via API with `default_vals`.
- `create_mode=disabled`:
  - no create option.

## Typical Root Causes
- `NO_VISIBLE_ACTION`: no visible action/menu for relation model in current role/group.
- `PAGE_ENTRY_READONLY`: page entry exists but current role has no create right.
- `DICT_TYPE_UNRESOLVED`: dictionary relation missing resolvable `type` domain.

## End-to-End Troubleshooting
1. Check backend model field definition and domain (example `project_type_id -> sc.dictionary` + `type=project_type`).
2. Check relation model action/menu visibility under current user groups.
3. Inspect contract payload `fields.<name>.relation_entry`.
4. Verify frontend behavior strictly follows `create_mode`.
5. Verify route-level `default_*` is merged into create defaults on target form page.
6. If mismatch exists, fix contract assembly first, then frontend mapping.

## Guard Commands
- Fast local guard:
  - `python3 scripts/verify/relation_entry_contract_guard.py`
- Frontend quick gate (includes relation-entry guard):
  - `make verify.frontend.quick.gate`

## Current Implementation Anchors
- Backend assembler:
  - `addons/smart_core/app_config_engine/services/assemblers/page_assembler.py`
- Frontend form page:
  - `frontend/apps/web/src/pages/ContractFormPage.vue`

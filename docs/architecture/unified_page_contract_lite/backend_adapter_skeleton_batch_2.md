# Unified Semantic Page Contract Lite - Backend Adapter Skeleton Batch 2

Date: 2026-05-01
Status: Phase 1 backend skeleton

## 1. Boundary

Layer Target: Contract Governance / Backend Semantic Adapter

Module:

- `addons/smart_core/core/unified_page_contract_lite_adapter.py`
- `docs/architecture/unified_page_contract_lite/fixtures`
- `docs/architecture/unified_page_contract_lite/snapshots`
- `scripts/verify/unified_page_contract_lite_adapter_guard.py`
- `Makefile`

Reason:

Batch-1 froze the source-to-target mapping inventory. Batch-2 adds a pure backend adapter skeleton that can convert static semantic/native source payloads into Lite contract and Lite patch snapshots.

## 2. What This Batch Does

- Adds a side-effect-free Python adapter.
- Converts semantic page style input to:
  - `pageInfo`
  - `layoutContract`
  - `statusContract`
  - `actionContract`
  - `dataContract`
  - `meta`
- Converts current `api.onchange` shape to Lite patch:
  - `patch` -> `dataPatch.mainData`
  - `modifiers_patch` -> `statusPatch.widgetStatus`
  - `line_patches` -> `dataPatch.relationData`
- Adds fixtures and snapshots for one form contract and one onchange patch.
- Adds a guard that compares generated output against snapshots and blocks runtime-heavy or DSL-like fields.

## 3. What This Batch Does Not Do

- Does not modify `login`.
- Does not modify `system.init`.
- Does not modify `ui.contract` default output.
- Does not register an Odoo model.
- Does not add fields, views, security, data, or controllers.
- Does not alter frontend runtime.
- Does not introduce `runtimeContract`.
- Does not introduce component registry, capabilities, selector status, dependency graph, realtime, collaboration, or AI orchestration.

## 4. Odoo Module Impact

Module: `smart_core`

Impact type: pure Python helper under `addons/smart_core/core`

Upgrade assessment:

- `-u smart_core`: not required
- manifest change: not required
- database schema change: none
- security/data/view XML change: none
- live worker reload: only required when this module is imported by a future runtime path

## 5. Verification

Primary target:

```bash
make verify.unified_page_contract.lite
```

The target now runs:

- Lite schema/example/patch guard
- mapping inventory guard
- backend adapter snapshot guard

## 6. Next Batch

Recommended next batch:

```text
Lite Phase 1 / Batch-3 - Adapter Source Coverage Expansion
```

Scope:

- add tree/search/x2many-specific fixtures
- strengthen status mapping from field policies, modifiers, action policies, and access policy
- keep adapter side-effect-free

Do not connect the adapter to public delivery until source coverage and snapshot stability are proven.

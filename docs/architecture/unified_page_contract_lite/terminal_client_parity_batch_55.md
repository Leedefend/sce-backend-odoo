# Unified Semantic Page Contract Lite - Terminal Client Parity Batch 55

Date: 2026-05-03
Status: implemented guard

## 1. Boundary

Layer Target: Contract Verification / All-Terminal Coverage

Module:

- `scripts/verify`
- `docs/architecture/unified_page_contract_lite`
- `Makefile`

Reason:

All-terminal coverage must prove that Web PC, UniApp mini program, and Harmony
H5 share one Lite semantic contract before any terminal renderer is introduced.
This batch adds the first guard for that rule.

## 2. What This Batch Adds

This batch adds:

- `verify.unified_page_contract.lite.terminal_client_parity`
- semantic signature comparison for `web_pc`, `wx_mini`, and `harmony_h5`
- patch operation guard for `replace` and `merge`
- report output at `artifacts/backend/unified_page_contract_lite_terminal_client_parity.json`

## 3. What Is Compared

For every checked Lite contract, the guard compares terminal signatures built
from:

- `pageInfo.pageId`
- `pageInfo.sceneKey`
- `pageInfo.model`
- `pageInfo.viewType`
- `contractVersion`
- container IDs and container types
- widget IDs, field codes, widget types, and component keys
- widget status semantics
- button status semantics
- action IDs and server dispatch declarations
- renderable data keys

The guard changes only `pageInfo.clientType` while computing terminal variants.
If any semantic signature diverges across `web_pc`, `wx_mini`, and
`harmony_h5`, the guard fails.

## 4. Current Checked Inputs

The first parity set covers:

- `project_form_lite.example.json`
- `project_form_lite_adapter_snapshot_v1.json`
- `project_tree_lite_adapter_snapshot_v1.json`
- `project_search_lite_adapter_snapshot_v1.json`
- `patch_lite.example.json`
- `onchange_patch_lite_adapter_snapshot_v1.json`
- `onchange_patch_complex_lite_adapter_snapshot_v1.json`

## 5. Non-Goals

This batch does not:

- implement Web, mini program, or H5 renderer code
- add terminal-specific business fields
- change Lite schema
- change backend handler behavior
- enable Lite by default
- alter `login`
- alter `system.init`
- alter `ui.contract`

## 6. Verification

Run:

```bash
make verify.unified_page_contract.lite.terminal_client_parity
make verify.unified_page_contract.lite
```

## 7. Rollback

Code rollback:

```text
revert this guard batch commit
```

Runtime rollback:

```text
none required; this batch has no runtime path
```

# Unified Semantic Page Contract Lite - Terminal Consumer Boundary Batch 57

Date: 2026-05-03
Status: implemented boundary

## 1. Boundary

Layer Target: Frontend Contract Consumer / All-Terminal Coverage

Module:

- `frontend/apps/web/src/app/contracts`
- `scripts/verify`
- `docs/architecture/unified_page_contract_lite`
- `Makefile`

Reason:

All terminal renderers must enter through one shared Lite contract consumer
boundary. Before mini program or Harmony H5 rendering starts, the frontend must
have a stable boundary that exposes contract identity, widget IDs, field codes,
and action IDs without adding terminal-specific business inference.

## 2. What This Batch Adds

This batch adds:

- `unifiedPageContractLiteTerminal.ts`
- `verify.unified_page_contract.lite.terminal_consumer_boundary`
- a guard that prevents terminal-specific Lite contract copies

The boundary accepts only:

- `web_pc`
- `wx_mini`
- `harmony_h5`

## 3. Consumer Rule

Terminal renderers may consume:

- `clientType`
- `pageId`
- `sceneKey`
- `model`
- `viewType`
- `contractVersion`
- `widgetIds`
- `fieldCodes`
- `actionIds`

Terminal renderers must not infer:

- role
- permission
- default route
- capability
- business workflow
- data access policy

## 4. Non-Goals

This batch does not:

- add a mini program renderer
- add a Harmony H5 renderer
- change Web rendering behavior
- change Lite schema
- change backend handlers
- change `login`
- change `system.init`
- change `ui.contract`

## 5. Verification

Run:

```bash
make verify.unified_page_contract.lite.terminal_consumer_boundary
make verify.unified_page_contract.lite
```

## 6. Rollback

Code rollback:

```text
revert this boundary batch commit
```

Runtime rollback:

```text
none required; this batch has no runtime path
```

# Unified Semantic Page Contract Lite - Terminal Store Skeleton Batch 58

Date: 2026-05-03
Status: implemented skeleton

## 1. Boundary

Layer Target: Frontend Contract Consumer / All-Terminal Coverage

Module:

- `frontend/apps/web/src/app/contracts`
- `scripts/verify`
- `docs/architecture/unified_page_contract_lite`
- `Makefile`

Reason:

After the shared terminal consumer boundary, the next step is a thin store
skeleton that all terminal renderers can use. It must store only normalized Lite
terminal boundary data and must not fetch, route, render, or infer business
semantics.

## 2. What This Batch Adds

This batch adds:

- `unifiedPageContractLiteTerminalStore.ts`
- `createLiteTerminalContractStore`
- store coverage in `verify.unified_page_contract.lite.terminal_consumer_boundary`

The store supports only:

- `setFromContract`
- `get`
- `list`
- `clear`
- `snapshot`

## 3. Store Rule

The store accepts only values that pass `parseLiteTerminalContract`.

The stored value is `LiteTerminalConsumerBoundary`, which contains only:

- `clientType`
- `pageId`
- `sceneKey`
- `model`
- `viewType`
- `contractVersion`
- `widgetIds`
- `fieldCodes`
- `actionIds`

## 4. Non-Goals

This batch does not:

- use Pinia
- attach to session store
- call backend APIs
- parse route state
- infer role or permission
- render Web, mini program, or H5 UI
- change Lite schema
- change backend handlers

## 5. Verification

Run:

```bash
pnpm --dir frontend/apps/web run typecheck
make verify.unified_page_contract.lite.terminal_consumer_boundary
make verify.unified_page_contract.lite
```

## 6. Rollback

Code rollback:

```text
revert this store skeleton batch commit
```

Runtime rollback:

```text
none required; this batch has no runtime path
```

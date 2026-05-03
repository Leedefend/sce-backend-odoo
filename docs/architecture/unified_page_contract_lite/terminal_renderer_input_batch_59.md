# Unified Semantic Page Contract Lite - Terminal Renderer Input Batch 59

Date: 2026-05-03
Status: implemented skeleton

## 1. Boundary

Layer Target: Frontend Contract Consumer / All-Terminal Coverage

Module:

- `frontend/apps/web/src/app/contracts`
- `scripts/verify`
- `docs/architecture/unified_page_contract_lite`

Reason:

After the shared terminal store skeleton, terminal renderers need a common input
model. This batch creates that input model without attaching it to Web, mini
program, or Harmony H5 pages.

## 2. What This Batch Adds

This batch adds:

- `unifiedPageContractLiteTerminalRendererInput.ts`
- `LiteTerminalRendererInput`
- `createLiteTerminalRendererInput`
- `createLiteTerminalRendererInputSnapshot`

The input contains only:

- terminal client
- page identity
- model and view type
- contract version
- widget IDs
- field codes
- action IDs
- counts for widgets, fields, and actions

## 3. Consumer Rule

Renderer inputs must be created from `LiteTerminalConsumerBoundary` or
`LiteTerminalContractStoreSnapshot`.

Renderer inputs must not:

- call backend APIs
- read route state
- infer role
- infer permission
- infer default route
- infer capability
- execute actions
- render UI

## 4. Non-Goals

This batch does not:

- implement the Web renderer
- implement the mini program renderer
- implement the Harmony H5 renderer
- change the terminal store
- change Lite schema
- change backend handlers
- enable Lite by default

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
revert this renderer input batch commit
```

Runtime rollback:

```text
none required; this batch has no runtime path
```

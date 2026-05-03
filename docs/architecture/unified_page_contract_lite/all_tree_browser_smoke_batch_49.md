# Unified Semantic Page Contract Lite - All Tree Browser Smoke Batch 49

Date: 2026-05-03
Status: implemented validation smoke

## 1. Boundary

Layer Target: Frontend Contract Consumer / Lite all_tree Validation

Module:

- `scripts/verify`
- `Makefile`
- `docs/architecture/unified_page_contract_lite`

Reason:

The rollout switch already supports `VITE_LITE_CONTRACT_ROLLOUT=all_tree`.
Before using it in a shared environment, the project needs a repeatable browser
gate proving that selected tree/list actions can render from Lite v2.0 through
`load_contract` preview without falling back to legacy `ui.contract`.

## 2. Scope

This batch adds a host-side browser smoke only.

It validates:

- the frontend is started with `VITE_LITE_CONTRACT_ROLLOUT=all_tree`
- selected action ids are opened through `/a/<action_id>`
- action routing dispatches `load_contract`
- the response contains `load_contract Lite preview`
- there is no repeated action-phase `ui.contract` fallback
- table rows render
- no browser console or page errors appear

The action list is controlled by:

```text
LITE_ALL_TREE_ACTION_IDS
```

Default:

```text
506
```

## 3. Verification Target

```bash
make verify.unified_page_contract.lite.all_tree_browser.host
```

Expected frontend server:

```bash
VITE_LITE_CONTRACT_ROLLOUT=all_tree
```

Default URL:

```text
http://127.0.0.1:5176
```

## 4. Explicitly Not Changed

This batch:

- does not make Lite the default
- does not change `login`
- does not change `system.init`
- does not remove legacy fallback
- does not add mobile contract fields
- does not add runtimeContract
- does not change backend contract shape

## 5. Rollback

Runtime rollback:

```text
unset VITE_LITE_CONTRACT_ROLLOUT
```

Code rollback:

```text
revert this batch commit
```

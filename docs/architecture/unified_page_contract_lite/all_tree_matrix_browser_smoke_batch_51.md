# Unified Semantic Page Contract Lite - All Tree Matrix Browser Smoke Batch 51

Date: 2026-05-03
Status: implemented matrix smoke

## 1. Boundary

Layer Target: Frontend Contract Rollout Gate / Lite all_tree Matrix

Module:

- `scripts/verify`
- `Makefile`
- `docs/architecture/unified_page_contract_lite`

Reason:

The rollout now has one positive tree/list browser smoke and one negative
non-tree browser smoke. The next gate must avoid hardcoded-only coverage by
discovering available actions from the current backend nav and classifying them
with backend `ui.contract`.

## 2. Discovery Rule

The matrix smoke:

- logs in to the backend intent API
- calls `system.init`
- collects unique nav action ids
- calls legacy `ui.contract` for each action
- classifies `tree`/`list` as Lite expected
- classifies non-tree views as legacy expected
- requires at least one Lite case and one legacy case

This keeps view semantics backend-owned.

## 3. Browser Assertions

Target:

```bash
make verify.unified_page_contract.lite.all_tree_matrix_browser.host
```

Expected frontend server:

```text
VITE_LITE_CONTRACT_ROLLOUT=all_tree
```

Lite cases assert:

- `load_contract` is dispatched
- response contains Lite v2.0 preview
- repeated action-phase `ui.contract` calls do not occur
- table rows render

Legacy cases assert:

- `load_contract` is not dispatched
- action-phase `ui.contract` is used
- page is not blank

## 4. Controls

```text
LITE_ALL_TREE_MATRIX_LIMIT=8
```

The limit applies independently to Lite and legacy cases.

## 5. Explicitly Not Changed

This batch:

- does not make Lite the default
- does not change `login`
- does not change `system.init`
- does not remove legacy fallback
- does not add mobile contract fields
- does not add runtimeContract
- does not change backend contract shape

## 6. Rollback

Runtime rollback:

```text
unset VITE_LITE_CONTRACT_ROLLOUT
```

Code rollback:

```text
revert this batch commit
```

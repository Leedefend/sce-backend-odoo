# Unified Semantic Page Contract Lite - All Tree Acceptance Gate Batch 52

Date: 2026-05-03
Status: implemented acceptance gate

## 1. Boundary

Layer Target: Contract Rollout Gate / Lite all_tree Acceptance

Module:

- `Makefile`
- `scripts/verify`
- `docs/architecture/unified_page_contract_lite`

Reason:

The all_tree rollout now has three browser checks: a tree/list positive smoke,
a non-tree legacy negative smoke, and an auto-discovered matrix smoke. They need
one explicit host-side acceptance target before this branch can be treated as
ready for mainline review.

## 2. Acceptance Target

```bash
make verify.unified_page_contract.lite.all_tree_acceptance_browser.host
```

This target runs:

- `verify.unified_page_contract.lite.all_tree_browser.host`
- `verify.unified_page_contract.lite.all_tree_legacy_browser.host`
- `verify.unified_page_contract.lite.all_tree_matrix_browser.host`

Expected frontend server:

```text
VITE_LITE_CONTRACT_ROLLOUT=all_tree
```

Default frontend URL:

```text
http://127.0.0.1:5176
```

## 3. What It Proves

The acceptance target proves:

- a tree/list action can render through Lite preview
- a non-tree action does not dispatch `load_contract`
- backend-owned `ui.contract` view_type classification is respected
- the current nav action matrix has at least one Lite case and one legacy case
- no browser console or page errors are observed by the smoke scripts

## 4. Mainline Review Rule

Before enabling `VITE_LITE_CONTRACT_ROLLOUT=all_tree` in any shared environment,
the branch must pass:

```bash
make verify.unified_page_contract.lite
make verify.frontend.quick.gate
make verify.unified_page_contract.lite.all_tree_acceptance_browser.host
```

This is a review gate, not a default runtime switch.

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

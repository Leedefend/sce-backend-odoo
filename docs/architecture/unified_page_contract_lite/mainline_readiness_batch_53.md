# Unified Semantic Page Contract Lite - Mainline Readiness Batch 53

Date: 2026-05-03
Status: ready for mainline review

## 1. Decision

This branch is ready for mainline review with default runtime behavior unchanged.

Merge condition:

```text
allowed to merge while Lite remains default-off
```

Runtime condition:

```text
VITE_LITE_CONTRACT_ROLLOUT is unset by default
```

## 2. What Enters Mainline

The branch adds:

- Lite v2.0 frontend consumption behind explicit rollout flags
- `pilot` mode for `project.project:tree`
- `all_tree` mode for governed tree/list action candidates
- legacy fallback for invalid or missing Lite preview
- backend-owned view type preflight when nav meta lacks `view_modes`
- positive, negative, and matrix browser acceptance gates

## 3. What Does Not Enter Mainline

This branch does not:

- does not make Lite the default
- does not change `login`
- does not change `system.init`
- does not replace legacy `ui.contract`
- does not remove legacy fallback
- does not add mobile contract fields
- does not add runtimeContract
- does not change backend contract shape
- does not add frontend business semantic inference

## 4. Required Merge Review Gates

Before merging this branch, run:

```bash
make verify.unified_page_contract.lite
make verify.frontend.quick.gate
make verify.docs.all
```

Before enabling `VITE_LITE_CONTRACT_ROLLOUT=all_tree` in a shared environment,
also run:

```bash
make verify.unified_page_contract.lite.all_tree_acceptance_browser.host
```

The browser target requires a frontend dev server started with:

```text
VITE_LITE_CONTRACT_ROLLOUT=all_tree
```

## 5. Current Acceptance Evidence

Latest accepted browser evidence:

- positive Lite smoke: `artifacts/playwright/lite_all_tree_rollout/20260503T025940/summary.json`
- legacy fallback smoke: `artifacts/playwright/lite_all_tree_legacy_rollout/20260503T030019/summary.json`
- matrix smoke: `artifacts/playwright/lite_all_tree_matrix_rollout/20260503T030050/summary.json`

Current discovered matrix:

- `506`: `tree`, expected Lite
- `642`: `kanban`, expected legacy

## 6. Remaining Risks

Known remaining risks:

- all_tree coverage currently depends on available demo nav actions
- broader model coverage will grow as more menu actions are exposed in the DB
- full shared-environment enablement still requires the acceptance browser gate

These risks do not block mainline merge because default runtime remains off.

## 7. Rollback

Runtime rollback:

```text
unset VITE_LITE_CONTRACT_ROLLOUT
unset VITE_LITE_CONTRACT_PILOT
```

Code rollback:

```text
revert commits after origin/main on codex/contract-governance-lite-next
```

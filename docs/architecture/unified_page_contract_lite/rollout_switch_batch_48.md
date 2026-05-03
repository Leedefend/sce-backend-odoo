# Unified Semantic Page Contract Lite - Rollout Switch Batch 48

Date: 2026-05-03
Status: implemented default-off

## 1. Boundary

Layer Target: Frontend Contract Consumer / Lite Rollout Switch

Module:

- `frontend/apps/web/src/app/runtime/unifiedPageContractLitePilot.ts`
- `frontend/apps/web/src/env.d.ts`
- `scripts/verify`
- `docs/architecture/unified_page_contract_lite`
- `Makefile`

Reason:

Lite v2.0 is already absorbed into mainline. The next step toward a broader
contract switch is to add a governed rollout switch before expanding runtime
coverage. This keeps the rollout auditable and reversible.

## 2. Rollout Modes

Default mode:

```text
off
```

Pilot mode:

```text
VITE_LITE_CONTRACT_ROLLOUT=pilot
```

Equivalent legacy pilot flag:

```text
VITE_LITE_CONTRACT_PILOT=1
```

Broad tree/list candidate mode:

```text
VITE_LITE_CONTRACT_ROLLOUT=all_tree
```

## 3. Behavior

`legacy `ui.contract` remains the default path` when no rollout flag is set.

When `pilot` is enabled:

- only `project.project:tree` is a Lite candidate
- invalid or missing Lite preview falls back to legacy `ui.contract`

When `all_tree` is enabled:

- tree/list action contracts with a known model become Lite candidates
- non-tree views stay on legacy `ui.contract`
- invalid or missing Lite preview falls back to legacy `ui.contract`

## 4. Explicitly Not Changed

This batch:

- does not change `login`
- does not change `system.init`
- does not make Lite the default
- does not remove legacy fallback
- does not add mobile contract fields
- does not add runtimeContract
- does not add frontend business semantic inference

## 5. Next Gate

Before enabling `all_tree` in a shared environment, a live browser matrix must
prove:

- at least one pilot page still uses Lite
- non-tree views still use legacy `ui.contract`
- fallback works when Lite preview is unavailable
- no console/page errors appear

## 6. Verification

```bash
make verify.unified_page_contract.lite.rollout_switch
make verify.unified_page_contract.lite
make verify.frontend.quick.gate
```

## 7. Rollback

Runtime rollback:

```text
unset VITE_LITE_CONTRACT_ROLLOUT
unset VITE_LITE_CONTRACT_PILOT
```

Code rollback:

```text
revert this batch commit
```

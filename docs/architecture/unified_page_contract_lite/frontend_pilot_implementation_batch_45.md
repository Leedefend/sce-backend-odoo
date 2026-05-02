# Unified Semantic Page Contract Lite - Frontend Pilot Implementation Batch 45

Date: 2026-05-02
Status: implemented behind default-off feature flag

## 1. Boundary

Layer Target: Frontend Contract Consumer / Lite v2.0 Pilot

Module:

- `frontend/apps/web/src/app/contracts`
- `frontend/apps/web/src/app/runtime`
- `frontend/apps/web/src/api`
- `frontend/apps/web/src/app/resolvers`
- `scripts/verify`
- `Makefile`

Reason:

Lite v2.0 is frozen for frontend consumption. The frontend can now implement a
single controlled pilot without changing default runtime behavior.

## 2. Scope

Implemented pilot:

```text
project.project:tree
```

Source entry:

```text
load_contract opt-in preview
```

Feature flag:

```text
VITE_LITE_CONTRACT_PILOT=0
```

Default behavior remains off.

## 3. Implementation Shape

Frontend implementation order:

```text
schema/types -> store/adapter -> page renderer
```

Actual implementation:

- `unifiedPageContractLite.ts`: frozen Lite v2.0 type and validator
- `unifiedPageContractLitePilot.ts`: default-off pilot gate and adapter
- `api/contract.ts`: `load_contract` opt-in preview request
- `actionResolver.ts`: pilot selection before legacy fallback

The page renderer is not globally replaced. Existing `ActionView` continues to
consume its existing action-view contract shape. The pilot adapter maps Lite
v2.0 into that existing shape for the single allowlisted page.

## 4. Runtime Rules

Allowed only when:

- `VITE_LITE_CONTRACT_PILOT=1`
- action meta model is `project.project`
- action view mode is empty, `tree`, or `list`
- `load_contract` returns valid `lite_preview`
- `payloadType=lite_contract`
- payload validates as Lite v2.0

Fallback:

- feature flag off -> legacy `ui.contract`
- non-allowlisted action -> legacy `ui.contract`
- missing/invalid `lite_preview` -> legacy `ui.contract`

## 5. Explicitly Not Changed

This batch does not:

- change `login`
- change `system.init`
- consume `ui.contract` as Lite
- make Lite default
- remove legacy fallback
- introduce `runtimeContract`
- introduce selector status
- introduce dependency graph
- introduce frontend business semantic inference

## 6. Guard

The frontend runtime negative guard now allows Lite tokens only inside the
pilot files:

```text
frontend/apps/web/src/api/contract.ts
frontend/apps/web/src/app/contracts/unifiedPageContractLite.ts
frontend/apps/web/src/app/runtime/unifiedPageContractLitePilot.ts
```

All other frontend files remain Lite-free.

Required target:

```bash
make verify.unified_page_contract.lite.frontend_pilot_implementation
```

## 7. Rollback

Runtime rollback:

```text
set VITE_LITE_CONTRACT_PILOT=0 and redeploy frontend
```

Code rollback:

```text
revert this batch commit
```

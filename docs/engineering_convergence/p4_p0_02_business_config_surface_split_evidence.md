# P4-P0-02 Business Config Surface Split Evidence

Date: 2026-07-12
Branch: `topic/p4-p0-02-business-config-surface-split`
Parent plan: `p0_split_plan_execution.md`

## Scope

This pass keeps backend contracts and user-visible behavior stable while reducing the route component's mixed responsibilities.

Extracted files:

| File | Responsibility |
| --- | --- |
| `frontend/apps/web/src/views/businessConfigSurface/formatters.ts` | Pure labels, field formatting, view-type display, coverage row display, and list parsing helpers. |
| `frontend/apps/web/src/views/businessConfigSurface/snapshotRemediation.ts` | Snapshot filename normalization and remediation plan generation. |
| `frontend/apps/web/src/views/businessConfigSurface/navigation.ts` | Navigation-tree parsing for the menu configuration entry. |
| `frontend/apps/web/src/views/businessConfigSurface/style.css` | Scoped page styles previously embedded in the route component. |

## Line Count Evidence

| File | Before | After |
| --- | ---: | ---: |
| `frontend/apps/web/src/views/BusinessConfigSurfaceView.vue` | 5447 | 3334 |

The route component remains in the P0 split-plan queue after this pass. The next pass should extract child panels or composables for the page picker, delivery readiness, list/search editor, analysis editor, approval editor, and version workbench.

## Non-Scope

- No backend contract change.
- No low-code boundary policy change.
- No menu or permission policy change.
- No visual redesign.
- No browser-flow behavior change intended.

## Verification

```text
scripts/dev/pnpm_exec.sh -C frontend/apps/web lint:src
scripts/dev/pnpm_exec.sh -C frontend/apps/web typecheck:strict
scripts/dev/pnpm_exec.sh -C frontend/apps/web build
```

Latest local result:

```text
frontend lint: passed
frontend strict typecheck: passed
frontend build: passed
```

Latest remote result:

```text
GitHub Actions v1.1 quality gate: passed
Run: 29189862161
Duration: 2m30s
Head: e75141461
```

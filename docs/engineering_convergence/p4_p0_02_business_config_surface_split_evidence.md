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
| `frontend/apps/web/src/views/businessConfigSurface/BusinessConfigStartPanel.vue` | Initial workbench landing surface and compact delivery-readiness panel. |
| `frontend/apps/web/src/views/businessConfigSurface/BusinessConfigCoverageWorkspace.vue` | Page coverage picker, selected-page configuration cards, and delivery-readiness rail. |
| `frontend/apps/web/src/views/businessConfigSurface/BusinessConfigAdvancedAuditPanels.vue` | Advanced coverage details and snapshot compare/remediation panels. |
| `frontend/apps/web/src/views/businessConfigSurface/BusinessConfigApprovalPanel.vue` | Approval policy editor panel. |
| `frontend/apps/web/src/views/businessConfigSurface/BusinessConfigVersionPanel.vue` | Configuration version history and rollback panel. |
| `frontend/apps/web/src/views/businessConfigSurface/BusinessConfigEditorPanels.vue` | List/search and analysis editor panels. |
| `frontend/apps/web/src/views/businessConfigSurface/LowCodeFieldChipEditor.vue` | Shared draggable field-chip editor used by list/search and analysis panels. |

## Line Count Evidence

| File | Before | After |
| --- | ---: | ---: |
| `frontend/apps/web/src/views/BusinessConfigSurfaceView.vue` | 5447 | 2567 |

The route component remains in the P0 split-plan queue after this pass because the Vue split-plan threshold is 1500 lines. The next pass should extract stateful composables for coverage workflows, list/search and analysis editors, approval policy editing, and version rollback orchestration.

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
Run: 29189974512
Duration: 2m30s
Head: ea6fef962
```

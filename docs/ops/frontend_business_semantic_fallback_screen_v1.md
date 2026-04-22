# Frontend Business Semantic Fallback Screen v1

next_candidate_family: `backend semantic-supply for user-facing business copy`

family_scope: `ContractFormPage scene/runtime text, action_semantics reason copy, ReleaseProductEntryView descriptions, HomeView workflow status labels`

reason: `These candidates all require the backend to become the source of user-facing business wording. If the frontend keeps any of them, it must continue inventing business semantics. By contrast, the remaining dashboard/detail/context candidates are mostly consumer-boundary cleanup and compat-exit work that can wait until the backend text source is available.`

## Candidate Family Classification

### Family A: Must move to backend semantic-supply first

- `frontend/apps/web/src/pages/ContractFormPage.vue`
  reason: runtime panel, page title/subtitle, and overview cards still embed business wording that should come from scene/runtime/page contract text.
- `frontend/apps/web/src/app/action_semantics.ts`
  reason: reason-code to message mapping is backend-owned business copy, not frontend-owned fallback.
- `frontend/apps/web/src/views/ReleaseProductEntryView.vue`
  reason: released-scene descriptions and scope text are product/delivery semantics and should come from backend delivery contract.
- `frontend/apps/web/src/views/HomeView.vue`
  reason: workflow status labels like `当前步骤/已完成/下一步` are backend-owned process semantics.

### Family B: Frontend cleanup-only candidates, but should follow Family A

- `frontend/apps/web/src/views/ProjectManagementDashboardView.vue`
  reason: local action/empty-state fallback wording can be cleaned further, but several remaining labels should ideally consume backend-provided copy first.
- `frontend/apps/web/src/views/RecordView.vue`
  reason: section titles and action wording can be narrowed further, but this is mostly a consumer cleanup pass after backend copy sources exist.
- `frontend/apps/web/src/app/projectEntryContext.ts`
  reason: compat-exit for legacy alias acceptance depends on backend contract rollout timing.
- `frontend/apps/web/src/views/ActionView.vue`
  reason: the current issue is mainly comment/documentation hygiene and does not block semantic ownership recovery.

## Decision

Result: `PASS`

Recommended next implementation line: `Open one dedicated backend semantic-supply batch for user-facing business copy, and do not reopen frontend cleanup before that family lands.`

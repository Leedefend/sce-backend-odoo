# Phase 12 Stage 3: Blocked Action Suggested-Run UX

## Goal
When payment request semantic actions are blocked, let users run backend-provided suggested actions directly from form UI.

## Scope
- `frontend/apps/web/src/pages/ModelFormPage.vue`

## Delivered
- Added runnable suggested-action button on blocked semantic action hints.
- Reused shared suggested-action runtime (`useSuggestedAction`) for consistency and trace coverage.
- Added user feedback for suggested-action execution success/failure.

## Verification
- `make verify.frontend.typecheck.strict`
- `make verify.frontend.build`
- `make verify.frontend.suggested_action.all`

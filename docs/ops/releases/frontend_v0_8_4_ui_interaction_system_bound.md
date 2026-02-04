# Frontend v0.8.4 – UI Interaction + System-Bound Gates

Date: 2026-02-04

## Scope
- Layout tree renderer + coverage HUD (RecordView/ModelFormPage)
- System-bound bootstrap (dev/test only) to run semantic gates without credentials
- execute_button dry_run pipeline + smoke
- Chatter MVP (read + post)

## Verification (system-bound)
Run with bootstrap secret (dev/test only):

```
SC_BOOTSTRAP_SECRET=test-secret \
SC_BOOTSTRAP_LOGIN=svc_project_ro \
make verify.portal.ui.v0_8.semantic.container \
  DB_NAME=sc_demo MVP_MODEL=project.project \
  BOOTSTRAP_SECRET=test-secret BOOTSTRAP_LOGIN=svc_project_ro
```

Artifacts (PASS):
- /mnt/artifacts/codex/portal-shell-v0_8-semantic/20260204T074052
- /mnt/artifacts/codex/portal-shell-v0_8-semantic/20260204T074055
- /mnt/artifacts/codex/portal-shell-v0_8-semantic/20260204T074057

execute_button dry_run smoke (PASS):
- /mnt/artifacts/codex/portal-shell-v0_8-semantic/20260204T075111

## Security Notes
- session.bootstrap is dev/test only and requires SC_BOOTSTRAP_SECRET
- when SC_BOOTSTRAP_SECRET is missing, handler returns 404 (hidden)

## Rollback
- unset SC_BOOTSTRAP_SECRET / SC_BOOTSTRAP_LOGIN to disable bootstrap
- revert frontend renderer changes (no DB/schema changes)

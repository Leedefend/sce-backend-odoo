# E2E User Contract (Phase 9.4)

Status: Active (Phase 9.9)

## Purpose
Define a stable, minimal-permission user for UI-level E2E smokes and CI runs.

## Canonical User
- Login: `svc_e2e_smoke`
- Password: defined by environment (`E2E_PASSWORD`)
  - Demo default: `demo`

## Minimum Capabilities
- Login via JWT/session
- Access `projects.list` (list layout + default sort)
- Access portal lifecycle via bridge

## Notes
- `svc_e2e_smoke` is the canonical UI smoke user for CI and gate runs.
- `demo_pm` remains for demos and manual UI walkthroughs.
- Service-only accounts (`svc_project_ro`) are not UI smoke users.

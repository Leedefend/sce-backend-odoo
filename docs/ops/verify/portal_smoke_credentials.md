# Portal Smoke Credentials (Pre-Release)

Status: Phase 9.9

## Purpose
These credentials are required for container-based portal smokes and should represent
an interactive user with minimal read access (not a service-only account).

## Required Capabilities
- Can log in via JWT/session.
- Can access `projects.list` (scene list profile / default sort).
- Can access portal lifecycle via bridge.

## Canonical Smoke User (CI/Gate)
`svc_e2e_smoke` is the canonical E2E smoke user for CI and gate runs.
Service accounts (`svc_*`) are not expected to pass UI-level smokes.

## Recommended Environment Variables
Provide these at runtime (do not hardcode in CI configs):

- Canonical: `E2E_LOGIN=svc_e2e_smoke`
- `E2E_PASSWORD=demo`

## svc_* Accounts (Non-Blocking)
- `svc_project_ro` is a read-only service account; 401 in UI smokes is expected.
- `svc_e2e_smoke` is the only svc_* account intended for UI smokes.

## E2E Contract
- See `docs/ops/verify/e2e_user_contract.md` for Phase 9.4 definition.

## Verified Result (Demo Data)
When demo seed data is present, `svc_e2e_smoke` with password `demo` passes the container smokes.

## Demo Data Default
If demo data is loaded, `svc_e2e_smoke` is created with password `demo`.
Override in CI by setting `E2E_PASSWORD`.

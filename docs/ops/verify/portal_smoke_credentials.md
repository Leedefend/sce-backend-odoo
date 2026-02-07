# Portal Smoke Credentials (Pre-Release)

Status: RC-1

## Purpose
These credentials are required for container-based portal smokes and should represent
an interactive user with minimal read access (not a service-only account).

## Required Capabilities
- Can log in via JWT/session.
- Can access `projects.list` (scene list profile / default sort).
- Can access portal lifecycle via bridge.

## RC / CI Canonical Smoke User (RC-1)
RC verification uses `demo_pm` as the canonical E2E smoke user.
Service accounts (`svc_*`) are not expected to pass UI-level smokes.

## Recommended Environment Variables
Provide these at runtime (do not hardcode in CI configs):

- RC canonical: `E2E_LOGIN=demo_pm`
- `E2E_PASSWORD=demo`

## svc_* Accounts (Non-Blocking)
- `svc_project_ro` is a read-only service account; 401 in UI smokes is expected.
- `svc_e2e_smoke` is reserved for future CI hardening and is not required for RC.

## Verified Result (Demo Data)
When demo seed data is present, `demo_pm` with password `demo` passes the container smokes.

## Demo Data Default
If demo data is loaded, `svc_e2e_smoke` is created with password `demo`.
Override in CI by setting `E2E_PASSWORD`.

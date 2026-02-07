# Portal Smoke Credentials (Pre-Release)

Status: RC-1

## Purpose
These credentials are required for container-based portal smokes and should represent
an interactive user with minimal read access (not a service-only account).

## Required Capabilities
- Can log in via JWT/session.
- Can access `projects.list` (scene list profile / default sort).
- Can access portal lifecycle via bridge.

## Recommended Environment Variables
Provide these at runtime (do not hardcode in CI configs):

- Primary: `E2E_LOGIN=svc_e2e_smoke`
- `E2E_PASSWORD=<set in environment>`

## Verified Fallback (Demo Data)
If demo seed data is present, `demo_pm` with password `demo` passes the container smokes.

## Demo Data Default
If demo data is loaded, `svc_e2e_smoke` is created with password `demo`.
Override in CI by setting `E2E_PASSWORD`.

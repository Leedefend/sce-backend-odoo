# Current Architecture Boundary (Pre-Release)

Status: Transitional (pre-release hardening)

## Dual UI Planes
- SPA (Portal Shell): `frontend/apps/web`
- Odoo Portal Pages: `/portal/*` (server-rendered templates + portal JS)

## Dual Auth Model
- SPA API: JWT via `Authorization: Bearer`
- Portal Pages: Odoo session cookie
- Bridge: `/portal/bridge` binds JWT -> Odoo session and redirects

## Transitional Elements
- `act_url` is transitional and should not be a long-term navigation backbone.
- Workbench is a diagnostic-only surface (not product UI).

## SPA API No-Cookie Rule
- All SPA API requests must omit cookies and rely on JWT only.
- Cookie-based auth is reserved for Odoo server-rendered pages.

## Meta Rule
No architecture refactor beyond the pre-release hardening task list is allowed before release.

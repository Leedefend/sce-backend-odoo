# Architecture Audit Summary (Pre-Release)

Date: 2026-02-07
Branch: `main`
Perspective: System Architect

## 1) System Topology
- Core runtime: Odoo 17 + custom modules (Smart Core + Smart Construction suites).
- API gateway: `/api/v1/intent` (Smart Core intent dispatcher). Single entry point for app shell.
- UI surfaces:
  - Portal Shell (custom SPA) at `frontend/apps/web`.
  - Odoo server-rendered portal pages (`/portal/*`) for lifecycle/capability/dashboard.
- Data plane: Odoo ORM; no separate service DB.

## 2) Primary Execution Paths
- App init:
  - SPA -> `POST /api/v1/intent` with `intent=app.init` (aliased to `system.init`).
  - Requires Bearer token (JWT) unless anonymous allowlist.
- Navigation:
  - Menu click -> menu resolver -> action route `/a/:actionId` or scene `/s/:sceneKey`.
  - Directory menus auto-redirect to first resolvable child.
- Scene routing:
  - Scene target resolves to `action_id` / `model` / `route` with fallback logic.
- Action execution:
  - Act window: renders list/kanban via data contract.
  - Act url: treated as external navigation, portal bridge used for `/portal/*`.

## 3) Security Model
- Auth:
  - JWT token in `Authorization: Bearer` for SPA API calls.
  - Odoo session cookie used for server-rendered portal pages.
- Token bridge:
  - `/portal/bridge` validates JWT -> binds Odoo session -> redirects to `/portal/*`.
  - `st` query param propagated for portal API calls.
- Risks:
  - Dual-auth stack (JWT + cookie) increases surface area.
  - Cookie contamination can break portal flows; SPA now omits cookies for API calls.

## 4) Contract & Intent System
- `intent_dispatcher` normalizes CORS + error envelopes.
- Contract service provides view/action/menu/scene data.
- Intent allowlist: only a small anonymous set; everything else requires valid token.

## 5) Scene & Navigation Architecture
- Scene orchestration module provides registry + target resolution.
- Runtime normalization upgrades legacy targets and resolves missing action/menu IDs.
- Workbench is strictly an exception surface, not product UI.

## 6) Portal Architecture
- Odoo portal routes render templates and load portal JS bundle.
- Portal JS talks to `/api/portal/contract` and other portal APIs.
- Token is injected via `st` and read client-side for API calls.

## 7) Observability / Diagnostics
- Workbench now exposes detailed diagnostic fields (action type, contract type, URLs).
- Intent dispatcher embeds trace IDs and CORS headers consistently.

## 8) Release Readiness Risks (Architectural)
- Split UI planes (SPA vs Odoo portal) create duplicated navigation logic.
- Act URL handling is brittle across domains; long-term fix is SPA-native portal views.
- JWT session bridge introduces auth coupling; must be well documented and tested.

## 9) Architecture Recommendations (Pre-Release)
- Short-term:
  - Keep bridge; enforce token-only API in SPA.
  - Add smoke test covering `portal/bridge` + `/portal/lifecycle` end-to-end.
- Mid-term:
  - Move portal pages into SPA routes to eliminate Odoo page rendering dependency.
  - Replace act_url with scene routes for all core menu entries.
- Long-term:
  - Consolidate auth into single mechanism (JWT or session) to reduce drift.

## 10) Key Artifacts
- Intent gateway: `addons/smart_core/controllers/intent_dispatcher.py`
- Scene registry: `addons/smart_construction_scene/scene_registry.py`
- Portal bridge: `addons/smart_construction_portal/controllers/portal_controller.py`
- SPA action handling: `frontend/apps/web/src/views/ActionView.vue`

---
End of summary.

# Portal Assets Boundary

Purpose
- Keep portal assets isolated from Odoo backend UI bundles.
- Prevent coupling to @web/* modules and backend widgets.

Rules
- Portal assets must only live in smart_construction_portal and be loaded via a dedicated bundle.
- Do not add portal assets to web.assets_backend or web.assets_frontend.
- Portal code must not import or require @web/* modules.
- Portal should only consume Contract + Meta APIs (read-only in N3).

Bundle
- Bundle name: smart_construction_portal.assets_portal
- Page entry: /portal/lifecycle

Feature flag
- sc.portal.lifecycle.enabled controls route availability and menu exposure.

# Platform Entry Occupation Audit (Phase A-3 / Scan)

- Stage: `scan` (fact-only, no final ownership conclusion)
- Scan source: bounded `rg` over `addons/smart_construction_core`, `addons/smart_core`, `addons/smart_construction_scene`, `frontend`
- Target families: `/api/login`, `/api/session/get`, `/api/menu/tree`, `/api/capabilities/*`, `/api/scenes/*`, `/api/ops/*`, `/api/packs/*`

## `/api/login`

- definition_count: `1`
- reference_count: `0`
- definitions_in_smart_construction_core: `1`
- definitions_in_smart_core: `0`
- definitions_in_smart_construction_scene: `0`

### Definition Evidence

- `addons/smart_construction_core/controllers/frontend_api.py:92` → `@http.route('/api/login', type='json', auth='public', csrf=False, cors='*', methods=['POST'])`

### Reference Evidence

- none

## `/api/session/get`

- definition_count: `1`
- reference_count: `0`
- definitions_in_smart_construction_core: `1`
- definitions_in_smart_core: `0`
- definitions_in_smart_construction_scene: `0`

### Definition Evidence

- `addons/smart_construction_core/controllers/frontend_api.py:131` → `@http.route('/api/session/get', type='json', auth='public', csrf=False, cors='*', methods=['POST'])`

### Reference Evidence

- none

## `/api/menu/tree`

- definition_count: `1`
- reference_count: `2`
- definitions_in_smart_construction_core: `1`
- definitions_in_smart_core: `0`
- definitions_in_smart_construction_scene: `0`

### Definition Evidence

- `addons/smart_construction_core/controllers/frontend_api.py:150` → `@http.route('/api/menu/tree', type='json', auth='user', csrf=False, cors='*', methods=['POST'])`

### Reference Evidence

- `addons/smart_core/docs/Contract-2.0-Spec.md:335` → `- **移除**：`GET /api/v1/contract`（仅 `model_code`）与 `/api/menu/tree`。`
- `addons/smart_construction_core/controllers/frontend_api.py:172` → `"""等价于 /api/menu/tree，保持向后兼容。"""`

## `/api/capabilities/*`

- definition_count: `3`
- reference_count: `0`
- definitions_in_smart_construction_core: `3`
- definitions_in_smart_core: `0`
- definitions_in_smart_construction_scene: `0`

### Definition Evidence

- `addons/smart_construction_core/controllers/capability_catalog_controller.py:14` → `@http.route("/api/capabilities/export", type="http", auth="public", methods=["GET"], csrf=False)`
- `addons/smart_construction_core/controllers/capability_catalog_controller.py:29` → `@http.route("/api/capabilities/search", type="http", auth="public", methods=["GET"], csrf=False)`
- `addons/smart_construction_core/controllers/capability_catalog_controller.py:80` → `@http.route("/api/capabilities/lint", type="http", auth="public", methods=["GET"], csrf=False)`

### Reference Evidence

- none

## `/api/scenes/*`

- definition_count: `3`
- reference_count: `3`
- definitions_in_smart_construction_core: `3`
- definitions_in_smart_core: `0`
- definitions_in_smart_construction_scene: `0`

### Definition Evidence

- `addons/smart_construction_core/controllers/scene_template_controller.py:446` → `@http.route("/api/scenes/export", type="http", auth="public", methods=["GET"], csrf=False)`
- `addons/smart_construction_core/controllers/scene_template_controller.py:607` → `@http.route("/api/scenes/import", type="http", auth="public", methods=["POST"], csrf=False)`
- `addons/smart_construction_core/controllers/scene_controller.py:47` → `@http.route("/api/scenes/my", type="http", auth="public", methods=["GET"], csrf=False)`

### Reference Evidence

- `addons/smart_construction_core/controllers/scene_controller.py:77` → `"[legacy_endpoint] /api/scenes/my called by uid=%s include_tests=%s; successor=%s",`
- `addons/smart_construction_core/static/src/js/sc_sidebar.js:1233` → `const resp = await fetch("/api/scenes/my", { credentials: "include" });`
- `addons/smart_construction_core/static/src/config/role_entry_map.js:3` → `// Role entries are now backend-orchestrated via /api/scenes/my.`

Legacy compliance note: `/api/scenes/my` is deprecated; successor endpoint is `/api/v1/intent` with `intent=app.init`; sunset date `2026-04-30`.

## `/api/ops/*`

- definition_count: `6`
- reference_count: `0`
- definitions_in_smart_construction_core: `6`
- definitions_in_smart_core: `0`
- definitions_in_smart_construction_scene: `0`

### Definition Evidence

- `addons/smart_construction_core/controllers/ops_controller.py:18` → `@http.route("/api/ops/tenants", type="http", auth="public", methods=["GET"], csrf=False)`
- `addons/smart_construction_core/controllers/ops_controller.py:59` → `@http.route("/api/ops/subscription/set", type="http", auth="public", methods=["POST"], csrf=False)`
- `addons/smart_construction_core/controllers/ops_controller.py:95` → `@http.route("/api/ops/packs/batch_upgrade", type="http", auth="public", methods=["POST"], csrf=False)`
- `addons/smart_construction_core/controllers/ops_controller.py:139` → `@http.route("/api/ops/packs/batch_rollback", type="http", auth="public", methods=["POST"], csrf=False)`
- `addons/smart_construction_core/controllers/ops_controller.py:160` → `@http.route("/api/ops/audit/search", type="http", auth="public", methods=["GET"], csrf=False)`
- `addons/smart_construction_core/controllers/ops_controller.py:189` → `@http.route("/api/ops/job/status", type="http", auth="public", methods=["GET"], csrf=False)`

### Reference Evidence

- none

## `/api/packs/*`

- definition_count: `4`
- reference_count: `0`
- definitions_in_smart_construction_core: `4`
- definitions_in_smart_core: `0`
- definitions_in_smart_construction_scene: `0`

### Definition Evidence

- `addons/smart_construction_core/controllers/pack_controller.py:18` → `@http.route("/api/packs/publish", type="http", auth="public", methods=["POST"], csrf=False)`
- `addons/smart_construction_core/controllers/pack_controller.py:81` → `@http.route("/api/packs/catalog", type="http", auth="public", methods=["GET"], csrf=False)`
- `addons/smart_construction_core/controllers/pack_controller.py:201` → `@http.route("/api/packs/install", type="http", auth="public", methods=["POST"], csrf=False)`
- `addons/smart_construction_core/controllers/pack_controller.py:229` → `@http.route("/api/packs/upgrade", type="http", auth="public", methods=["POST"], csrf=False)`

### Reference Evidence

- none

## Scan Notes

- Evidence lines include route definitions and route-string references only.
- Caller-chain and response-contract dependency interpretation is deferred to next stage.

# Frontend Runtime Dependency (Phase F-1 / Scan)

- Stage: `scan` (fact-only; no ownership/priority conclusion)
- Scope: `frontend/apps`, `frontend/packages`, `addons/smart_construction_core/static/src`, `addons/smart_construction_core/controllers`, `addons/smart_core/controllers`
- Exclusion: `dist` outputs excluded from evidence set

## 登录链

- evidence_count: `3`
- frontend_references: `1`
- backend_route_or_service_refs: `2`

### Evidence

- `addons/smart_construction_core/controllers/frontend_api.py:92` → `@http.route('/api/login', type='json', auth='public', csrf=False, cors='*', methods=['POST'])`
- `addons/smart_construction_core/controllers/frontend_api.py:131` → `@http.route('/api/session/get', type='json', auth='public', csrf=False, cors='*', methods=['POST'])`
- `frontend/apps/web/src/api/intents.ts:49` → `hint: 'Allowed before init: login/auth.login/auth.logout/session.bootstrap/system.init/scene.health',`

## system.init 链

- evidence_count: `41`
- frontend_references: `32`
- backend_route_or_service_refs: `9`

### Evidence

- `addons/smart_core/controllers/intent_dispatcher.py:37` → `"app.init": "system.init",`
- `addons/smart_core/controllers/intent_dispatcher.py:38` → `"system.init": "system.init",`
- `addons/smart_core/controllers/intent_dispatcher.py:214` → `@http.route('/api/v1/intent', type='http', auth='public', methods=['POST', 'OPTIONS'], csrf=False)`
- `addons/smart_construction_core/controllers/ui_contract_controller.py:14` → `"legacy /api/ui/contract endpoint is disabled; use /api/v1/intent system.init scene-ready contracts",`
- `addons/smart_core/controllers/enhanced_intent_dispatcher.py:8` → `@http.route('/api/v1/intent_enhanced', type='http', auth='public', methods=['POST'], csrf=False)`
- `addons/smart_core/controllers/enhanced_intent_dispatcher.py:16` → `"message": "intent_enhanced endpoint is decommissioned; use /api/v1/intent",`
- `addons/smart_core/controllers/enhanced_intent_dispatcher.py:24` → `@http.route('/api/v2/intent', type='http', auth='public', methods=['POST'], csrf=False)`
- `addons/smart_core/controllers/enhanced_intent_dispatcher.py:33` → `"message": "enhanced intent router is decommissioned; use /api/v1/intent",`
- `addons/smart_construction_core/controllers/scene_controller.py:21` → `_LEGACY_SCENES_SUCCESSOR = "/api/v1/intent"`
- `frontend/apps/web/src/api/client.ts:96` → `if (!raw.startsWith('/api/v1/intent')) return raw;`
- `frontend/apps/web/src/api/client.ts:121` → `const isIntentEndpoint = String(path || '').trim().startsWith('/api/v1/intent');`
- `frontend/apps/web/src/api/client.ts:141` → `// A2: 网络级别校验 - 针对 system.init 请求`
- `frontend/apps/web/src/api/client.ts:146` → `if (resolvedPath.startsWith('/api/v1/intent') && options.body && typeof options.body === 'string') {`
- `frontend/apps/web/src/api/client.ts:150` → `isAppInitRequest = initIntent === 'system.init' || initIntent === 'app.init';`
- `frontend/apps/web/src/api/client.ts:157` → `console.group('[A2] system.init 网络诊断快照');`
- `frontend/apps/web/src/api/client.ts:191` → `// A2: 响应诊断 - 针对 system.init 请求`
- `frontend/apps/web/src/api/client.ts:196` → `console.group('[A2] system.init 响应诊断快照');`
- `frontend/apps/web/src/api/intents.ts:27` → `'system.init',`
- `frontend/apps/web/src/api/intents.ts:47` → `throw new ApiError('startup chain required: run system.init before other intents', 409, undefined, {`
- `frontend/apps/web/src/api/intents.ts:49` → `hint: 'Allowed before init: login/auth.login/auth.logout/session.bootstrap/system.init/scene.health',`
- `frontend/apps/web/src/api/intents.ts:98` → `const routedEditionKey = intent === 'system.init' ? requestedEditionKey : effectiveEditionKey;`
- `frontend/apps/web/src/api/intents.ts:142` → `if (!['system.init', 'app.init', 'release.operator.surface'].includes(intent)) return false;`
- `frontend/apps/web/src/api/intents.ts:153` → `const response = await apiRequestRaw<IntentEnvelope<T>>('/api/v1/intent', {`
- `frontend/apps/web/src/api/contract.ts:35` → `hint: 'Prefer Scene-ready contract path: system.init -> scene registry -> /s/:sceneKey',`
- `frontend/apps/web/src/stores/session.ts:383` → `bootstrapNextIntent: 'system.init',`
- `frontend/apps/web/src/stores/session.ts:430` → `this.bootstrapNextIntent = String(parsed.bootstrapNextIntent || 'system.init').trim() || 'system.init';`
- `frontend/apps/web/src/stores/session.ts:482` → `this.bootstrapNextIntent = 'system.init';`
- `frontend/apps/web/src/stores/session.ts:582` → `const nextIntent = String(result.bootstrap?.next_intent || 'system.init').trim();`
- `frontend/apps/web/src/stores/session.ts:583` → `const allowedBootstrapIntents = new Set(['system.init', 'session.bootstrap']);`
- `frontend/apps/web/src/stores/session.ts:645` → `const bootstrapIntent = String(this.bootstrapNextIntent || 'system.init').trim();`

## menu/nav 链

- evidence_count: `6`
- frontend_references: `3`
- backend_route_or_service_refs: `3`

### Evidence

- `addons/smart_construction_core/controllers/frontend_api.py:150` → `@http.route('/api/menu/tree', type='json', auth='user', csrf=False, cors='*', methods=['POST'])`
- `addons/smart_construction_core/controllers/frontend_api.py:170` → `@http.route('/api/user_menus', type='json', auth='user', csrf=False, cors='*', methods=['POST'])`
- `addons/smart_construction_core/controllers/frontend_api.py:172` → `"""等价于 /api/menu/tree，保持向后兼容。"""`
- `frontend/apps/web/src/stores/session.ts:998` → `this.initError = 'system.init missing required nav contract';`
- `frontend/apps/web/src/stores/session.ts:1000` → `throw new Error('system.init missing required nav contract');`
- `frontend/apps/web/src/stores/session.ts:1004` → `console.info('[debug] system.init nav length', nav.length);`

## scene open 链

- evidence_count: `4`
- frontend_references: `0`
- backend_route_or_service_refs: `4`

### Evidence

- `addons/smart_construction_core/controllers/scene_controller.py:47` → `@http.route("/api/scenes/my", type="http", auth="public", methods=["GET"], csrf=False)`
- `addons/smart_construction_core/controllers/scene_controller.py:77` → `"[legacy_endpoint] /api/scenes/my called by uid=%s include_tests=%s; successor=%s",`
- `addons/smart_construction_core/static/src/config/role_entry_map.js:3` → `// Role entries are now backend-orchestrated via /api/scenes/my.`
- `addons/smart_construction_core/static/src/js/sc_sidebar.js:1233` → `const resp = await fetch("/api/scenes/my", { credentials: "include" });`

Legacy compliance note: `/api/scenes/my` is deprecated; successor endpoint is `/api/v1/intent` with `intent=app.init`; sunset date `2026-04-30`.

## page/block fetch 链

- evidence_count: `4`
- frontend_references: `1`
- backend_route_or_service_refs: `3`

### Evidence

- `addons/smart_construction_core/controllers/portal_execute_button_controller.py:16` → `"/api/contract/portal_execute_button",`
- `addons/smart_construction_core/controllers/ui_contract_controller.py:10` → `@http.route("/api/ui/contract", type="http", auth="user", methods=["GET", "POST"], csrf=False)`
- `addons/smart_construction_core/controllers/ui_contract_controller.py:14` → `"legacy /api/ui/contract endpoint is disabled; use /api/v1/intent system.init scene-ready contracts",`
- `frontend/apps/web/src/views/ProjectManagementDashboardView.vue:1211` → `if (action.intent.endsWith('.block.fetch')) {`

## execute/action 链

- evidence_count: `14`
- frontend_references: `4`
- backend_route_or_service_refs: `10`

### Evidence

- `addons/smart_construction_core/controllers/__init__.py:15` → `from . import portal_execute_button_controller`
- `addons/smart_construction_core/controllers/portal_execute_button_controller.py:9` → `from odoo.addons.smart_construction_core.services.portal_execute_button_service import (`
- `addons/smart_construction_core/controllers/portal_execute_button_controller.py:16` → `"/api/contract/portal_execute_button",`
- `addons/smart_construction_core/controllers/portal_execute_button_controller.py:22` → `def portal_execute_button_contract(self, **params):`
- `addons/smart_construction_core/controllers/portal_execute_button_controller.py:33` → `"/api/portal/execute_button",`
- `addons/smart_construction_core/controllers/portal_execute_button_controller.py:39` → `def portal_execute_button(self, **params):`
- `addons/smart_construction_core/controllers/portal_execute_button_controller.py:59` → `result = request.env["sc.execute_button.service"].execute(`
- `addons/smart_construction_core/controllers/execute_controller.py:14` → `@http.route("/api/execute_button", type="http", auth="user", methods=["POST"], csrf=False)`
- `addons/smart_construction_core/controllers/execute_controller.py:15` → `def execute_button(self, **params):`
- `addons/smart_construction_core/controllers/execute_controller.py:29` → `result = request.env["sc.execute_button.service"].execute(model, res_id, method, context=context)`
- `frontend/apps/web/src/api/executeButton.ts:6` → `intent: 'execute_button',`
- `frontend/apps/web/src/views/RecordView.vue:800` → `intent: 'execute_button',`
- `frontend/apps/web/src/views/RecordView.vue:836` → `lastIntent.value = 'execute_button';`
- `frontend/apps/web/src/views/RecordView.vue:859` → `setError(err, pageText('error_execute_button', 'failed to execute button'));`

## Scan Notes

- This artifact maps where runtime chain strings are referenced/defined.
- Priority grading (P0/P1/P2/P3) is deferred to the next stage.

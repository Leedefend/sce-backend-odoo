# Duplicate Controller Surface (Phase G-1 / Scan)

- Stage: `scan` (fact-only; duplicate surface evidence)
- Scope: controller route definitions in `smart_construction_core`, `smart_core`, `smart_construction_scene`

## Exact Route Multi-Source Evidence

- no exact same-route multi-module duplicates found in scanned controllers

## Route Family Distribution Evidence

- `/api/login`: routes=`1`, modules=`smart_construction_core`
  - `/api/login` -> `smart_construction_core:addons/smart_construction_core/controllers/frontend_api.py:92`
- `/api/session/get`: routes=`1`, modules=`smart_construction_core`
  - `/api/session/get` -> `smart_construction_core:addons/smart_construction_core/controllers/frontend_api.py:131`
- `/api/menu/tree`: routes=`1`, modules=`smart_construction_core`
  - `/api/menu/tree` -> `smart_construction_core:addons/smart_construction_core/controllers/frontend_api.py:150`
- `/api/scenes/`: routes=`3`, modules=`smart_construction_core`
  - `/api/scenes/my` -> `smart_construction_core:addons/smart_construction_core/controllers/scene_controller.py:47`

Legacy compliance note: `/api/scenes/my` is deprecated; successor endpoint is `/api/v1/intent` with `intent=app.init`; sunset date `2026-04-30`.
  - `/api/scenes/export` -> `smart_construction_core:addons/smart_construction_core/controllers/scene_template_controller.py:446`
  - `/api/scenes/import` -> `smart_construction_core:addons/smart_construction_core/controllers/scene_template_controller.py:607`
- `/api/ops/`: routes=`6`, modules=`smart_construction_core`
  - `/api/ops/tenants` -> `smart_construction_core:addons/smart_construction_core/controllers/ops_controller.py:18`
  - `/api/ops/subscription/set` -> `smart_construction_core:addons/smart_construction_core/controllers/ops_controller.py:59`
  - `/api/ops/packs/batch_upgrade` -> `smart_construction_core:addons/smart_construction_core/controllers/ops_controller.py:95`
  - `/api/ops/packs/batch_rollback` -> `smart_construction_core:addons/smart_construction_core/controllers/ops_controller.py:139`
  - `/api/ops/audit/search` -> `smart_construction_core:addons/smart_construction_core/controllers/ops_controller.py:160`
  - `/api/ops/job/status` -> `smart_construction_core:addons/smart_construction_core/controllers/ops_controller.py:189`
- `/api/packs/`: routes=`4`, modules=`smart_construction_core`
  - `/api/packs/publish` -> `smart_construction_core:addons/smart_construction_core/controllers/pack_controller.py:18`
  - `/api/packs/catalog` -> `smart_construction_core:addons/smart_construction_core/controllers/pack_controller.py:81`
  - `/api/packs/install` -> `smart_construction_core:addons/smart_construction_core/controllers/pack_controller.py:201`
  - `/api/packs/upgrade` -> `smart_construction_core:addons/smart_construction_core/controllers/pack_controller.py:229`
- `/api/capabilities/`: routes=`3`, modules=`smart_construction_core`
  - `/api/capabilities/export` -> `smart_construction_core:addons/smart_construction_core/controllers/capability_catalog_controller.py:14`
  - `/api/capabilities/search` -> `smart_construction_core:addons/smart_construction_core/controllers/capability_catalog_controller.py:29`
  - `/api/capabilities/lint` -> `smart_construction_core:addons/smart_construction_core/controllers/capability_catalog_controller.py:80`
- `/api/v1/intent`: routes=`2`, modules=`smart_core`
  - `/api/v1/intent_enhanced` -> `smart_core:addons/smart_core/controllers/enhanced_intent_dispatcher.py:8`
  - `/api/v1/intent` -> `smart_core:addons/smart_core/controllers/intent_dispatcher.py:214`
- `/api/v2/intent`: routes=`1`, modules=`smart_core`
  - `/api/v2/intent` -> `smart_core:addons/smart_core/controllers/enhanced_intent_dispatcher.py:24`

## Scan Notes

- This artifact reports exact duplicate and family-level co-location evidence only.
- Main-source vs residual-source ownership decision is deferred to later screen stage.

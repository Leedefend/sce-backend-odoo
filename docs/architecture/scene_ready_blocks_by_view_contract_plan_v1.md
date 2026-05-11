# Scene-ready Blocks by View Contract Plan v1

## Goal

Freeze a backend-first scene block contract so frontend renders list/form/kanban directly from `scene_ready_contract_v1.scenes[*].scene_blocks_by_view`.

## Boundary

- Backend owns block orchestration and per-view semantics.
- Frontend owns generic rendering only.
- Frontend must not synthesize missing view blocks from local heuristics.

## Contract Shape

Each scene row should carry:

- `scene_blocks`: default block sequence (generic fallback only)
- `scene_blocks_by_view`:
  - `list: block[]`
  - `form: block[]`
  - `kanban: block[]`

Block shape follows existing `scene_blocks` row model:

- `key`, `kind`, `title`, `order`, `visible`, `semantic_role`
- optional: `layout`, `data_deps`, `actions`, `children`, `payload`

## Required Kind Baseline

The backend must enforce this baseline as a native-view blueprint, not advisory metadata.

### List

Required minimum kinds:

- `page_shell`
- `header_bar`
- `toolbar`
- `list_view`

Optional:

- `pagination`
- `footer`

### Form

Required minimum kinds:

- `page_shell`
- `header_bar`
- `statusbar`
- `body`

Optional:

- `primary_actions`
- `smart_actions`
- `relation_block`
- `chatter`
- `footer`

### Kanban

Required minimum kinds:

- `page_shell`
- `header_bar`
- `toolbar`
- `kanban_board`

Optional:

- `overview_strip`
- `footer`

## Delivery Gates

1. Backend build gate
   - emits `scene_blocks_by_view` for `form/list/kanban`.
2. System init minimal payload gate
   - preserves `scene_blocks_by_view` in compacted startup payload.
3. Frontend consumption gate
   - resolver prefers `scene_blocks_by_view[mode]`.
   - no local `synthesize*SceneBlocks`.

## Current Implementation Mapping

- Backend block producer:
  - `addons/smart_core/core/scene_ready_contract_builder.py`
- Startup compact payload:
  - `addons/smart_core/core/system_init_payload_builder.py`
- Web direct consumer:
  - `frontend/apps/web/src/app/resolvers/sceneReadyResolver.ts`
- Web scene-ready registry passthrough:
  - `frontend/apps/web/src/app/resolvers/sceneRegistry.ts`
- Guard:
  - `scripts/verify/scene_ready_blocks_by_view_guard.py`
  - `make verify.scene.ready.blocks_by_view.guard`

## Non-goals

- No frontend scene-specific hardcode for block generation.
- No fallback to native `ui_base_contract` in page render layer.
- No business-domain branching in frontend render runtime.

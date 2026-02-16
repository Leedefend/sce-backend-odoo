# Scene Orchestration v0.1

## Purpose
Define the user-facing experience layer as a backend-controlled catalog of capabilities and scenes.
Frontend renders tiles and executes intents; backend governs visibility, ordering, and payloads.

## Concepts

### Capability (`sc.capability`)
- **key**: unique capability key (e.g. `project.work`, `contract.work`).
- **intent**: intent name (e.g. `ui.contract`, `api.data`, `execute_button`).
- **default_payload**: JSON payload to execute the intent.
- **required_groups**: Odoo groups required to access the capability.
- **status**: `alpha` / `beta` / `ga`.

### Scene (`sc.scene`)
- **code**: unique scene code.
- **layout**: `grid` / `flow`.
- **target_groups**: groups allowed to see the scene.
- **tiles**: ordered list of `sc.scene.tile`.
- **state**: `draft` / `published` / `archived`.
- **active_version**: published snapshot used by APIs.

### Tile (`sc.scene.tile`)
- **capability**: link to `sc.capability`.
- **payload_override**: JSON payload overrides capability defaults.
- **title/subtitle/icon**: frontend display fields.
- **layout hints**: `visible`, `span`, `min_width`, `badge`.

## Orchestration Flow
1. User logs in and calls `/api/scenes/my`.
2. Backend filters scenes and tiles by group permissions.
3. Frontend renders tiles and executes the provided `intent + payload`.

## API

### `GET /api/scenes/my`

> Deprecated endpoint: runtime clients should migrate to `/api/v1/intent` with `intent=app.init`.
> Sunset date: `2026-04-30`.
> Response includes deprecation signals (`deprecation` payload + `Deprecation`/`Sunset`/`Link`/`X-Legacy-Endpoint` headers).
Returns scenes visible to the current user and their tiles.
Only `published` scenes are returned; if a published version exists, the snapshot is served.

### `GET /api/capabilities/export`
Exports the capability catalog (JSON).

### `GET /api/scenes/export`
Exports scenes (and optionally capabilities) as a template JSON.

### `POST /api/scenes/import`
Imports scene templates. Supports `mode=merge|replace`.

### `POST /api/preferences/get` / `POST /api/preferences/set`
Gets/sets user-level defaults (e.g., default scene, pinned tiles).

## Backend Extension Hooks
If `sc.core.extension_modules` includes `smart_construction_core`, smart_core `system.init`
will include:
- `capabilities`: filtered list of `sc.capability`
- `scenes`: filtered list of `sc.scene`

## Seed Strategy
Default capabilities and scenes are seeded in XML:
- `data/sc_scene_seed.xml`

Seed data **only adds** defaults and should not delete user customization.

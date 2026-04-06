# Platform Scene Access Interface v1

## Purpose

Define a platform-owned scene access surface so `smart_core` talks to
scene/runtime services directly, without industry proxy bridge functions.

## Ownership

- platform owner:
  - scene access contract definition
  - scene runtime orchestration entry selection
  - response normalization and error envelope
- scene module owner:
  - concrete implementation of scene package/governance/registry services
- industry module:
  - optional scene-related contribution data only
  - no proxy owner role for platform scene access

## Platform Access Surface

Required platform-facing capabilities:

1. scene package service class
2. scene governance service class
3. load scene configs
4. detect db scene existence
5. get scene version
6. get schema version

## Interface Contract (Logical)

- `resolve_scene_package_service(env) -> class | None`
- `resolve_scene_governance_service(env) -> class | None`
- `load_scene_configs(env, drift=None) -> dict | list | None`
- `has_db_scenes(env) -> bool`
- `get_scene_version() -> str | None`
- `get_schema_version() -> str | None`

## Migration Rules

- platform reads scene interface directly from scene owner module.
- platform does not call industry `smart_core_scene_*` bridge exports.
- industry module must not become mandatory relay in scene access chain.

## Compatibility Stage

- transition stage may keep fallback path for one iteration cycle.
- fallback is read-only compatibility and must not become new ownership source.

## Guard Target

Future verify guard should fail when:

- industry module exports `smart_core_scene_*` as platform required source.
- platform scene runtime path still depends on industry bridge as first path.


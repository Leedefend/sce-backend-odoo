# Phase 10.5 — Frontend Type Safety Recovery

## Goal
- Recover frontend build baseline (`pnpm build` PASS).
- Enforce strict type discipline for Scene/Governance/Health UI via isolated strict config.
- Prevent new type debt spread while legacy debt remains contained.

## Type Debt Containment
- Main app tsconfig (`frontend/apps/web/tsconfig.json`) is relaxed for legacy areas:
  - `strict=false`
  - `allowJs=true`
  - `checkJs=false`
  - `skipLibCheck=true`
- Strict boundary config added:
  - `frontend/apps/web/tsconfig.strict.json`
  - Includes only:
    - `src/contracts/**/*.ts`
    - `src/api/scene.ts`
    - `src/views/SceneHealthView.vue`

## Contract-First UI
- Added scene contract types:
  - `frontend/apps/web/src/contracts/scene.ts`
- Added typed scene API client:
  - `frontend/apps/web/src/api/scene.ts`
- `SceneHealthView` now uses typed API + contract validation path:
  - `frontend/apps/web/src/views/SceneHealthView.vue`

## Build / Typecheck Scripts
- `frontend/apps/web/package.json`
  - `build`: `vite build`
  - `typecheck:strict`: `vue-tsc --noEmit -p tsconfig.strict.json`
- `frontend/package.json`
  - `typecheck:strict`
  - `gate` updated to use strict typecheck

## Make Targets
- `verify.frontend.build`
- `verify.frontend.typecheck.strict`

## Verify Commands
- `pnpm -C frontend/apps/web build`
- `pnpm -C frontend/apps/web typecheck:strict`
- `make verify.frontend.build`
- `make verify.frontend.typecheck.strict`

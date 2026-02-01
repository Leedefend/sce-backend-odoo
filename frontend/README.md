# Frontend (0 → 1)

This workspace is the independent frontend for the Smart Construction Platform.

## Layout

- `apps/web`: primary web app (Vue 3 + Vite)
- `packages/ui`: shared UI components (future)
- `packages/sdk`: API/intent client (future)
- `packages/schema`: contract types (future)
- `packages/tools`: codegen/validation tools (future)

## Quick Start

```bash
pnpm -C frontend install
pnpm -C frontend dev
```

## Environment

Copy the example env file and adjust as needed:

```bash
cp frontend/.env.example frontend/apps/web/.env
```

Key vars (Vite uses `VITE_*`):

- `VITE_API_BASE_URL`
- `VITE_APP_ENV`
- `VITE_TENANT`
- `VITE_FEATURE_FLAGS`

## Scripts

From repo root:

```bash
pnpm -C frontend dev
pnpm -C frontend build
pnpm -C frontend lint
pnpm -C frontend typecheck
```

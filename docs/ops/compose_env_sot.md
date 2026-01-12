# Compose Env SOT Policy

## Incident Summary
We saw rebuild failures caused by mismatched compose project names and missing
env vars required by the Odoo entrypoint. The root causes were:

- Fixed `container_name` values causing cross-project collisions.
- Missing required env vars (e.g. `ODOO_DBFILTER`) that are only detected at
  container startup.
- Multiple sources of truth for compose project name (`PROJECT` vs
  `COMPOSE_PROJECT_NAME`).

## Policy (Single Source of Truth)
1. `.env` is the only source of truth for compose and runtime env.
2. Required env vars must be present before running any make targets.
3. `container_name` is forbidden in compose files.
4. Compose project name must be pinned and consistent across make, scripts, and
   docker compose labels.

## Required Env Vars
Copy `.env.example` and fill values:

```
cp .env.example .env
```

Required keys:
- `COMPOSE_PROJECT_NAME`
- `DB_USER`
- `DB_PASSWORD`
- `DB_NAME`
- `ADMIN_PASSWD`
- `JWT_SECRET`
- `ODOO_DBFILTER`

## Standard Commands
- Environment gate: `make check-compose-env`
- Project diagnosis: `make diag.project`
- Rebuild: `make dev.rebuild`

## Troubleshooting
- Check compose config: `make gate.compose.config`
- Check labels: `docker ps --format '{{.Names}} {{.Label "com.docker.compose.project"}}'`
- Verify `.env` is loaded: `make diag.project`

# SCEMS v1.0 Deployment Guide

## 1. Scope
- Target version: `SCEMS v1.0`
- Environments: `dev` / `test` / `prod`
- Delivery mode: Docker Compose + Makefile orchestration

## 2. Prerequisites
- Docker and Docker Compose are installed.
- `.env` (or `.env.dev` / `.env.test` / `.env.prod`) is prepared with valid `COMPOSE_PROJECT_NAME`, `DB_NAME`, and `ENV`.
- Run preflight checks:
  - `make check-compose-project`
  - `make check-compose-env`

## 3. Standard Deployment Flow

### 3.1 Start services
- `make up`
- `make ps`

### 3.2 Initialize DB and demo baseline (dev/test)
- Reset DB: `make db.reset DB_NAME=<db>`
- Seed demo baseline: `make demo.reset DB=<db>`

### 3.3 Install/upgrade modules
- Install: `make mod.install MODULE=smart_construction_core DB_NAME=<db>`
- Upgrade: `make mod.upgrade MODULE=smart_construction_core DB_NAME=<db>`

### 3.4 Critical verification
- `make verify.phase_next.evidence.bundle`
- `make verify.scene.catalog.governance.guard`
- `make verify.project.form.contract.surface.guard`

## 4. Upgrade and Rollback

### 4.1 Upgrade
- Run upgrade: `make mod.upgrade MODULE=<module_list> DB_NAME=<db>`
- Run regression checks:
  - `make verify.phase_next.evidence.bundle`
  - `make verify.runtime.surface.dashboard.strict.guard`

### 4.2 Rollback (branch/code)
- Use Codex rollback orchestration: `make codex.rollback`

### 4.3 Scene-level rollback (scene channel)
- `make scene.rollback.stable`
- Verify: `make verify.portal.scene_rollback_smoke.container`

## 5. Environment Parameter Suggestions

### 5.1 dev
- `ENV=dev`
- `DB_NAME=sc_demo`

### 5.2 test
- `ENV=test`
- Use dedicated `DB_NAME` and fixed verification credentials

### 5.3 prod
- `ENV=prod`
- Do not run reset operations directly; require change review and rollback rehearsal first

## 6. Deployment Completion Criteria
- Services are healthy (`make ps`).
- Phase 5 verification command chain passes.
- Evidence artifacts are archived under `artifacts/`.


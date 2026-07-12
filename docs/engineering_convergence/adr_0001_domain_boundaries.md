# ADR-0001 Domain Boundaries for v1.1 Convergence

Status: Accepted for v1.1 convergence
Date: 2026-07-12

## Context

The system has accumulated platform, low-code, construction business, migration, acceptance, and operations concerns in the same repository. Recent productization work repeatedly exposed boundary drift: frontend fallback logic, menu/config mismatch, legacy carrier exposure, and unclear ownership of validation scripts.

v1.1 convergence needs stable boundaries before larger refactoring starts.

## Decision

The repository is governed by these domain boundaries.

## Platform Core

Primary module: `addons/smart_core`

Responsibilities:

- Contract assembly and structure-driven API semantics.
- Intent routing and permission-aware backend orchestration.
- Low-code configuration engine boundaries.
- Product menu/config policy primitives.
- Platform access, subscription, and shared technical services.

Rules:

- Must not depend on construction business modules.
- Must not encode construction-specific workflow decisions.
- Must provide backend-owned contracts so the frontend can render without inventing business logic.
- Must treat frontend-only fallback behavior as a boundary violation unless explicitly approved for degraded display.

## Construction Business Core

Primary module: `addons/smart_construction_core`

Responsibilities:

- Project, BOQ, WBS, contract, budget, material, payment, settlement, finance, and business workflow models.
- Business menus, views, approvals, record rules, and operational data.
- Business-facing configuration seeds that belong to construction usage.

Rules:

- May depend on `smart_core`.
- Must not push construction semantics back into `smart_core`.
- Cross-domain money, approval, and status transitions must be exposed through service-style functions or explicit model methods, not scattered controller logic.

## Product Configuration and Low-Code

Primary locations:

- `addons/smart_core/app_config_engine`
- frontend configuration workbench surfaces
- menu/config policy data in construction modules

Responsibilities:

- Backend-owned menu/config visibility decisions.
- Backend-owned form/list/search/action contracts.
- User-facing configuration workbench behavior.

Rules:

- The backend is the source of truth for effective visibility, grouping, ordering, and action binding.
- The frontend must not synthesize product menu structure that changes business meaning.
- Configuration UI must display the same effective semantics as the main navigation.
- Group/menu carriers are allowed only when the backend exposes their effective configurable state.

## Scene and Extension Modules

Primary modules:

- `addons/smart_scene`
- `addons/smart_construction_scene`
- extension and capability assets under construction modules

Responsibilities:

- Scene metadata, capability grouping, and optional extension surfaces.

Rules:

- Scene modules may depend inward on platform/business cores.
- Core modules must not depend outward on scene modules.
- Scene activation must not bypass core permission or project isolation rules.

## Seed, Demo, Bundle, and Portal Edge Modules

Primary modules:

- `smart_construction_seed`
- `smart_construction_demo`
- `smart_construction_bundle`
- `smart_construction_portal`
- owner/license bundle modules

Responsibilities:

- Install composition, bootstrap data, demos, portal exposure, and distribution packaging.

Rules:

- These modules sit at the outer edge of the graph.
- Demo data must not be required for production behavior.
- Bundle modules must not become hidden owners of core business behavior.

## Migration and Legacy Compatibility

Primary locations:

- `scripts/migration`
- legacy carrier models and compatibility views inside construction modules

Responsibilities:

- Data migration, replay evidence, legacy asset verification, and compatibility disposition.

Rules:

- Every legacy object must be classified as keep, migrate, hide, or remove.
- A legacy carrier may support product behavior only when the product-facing action/menu is formalized and documented.
- Legacy exposure in navigation or configuration must be treated as a productization defect unless explicitly allowed by the release baseline.

## Analytics and Projection

Primary locations:

- projection views/models inside construction modules
- dashboard and operating metric assets

Responsibilities:

- Read-optimized aggregation and traceable management views.

Rules:

- Analytics must be traceable back to source business documents.
- Projection code must not own source-of-truth business transitions.
- Dashboard performance baselines are required before pilot.

## Operations and Release

Primary locations:

- `scripts/ops`
- `scripts/prod`
- `deploy`
- `.github`
- root `Makefile`

Responsibilities:

- Environment validation, release, rollback, backup/restore, and CI governance.

Rules:

- Production mutation requires an explicit runbook and evidence.
- PR gates and release gates must use documented Make targets.
- Local, daily development, and production server paths must be named explicitly in runbooks to avoid environment drift.

## Consequences

- New cross-boundary dependencies require an ADR.
- The module dependency map is a required freshness gate.
- Low-code and product navigation defects must be diagnosed from backend source-of-truth first.
- Future Makefile/module splitting should preserve these boundaries instead of only moving files.

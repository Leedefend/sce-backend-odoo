# /api/meta/project_capabilities Ownership Screen (ITER-2026-04-05-1050)

## Object Facts

- endpoint: `/api/meta/project_capabilities`
- file: `addons/smart_construction_core/controllers/meta_controller.py`
- handler: `MetaController.describe_project_capabilities`
- auth/type: `auth=user`, `type=http`

## Responsibility Analysis

The endpoint currently:

1. resolves a concrete `project.project` record and enforces access rights/rules;
2. calls `LifecycleCapabilityService` from `smart_construction_core.services`;
3. returns project-specific lifecycle capability facts with `schema_version=lifecycle-capability-v1`.

This is scenario business-fact semantics, not generic platform runtime envelope.

## Boundary Classification

- current owner fit: **acceptable** in scenario module.
- migration pressure: low under current policy.
- risk level: `P2` (stable, bounded, not platform mainline runtime entry shell).

## Permanence Decision

- keep scenario ownership for now.
- do not open immediate migration to smart_core.

## Guardrails

1. keep contract narrow to project lifecycle capability facts.
2. avoid expanding this endpoint with generic app/menu/session/platform semantics.
3. if future requirement needs cross-domain generic capability catalog semantics, open a new platform provider line instead of overloading this route.

## Next Backlog Suggestion

- shift focus to dormant controller cleanup residuals and non-auth dormant surfaces with low-risk hygiene batches.

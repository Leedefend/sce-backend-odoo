# Verification Entry Points

## Core Gates
- `make gate.full`
  - Default strict mode includes Phase 9.8 guards.
  - Use `SC_GATE_STRICT=0` to skip Phase 9.8 enforcement.
  - Use `SC_SCENE_OBS_STRICT=1` to additionally enforce strict scene observability evidence during gate runs.
  - Default gate path includes `verify.portal.scene_observability_gate_smoke.container` (structure + preflight smoke + smoke chain).
  - Contract preflight now runs baseline freeze guard by default (`BASELINE_FREEZE_ENFORCE=1`).
  - Contract preflight includes scene runtime boundary gate:
    - `make verify.scene.runtime_boundary.gate`
  - Contract preflight includes legacy contract bundle checks:
    - `make verify.scene.legacy.bundle`
  - Contract preflight can be run as a single scene contract path gate:
    - `make verify.scene.contract_path.gate`
  - Full legacy endpoint aggregate (includes endpoint usage guard):
    - `make verify.scene.legacy.all`
    - legacy endpoint `/api/scenes/my` is deprecated; successor is `/api/v1/intent` with `intent=app.init`; sunset date `2026-04-30`.
  - Any docs mentioning `/api/scenes/my` must include deprecated + successor migration semantics; enforced by:
    - `make verify.scene.legacy_docs.guard`

## Architecture Guard Aliases
- `make verify.boundary.guard`
  - Aggregates scene runtime boundary + legacy contract path checks.
- `make verify.contract.snapshot`
  - Snapshot-structure baseline gate for scene contract shape + ordering determinism smoke.
- `make verify.mode.filter`
  - Verifies user/hud mode isolation (`contract_mode` behavior).
- `make verify.capability.schema`
  - Verifies capability payload schema and scene/capability contract cohesion.
- `make verify.scene.schema`
  - Verifies scene definition semantics + scene contract schema shape.
- `make verify.seed.demo.isolation`
  - Verifies provider layer does not depend on demo/seed modules and user-mode contract output does not leak demo/showcase semantics.
- `make verify.contract.ordering.smoke`
  - Verifies scene/capability sequence determinism across repeated `system.init` calls.
- `make verify.contract.catalog.determinism`
  - Verifies contract catalog exports are deterministic across repeated generations.
- `make verify.contract.envelope`
  - Aggregates envelope consistency checks (`ok/data/meta`) across intent and contract API paths.
- `make verify.backend.architecture.full`
  - One-command backend governance gate (boundary + envelope + mode + scene/capability schema + seed/demo isolation + snapshot determinism).
- Guard coverage matrix:
  - `docs/ops/verify/backend_architecture_guard_matrix.md`

## Phase 9.8 Menu/Scene Coverage
- `make verify.menu.scene_resolve.container`
- `make verify.menu.scene_resolve.summary`
- `make verify.portal.scene_warnings_guard.container`
- `make verify.portal.scene_warnings_limit.container`
- `make verify.portal.act_url_missing_scene_report.container`
- `make verify.phase_9_8.gate_summary`

## Phase D/E Cross-Stack Envelope Coverage
- `make verify.portal.envelope_smoke.container`
  - Aggregates:
    - `make verify.portal.scene_contract_smoke.container`
    - `make verify.portal.my_work_smoke.container`
    - `make verify.portal.execute_button_smoke.container`
    - `make verify.portal.cross_stack_contract_smoke.container`
  - Enforces intent envelope checks (`ok=true`) and `meta.trace_id` presence.

## Scene Observability Strict Mode
- Default smoke targets remain compatibility-friendly and may skip when governance/audit models are unavailable:
  - `make verify.portal.scene_observability_preflight.refresh.container DB_NAME=<name>`
  - `make verify.portal.scene_observability_preflight_smoke.container`
  - `make verify.portal.scene_observability_preflight.latest`
  - `make verify.portal.scene_governance_action_smoke.container`
  - `make verify.portal.scene_auto_degrade_smoke.container`
  - `make verify.portal.scene_auto_degrade_notify_smoke.container`
  - `make verify.portal.scene_package_import_smoke.container`
  - Aggregate:
    - `make verify.portal.scene_observability_smoke.container`
- Strict variants enforce governance/audit artifacts and fail fast when evidence is missing:
  - `make verify.portal.scene_observability.structure_guard`
  - Baseline update:
    - `make verify.portal.scene_observability.structure_guard.update`
  - `make verify.portal.scene_observability_preflight.container` (`SCENE_OBSERVABILITY_PREFLIGHT_STRICT=1`)
  - `make verify.portal.scene_observability_preflight.report.strict`
  - `make verify.portal.scene_governance_action_strict.container`
  - `make verify.portal.scene_auto_degrade_strict.container`
  - `make verify.portal.scene_auto_degrade_notify_strict.container`
  - `make verify.portal.scene_package_import_strict.container`
- One-command strict aggregate:
  - `make verify.portal.scene_observability_strict.container`
- Gate-friendly smoke aggregate (structure guard + preflight smoke + smoke chain):
  - `make verify.portal.scene_observability_gate_smoke.container`
- UI semantic suite strict variant:
  - `make verify.portal.ui.v0_8.semantic.strict.container`

## Demo Baseline
- `make verify.demo`

## Stage 3 Approval MVP
- Cross-stack payment request approval smoke:
  - `make verify.portal.payment_request_approval_smoke.container`
  - Shared prepare step can be skipped when already prepared:
    - `PAYMENT_APPROVAL_SKIP_PREPARE=1 make verify.portal.payment_request_approval_smoke.container`
  - Covers login -> `api.data` payment request discovery -> `payment.request.submit` -> `payment.request.approve`.
  - Live path selection is action-surface aware:
    - probes `payment.request.available_actions` and prefers records with executable actions
    - reports `primary_action_key`, `allowed_actions`, and `blocked_reason_summary`
  - Default credential source for this smoke is finance-role-first:
    - `ROLE_FINANCE_LOGIN` / `ROLE_FINANCE_PASSWORD` (defaults: `demo_role_finance` / `demo`)
    - falls back to `E2E_LOGIN` / `E2E_PASSWORD` only when role vars are unset.
  - Optional env knobs:
    - `PAYMENT_REQUEST_SMOKE_AUTO_CREATE=1` (default): auto-create minimal payment request + attachment when no live record is available.
    - `PAYMENT_REQUEST_SMOKE_REQUIRE_LIVE=1`: fail if smoke cannot enter live-record path.
- Cross-role handoff smoke (finance -> executive -> finance):
  - `make verify.portal.payment_request_approval_handoff_smoke.container`
  - Shared prepare step can be skipped when already prepared:
    - `PAYMENT_APPROVAL_SKIP_PREPARE=1 make verify.portal.payment_request_approval_handoff_smoke.container`
  - Verifies a delivery-grade handoff path:
    - finance executes `payment.request.execute` with `submit`
    - executive executes one allowed follow-up action (`approve` preferred, fallback `reject`)
    - finance re-probes available actions and executes `done` when allowed
  - Optional env knob:
    - `PAYMENT_REQUEST_HANDOFF_EXEC_ACTION_ORDER=approve,reject` (default)
- One-command sequential aggregate (single upgrade/restart + both smokes):
  - `make verify.portal.payment_request_approval_all_smoke.container`
  - Use this target in CI/local when running both approval smokes to avoid concurrent `mod.upgrade` conflicts on the same DB.
- Payment form delivery UX notes (frontend):
  - Blocked actions can run `suggested_action` directly from form hint area.
  - Action feedback shows trace/request evidence and supports one-click copy.
  - Shortcuts:
    - `Ctrl+Enter`: run primary allowed semantic action
    - `Alt+R`: retry last semantic action
  - Action-surface freshness is visible and can be manually refreshed in form.
  - Action history supports reason-code filtering and per-entry evidence copy.
  - Optional action-surface auto-refresh is available in form UX.
  - Action feedback can be explicitly dismissed by user.

## Baseline Semantics
- Platform baseline (environment/bootstrap consistency)
  - `make verify.platform_baseline`
  - `make gate.platform_baseline`
  - Legacy compatibility:
    - `make verify.baseline` (same as platform baseline)
    - `make gate.baseline` (same as platform baseline gate)
- Business baseline (core+seed install + business usable checks)
  - `make verify.business_baseline`
  - `make gate.business_baseline`
  - Legacy compatibility:
    - `make verify.p0.flow` (same as business baseline verification)
- One-command aggregate
  - `make verify.baseline.all` (platform + business)
  - `make gate.baseline.all` (platform gate + business gate)

## Business Increment Preflight
- Readiness report (non-blocking):
  - `make verify.business.increment.readiness`
  - optional profile: `BUSINESS_INCREMENT_PROFILE=base|strict`
- Readiness brief (non-blocking):
  - `make verify.business.increment.readiness.brief`
- Readiness report (blocking):
  - `make verify.business.increment.readiness.strict`
- Readiness brief (blocking):
  - `make verify.business.increment.readiness.brief.strict`
- One-command preflight (refresh catalogs + scene shape + intent surface + readiness):
  - `make verify.business.increment.preflight`
- Strict preflight:
  - `make verify.business.increment.preflight.strict`
  - strict profile enforces `renderability_fully_renderable=true`, required core `intents` / `scene_keys`, required `test_refs` coverage, behavioral coverage completeness (`examples + request/response hints`), and reason-code coverage for selected side-effect intents.
- Policy source:
  - `scripts/verify/baselines/business_increment_readiness_policy.json`
  - strict profile also emits warning when untested intents exceed `warning_untested_limit`.

## Notes
- Typical env: `DB_NAME=sc_demo E2E_LOGIN=svc_e2e_smoke E2E_PASSWORD=demo`.
- Phase 9.8 warnings baseline can be adjusted via `SC_WARN_ACT_URL_LEGACY_MAX`.
- Menu exemptions file: `docs/ops/verify/menu_scene_exemptions.yml`.
- Menu scene resolve enforcement scope (default business namespace only):
  - `MENU_SCENE_ENFORCE_PREFIXES=smart_construction_core.,smart_construction_demo.,smart_construction_portal.`
  - Set `MENU_SCENE_ENFORCE_PREFIXES=` (empty) to enforce all namespaces (including Odoo technical menus).
- Strict failure guide: `docs/ops/verify/scene_observability_troubleshooting.md`.
- Baseline freeze guard:
  - `make verify.baseline.freeze_guard`
  - Temporary bypass in approved exception PR only:
    - `BASELINE_FREEZE_ALLOW=1 make verify.baseline.freeze_guard`

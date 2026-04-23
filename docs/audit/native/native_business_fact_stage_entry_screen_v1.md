# Native Business-Fact Stage Entry Screen v1

## Objective

Determine whether the execution lane can move from runtime-recovery governance into native business-fact usability work under low-risk constraints.

## Screen Inputs

- Runtime live classification (`ITER-2026-04-07-1229`):
  - `POST /api/v1/intent` -> `401 AUTH_REQUIRED`
  - `GET /api/scenes/my` -> `401 AUTH_REQUIRED` + deprecation headers
- Current repository guardrails:
  - `security/**`, `record_rules/**`, `ir.model.access.csv`, `__manifest__.py` remain stop-gated by default.
- Current batch verification signals:
  - `scene_legacy_auth_smoke_semantic_verify` PASS
  - `scene_legacy_auth_runtime_probe` PASS (sandbox still shows reachability restrictions)

## Screen Decision

- Runtime blocker for endpoint URL correctness is **cleared**.
- Native and legacy auth entry both show expected unauthenticated gate semantics in host-approved probe.
- Next eligible work should stay in low-risk business-fact lane and avoid ACL/rule/manifest changes.

## Next Executable Low-Risk Lane

1. Build a factual usability checklist focused on non-ACL blockers:
   - required business dictionaries presence evidence
   - native action/menu runtime open-path evidence
   - non-empty mandatory business facts on core records
2. Keep changes to:
   - `scripts/verify/**` (read-only checks or helper asserts)
   - `docs/audit/native/**`
   - `agent_ops/**`
3. If any gap requires ACL or record-rule edits, open a dedicated high-risk gated task instead of direct implementation.

## Risk Classification

- This screen batch: **low risk / PASS**.
- Next batch: **low risk** if constrained to evidence + verify helpers; otherwise must branch into high-risk gate flow.

## Legacy Endpoint Deprecation Note
- `/api/scenes/my` is deprecated.
- Successor endpoint: `/api/v1/intent` with `intent=app.init`.
- Sunset date: `2026-04-30`.
- Deprecation header contract reference: `Deprecation`, `Sunset`, `Link`, `X-Legacy-Endpoint`.

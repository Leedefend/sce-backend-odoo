# ITER-2026-04-02-801

- status: PASS
- mode: implement
- layer_target: Backend Usability
- module: cross stack suggested action recovery
- priority_lane: usability_verification_mainline
- risk: low

## Implementation Result

- backend:
  - `addons/smart_core/handlers/system_init.py`
  - add `_normalize_access_suggested_action(data)` to recover `access.suggested_action`
  - fallback semantics now reuse `failure_meta_for_reason(reason_code)` when missing
- frontend:
  - `frontend/apps/web/src/views/ActionView.vue`
  - restore explicit generic calls `resolveSuggestedAction(...)` and `runSuggestedAction(...)` via local wrappers
  - wire wrappers into existing batch runtimes without adding model-specific判断

## Decision

- PASS
- implementation batch completed; move to verify-only batch

## Next Iteration Suggestion

- run semantic aggregate gate to confirm recovery:
  - `make verify.portal.ui.v0_8.semantic.container`

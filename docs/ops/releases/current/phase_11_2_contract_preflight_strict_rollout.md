# Phase 11.2 Contract Preflight Strict Rollout

Date: 2026-03-04  
Branch: `feat/interaction-core-p0-v0_1`

## Scope

- Promote advanced-view semantic strict checks from optional to default in contract preflight.
- Clear preflight blockers discovered during rollout (reason-code drift, legacy token path).
- Keep an explicit temporary rollback switch for emergency iteration.

## Delivered Changes

1. Preflight strict-by-default
- `CONTRACT_PREFLIGHT_STRICT_VIEW_TYPES ?= 1` in `Makefile`.
- `verify.contract.preflight` now executes:
  - `verify.contract.view_type_semantic.smoke` (`min_models=1`)
  - `verify.contract.view_type_semantic.strict.smoke` (`min_models=2`)

2. Contract drift unblock
- Removed hard-coded `reason_code` values in `my_work_summary` and switched to shared constants in `smart_core.utils.reason_codes`.

3. Legacy scenes endpoint stability
- Fixed token-auth user binding in `smart_core/security/auth.py` for `/api/scenes/my` legacy path under smoke/preflight checks.

4. Capability baseline alignment
- Updated `scripts/verify/baselines/scene_capability_contract_guard.json` role logins to fixture-standard `sc_fx_*` accounts.

## Verification

- `make verify.contract.preflight` (default strict enabled): PASS
- `make verify.contract.preflight CONTRACT_PREFLIGHT_STRICT_VIEW_TYPES=1`: PASS
- `make verify.contract.view_type_semantic.strict.smoke`: PASS
- `make verify.scene.legacy_deprecation.smoke`: PASS

## Temporary Rollback

For unstable feature branches only:

```bash
make verify.contract.preflight CONTRACT_PREFLIGHT_STRICT_VIEW_TYPES=0
```

This disables only strict advanced-view semantic smoke while keeping the rest of preflight checks unchanged.

## Merge-ready Changelog Snippet

```md
### Changed
- Contract preflight now enables strict advanced-view semantic checks by default.
- `verify.contract.preflight` includes both baseline and strict advanced-view smoke:
  - `verify.contract.view_type_semantic.smoke` (`min_models=1`)
  - `verify.contract.view_type_semantic.strict.smoke` (`min_models=2`)

### Fixed
- Removed hard-coded `reason_code` literals in my-work summary flow by switching to shared constants.
- Fixed legacy token-auth user binding for `/api/scenes/my` to avoid request-cursor mismatch failures.
- Aligned scene-capability guard baseline role logins with fixture-standard `sc_fx_*` accounts.

### Docs
- Added rollout + rollback runbook for strict preflight toggle.
- Linked Phase 11 closure doc to Phase 11.2 strict rollout note.

### Verification
- `make verify.contract.preflight` PASS (strict on by default)
- `make verify.contract.view_type_semantic.strict.smoke` PASS
- `make verify.scene.legacy_deprecation.smoke` PASS
```

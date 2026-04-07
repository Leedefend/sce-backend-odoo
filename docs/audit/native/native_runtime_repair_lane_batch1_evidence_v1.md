# Native Runtime Repair Lane Batch1 Evidence v1

## Scope

- Task: `ITER-2026-04-07-1211`
- Objective: harden unreachable error classification in legacy auth smoke

## Changes

- `scripts/verify/scene_legacy_auth_smoke.py`
  - `_is_runtime_unreachable` now explicitly recognizes:
    - `Remote end closed connection without response`
    - `RemoteDisconnected`

- `scripts/verify/scene_legacy_auth_smoke_semantic_verify.py`
  - added semantic case for `RemoteDisconnected`:
    - strict mode must FAIL
    - explicit fallback mode must PASS

## Verification

- `make verify.scene.legacy_contract.guard`: PASS
- `make verify.test_seed_dependency.guard`: PASS
- `make verify.scene.legacy_auth.smoke.semantic`: PASS

## Risk Summary

- Low risk; verify-helper scope only.
- No business facts, ACL/rules, or financial semantics changed.

## Conclusion

- Runtime unreachable classification is more robust while preserving strict default + explicit fallback semantics.

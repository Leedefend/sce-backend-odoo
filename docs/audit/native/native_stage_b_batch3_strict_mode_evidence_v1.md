# Native Stage-B Batch3 Strict-Mode Evidence v1

## Scope

- Task: `ITER-2026-04-07-1204`
- Focus: legacy auth smoke strict-mode fallback policy evidence
- Boundary: evidence-only, no source mutation in this batch

## Policy Evidence

- `scripts/verify/scene_legacy_auth_smoke.py` default fallback env decode:
  - `SCENE_LEGACY_AUTH_SMOKE_ALLOW_UNREACHABLE_FALLBACK` default = `False`
- Unreachable strict-mode behavior:
  - raises `RuntimeError` containing `base_url`, `endpoint`, and original error text
- Explicit fallback behavior:
  - fallback is activated only when `fallback_on_unreachable=True`

## Verification Matrix

- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-07-1204.yaml`: PASS
- `make verify.scene.legacy_contract.guard`: PASS
- `make verify.test_seed_dependency.guard`: PASS
- `make verify.scene.legacy_auth.smoke.semantic`: PASS

## Risk Notes

- Low risk verify batch with governance/doc-only outputs.
- Runtime warning line still appears in semantic harness output, but semantic assertions for strict/fallback paths pass.

## Conclusion

- Stage-B Batch3 strict-mode policy evidence is complete and auditable.

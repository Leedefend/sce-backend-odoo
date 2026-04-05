# ITER-2026-04-03-938

- status: FAIL
- mode: verify
- layer_target: Product Release Usability Proof
- module: delivery policy guard drift verify
- risk: medium
- publishability: blocked

## Verification Result

- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-03-938.yaml`: PASS
- `... make verify.product.delivery_policy_guard DB_NAME=sc_demo`: FAIL
- artifact:
  - `artifacts/backend/product_delivery_policy_guard.json`
- failure:
  - reproducible `menu policy drift` (policy core keys vs nav core+native_preview keys).

## Decision

- FAIL
- stop condition: `acceptance_failed`

## Next Iteration Suggestion

- open dedicated implement batch to align `scripts/verify/product_delivery_policy_guard.py` with release-core policy semantics and extension allowance.

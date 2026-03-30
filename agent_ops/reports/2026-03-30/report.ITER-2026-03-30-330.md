# ITER-2026-03-30-330

## Summary

Defined the smallest optimization composition contract that should be added on
top of completed backend native truths. This batch keeps native truths and
optimization responsibilities explicitly separated.

The contract scope is intentionally limited to:

- `toolbar_sections`
- `active_conditions`
- `high_frequency_filters`
- `advanced_filters`
- `batch_actions`
- `guidance`

## Changed Files

- `docs/tmp/minimal_optimization_composition_contract_v1_2026-03-30.md`
- `agent_ops/tasks/ITER-2026-03-30-330.yaml`

## Verification

- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-03-30-330.yaml` PASS

## Key Findings

- Backend native truths are now sufficient as the factual layer.
- Optimization composition should not repeat capability facts.
- The first implementation batch should only cover:
  - `toolbar_sections`
  - `active_conditions`
  - `high_frequency_filters`
  - `advanced_filters`
- `batch_actions` and `guidance` should come later, after toolbar hierarchy is stable.

## Risk Summary

- Documentation-only batch
- No backend code changed
- No frontend code changed
- No contract implementation yet

## Rollback

```bash
git restore agent_ops/tasks/ITER-2026-03-30-330.yaml
git restore docs/tmp/minimal_optimization_composition_contract_v1_2026-03-30.md
git restore agent_ops/reports/2026-03-30/report.ITER-2026-03-30-330.md
git restore agent_ops/state/task_results/ITER-2026-03-30-330.json
```

## Next Suggestion

Start backend implementation batch 1 for minimal optimization composition:

- `toolbar_sections`
- `active_conditions`
- `high_frequency_filters`
- `advanced_filters`

Do not implement `batch_actions` or `guidance` in the same batch.

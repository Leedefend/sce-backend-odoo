# BE Finance Center Action Align Implement FH

## Goal

Realign `finance.center` and `finance.workspace` scene target action identity to
the actual finance center root menu action `action_sc_finance_dashboard`.

## Verification

1. `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-21-BE-FINANCE-CENTER-ACTION-ALIGN-IMPLEMENT-FH.yaml`
2. `python3 addons/smart_construction_scene/tests/test_action_only_scene_semantic_supply.py`
3. `git diff --check -- agent_ops/tasks/ITER-2026-04-21-BE-FINANCE-CENTER-ACTION-ALIGN-IMPLEMENT-FH.yaml addons/smart_construction_scene/profiles/scene_registry_content.py addons/smart_construction_scene/tests/test_action_only_scene_semantic_supply.py docs/verify/be_finance_center_action_align_implement_fh_v1.md docs/ops/iterations/delivery_context_switch_log_v1.md`

## Result

```json
{
  "result": "PASS",
  "closed_slice": "finance center root action alignment",
  "effect": [
    "finance.center and finance.workspace now publish the actual finance center root action xmlid",
    "nav scene-map derivation for finance center no longer depends on a finance sub-action target",
    "the batch stayed inside scene-orchestration alignment and avoided payment/settlement model changes"
  ],
  "residual_risk": "Other finance residual actions still require separate scene-supply screening."
}
```

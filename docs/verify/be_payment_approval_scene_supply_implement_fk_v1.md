# BE Payment Approval Scene Supply Implement FK

## Goal

Add the missing approval action target identity to `payments.approval` without
touching payment business files.

## Verification

1. `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-21-BE-PAYMENT-APPROVAL-SCENE-SUPPLY-IMPLEMENT-FK.yaml`
2. `python3 addons/smart_construction_scene/tests/test_action_only_scene_semantic_supply.py`
3. `git diff --check -- agent_ops/tasks/ITER-2026-04-21-BE-PAYMENT-APPROVAL-SCENE-SUPPLY-IMPLEMENT-FK.yaml addons/smart_construction_scene/profiles/scene_registry_content.py addons/smart_construction_scene/tests/test_action_only_scene_semantic_supply.py docs/verify/be_payment_approval_scene_supply_implement_fk_v1.md docs/ops/iterations/delivery_context_switch_log_v1.md`

## Result

```json
{
  "result": "PASS",
  "closed_slice": "payments.approval action target identity supply",
  "effect": [
    "payments.approval now publishes a formal approval action xmlid",
    "scene-known resolution can bind the approval center to its stable tier-review action",
    "the batch avoided payment_request business file changes"
  ],
  "residual_risk": "Other payment/settlement residual families still require new screened work."
}
```

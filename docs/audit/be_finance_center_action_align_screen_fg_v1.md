# BE Finance Center Action Align Screen FG

```json
{
  "candidate_family": "finance.center root action alignment",
  "decision": "eligible_for_bounded_scene_orchestration_fix",
  "evidence": [
    "smart_construction_core.views.menu_finance_center.xml binds menu_sc_finance_center to smart_construction_core.action_sc_finance_dashboard",
    "scene_registry_content currently binds finance.center and finance.workspace to smart_construction_core.action_sc_tier_review_my_payment_request",
    "the candidate fix only realigns scene target identity and does not touch payment/settlement business models or approval rules"
  ],
  "next_step": "update finance.center and finance.workspace scene registry action_xmlid to action_sc_finance_dashboard and add regression coverage"
}
```

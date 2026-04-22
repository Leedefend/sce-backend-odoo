# BE Finance Payment Requests Semantic Screen FM

```json
{
  "decision": "canonical_scene_entry_is_action_payment_request_my",
  "evidence": [
    "sc_scene_list_profile finance.payment_requests target already uses smart_construction_core.action_payment_request_my",
    "capability finance.payment_request.list default_payload uses action_payment_request_my",
    "scene tiles and portal dashboard finance entry both use action_payment_request_my",
    "core_extension already maps both action_payment_request and action_payment_request_my to finance.payment_requests, so choosing the personal action as canonical scene entry does not remove menu-based scene resolution"
  ],
  "reason": "Within the scene-orchestration layer, finance.payment_requests is repeatedly consumed as a user-facing work entry rather than the raw generic finance menu default. Therefore action_payment_request_my is the stronger canonical scene entry, while action_payment_request can remain a compatibility/native menu binding."
}
```

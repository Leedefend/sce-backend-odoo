# Finance Payment Requests Action Closure Sample v1

## 场景

- `scene_key`: `finance.payment_requests`

## Scene-ready 动作样例

```json
[
  {
    "key": "approve_payment_request",
    "label": "批准",
    "intent": "record.update",
    "target": {
      "mutation": {
        "type": "transition",
        "model": "finance.payment.request",
        "operation": "approve",
        "payload_schema": {"required": ["record_id"]}
      },
      "refresh_policy": {
        "on_success": ["scene_projection", "workbench_projection"],
        "scope": "local"
      }
    }
  },
  {
    "key": "reject_payment_request",
    "label": "驳回",
    "intent": "record.update",
    "target": {
      "mutation": {
        "type": "transition",
        "model": "finance.payment.request",
        "operation": "reject",
        "payload_schema": {"required": ["record_id", "reason"]}
      },
      "refresh_policy": {
        "on_success": ["scene_projection", "workbench_projection"],
        "scope": "local"
      }
    }
  },
  {
    "key": "assign_payment_request",
    "label": "指派",
    "intent": "record.update",
    "target": {
      "mutation": {
        "type": "assign",
        "model": "finance.payment.request",
        "operation": "assign",
        "payload_schema": {"required": ["record_id", "assignee_id"]}
      },
      "refresh_policy": {
        "on_success": ["scene_projection", "workbench_projection"],
        "scope": "local"
      }
    }
  }
]
```


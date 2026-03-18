# Scene Action Runtime Protocol v1

## 目的

统一 Action Runtime 边界：

- 动作协议属于 `Scene Runtime`
- Workbench 是动作消费者，不定义私有动作协议

## 运行链路

`Intent -> Scene -> Action -> Mutation -> Projection -> Refresh`

## Action 协议

```json
{
  "id": "approve_payment_request",
  "label": "批准",
  "intent": "record.update",
  "target_scene": "finance.payment_requests",
  "mutation": {
    "type": "write",
    "model": "finance.payment.request",
    "operation": "approve",
    "payload_schema": {
      "required": ["record_id"]
    }
  },
  "refresh_policy": {
    "on_success": ["scene_projection", "workbench_projection"],
    "scope": "local"
  },
  "visibility": {
    "roles": ["finance", "executive"],
    "permissions": ["finance.payment_requests.approve"]
  }
}
```

## 约束

- `core` 场景动作必须声明 `mutation`。
- `core` 场景动作必须声明 `refresh_policy`。
- 未满足约束的动作不得进入 `product_ready`。

## Workbench 角色

- Workbench 仅消费 `scene_action_protocol_v1.actions[]`。
- `action_source` 固定为 `workbench_projection`。


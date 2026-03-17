# Mutation Contract v1

## 目标

避免 Action Runtime 退化为任意 RPC，建立可验证的写回语义层。

## 合同结构

```json
{
  "mutation": {
    "type": "write",
    "model": "finance.payment.request",
    "operation": "approve",
    "payload_schema": {
      "required": ["record_id"],
      "properties": {
        "record_id": {"type": "integer"},
        "comment": {"type": "string"}
      }
    }
  }
}
```

## 字段定义

- `type`：`write/create/transition/assign/custom`
- `model`：目标模型
- `operation`：业务语义操作名
- `payload_schema`：输入参数约束

## 约束

- `core` 场景 action 必须声明 mutation。
- mutation 必须可映射到可审计的后端 service 操作。
- mutation 执行后必须绑定至少一个 `projection refresh` 目标。


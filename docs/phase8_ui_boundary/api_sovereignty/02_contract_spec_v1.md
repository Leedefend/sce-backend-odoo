# Smart Construction · API Contract Spec v1

**版本**：v1.0  
**目的**：提供稳定、统一、可演进的 API 交互契约，使能力不依赖 UI。

---

## 1) 总体约定

### 1.1 版本与兼容
- Contract 版本：`v1`
- **兼容原则**：v1 内只允许“新增字段/新增端点”，不做破坏性变更。
- 破坏性变更进入 v2，并提供迁移说明。

### 1.2 编码与时区
- UTF-8
- 时间字段统一 ISO8601（建议带时区偏移），例如：`2025-12-17T05:30:46+08:00`

---

## 2) 响应 Envelope（统一结构）

### 2.1 成功响应
```json
{
  "meta": {
    "request_id": "uuid-or-trace-id",
    "server_time": "2025-12-17T05:30:46+08:00",
    "contract_version": "v1",
    "etag": "W/\"...\"" 
  },
  "data": {},
  "errors": []
}
```

### 2.2 失败响应

```json
{
  "meta": {
    "request_id": "uuid-or-trace-id",
    "server_time": "2025-12-17T05:30:46+08:00",
    "contract_version": "v1"
  },
  "data": null,
  "errors": [
    {
      "code": "SC.AUTH.FORBIDDEN",
      "message": "Permission denied",
      "details": {
        "required_groups": ["group_sc_cap_finance_user"],
        "operation": "payment_request.create"
      }
    }
  ]
}
```

---

## 3) 错误码规范（建议）

* `SC.AUTH.UNAUTHORIZED`：未登录/Token 无效（HTTP 401）
* `SC.AUTH.FORBIDDEN`：已登录但无权限（HTTP 403）
* `SC.NOT_FOUND`：资源不存在（HTTP 404）
* `SC.VALIDATION.ERROR`：校验失败（HTTP 400）
* `SC.CONFLICT`：并发/状态冲突（HTTP 409）
* `SC.RATE_LIMIT`：限流（HTTP 429）
* `SC.INTERNAL.ERROR`：未知错误（HTTP 500）

> 重要：避免在 403/404 的选择上泄露敏感资源存在性；默认优先 403。

---

## 4) 分页/排序/过滤（v1 规范）

### 4.1 列表请求 Query 参数（推荐 Cursor）

* `limit`：默认 50，最大 200
* `cursor`：游标（首次为空）
* `order`：如 `create_date desc`
* `fields`：可选字段投影（减少 payload）
* `q`：全文/关键字（可选）
* `domain`：高级过滤（v1 先声明，v2 再增强）

### 4.2 列表响应 data 结构

```json
{
  "items": [],
  "page": {
    "limit": 50,
    "next_cursor": "xxx",
    "has_more": true
  }
}
```

---

## 5) 幂等（写操作必须支持）

### 5.1 Header

* `Idempotency-Key: <uuid>`
* 服务端需保证：相同 key 在 TTL 内重复请求不会产生重复副作用

### 5.2 响应 meta

* `meta.idempotency_key` 可选回显
* `meta.replayed` 可选（true/false）

---

## 6) 并发控制（ETag，可选但建议）

* GET 返回 `meta.etag`
* 更新时携带 `If-Match: <etag>`
* ETag 不一致 → `SC.CONFLICT`（HTTP 409）

---

## 7) 资源表示（Record 规范）

### 7.1 基础 Record

```json
{
  "id": 123,
  "display_name": "PR-2025-0001"
}
```

### 7.2 Many2one 表示

```json
{
  "id": 45,
  "display_name": "合同A",
  "model": "project.contract"
}
```

### 7.3 One2many/Many2many（v1 简化）

* 列表接口返回 `ids` 或 `items`（二选一，v1 建议 ids + 单独 list）

```json
{
  "line_ids": [1, 2, 3]
}
```

---

## 8) 业务动作（Action）规范

很多工程单据不是“CRUD”能描述完的，必须定义 action：

* `submit`
* `approve`
* `reject`
* `cancel`
* `reset_to_draft`

### Action 请求与响应

```json
POST /api/v1/payment_requests/{id}/actions/submit
{
  "meta": {...},
  "data": { "comment": "提交审批" },
  "errors": []
}
```

---

## 9) 权限声明（与 capability groups 对齐）

* 每个 endpoint/operation 必须声明：

  * `required_groups`（最小组集合）
  * `capability_operation`（如 `finance.payment_request.submit`）

---

## 10) 日志与审计（v1 只声明）

* 所有写操作必须可审计：谁、何时、对哪个资源、做了什么 action、结果如何。
* 审计落点：Odoo chatter / mail.message / 自研 audit 表（v1 不实现，只规定必须有）。

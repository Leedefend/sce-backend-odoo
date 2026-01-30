# Stable Response Fields v0.1 (login / system.init / ui.contract)

目标：前端只依赖“稳定字段集”，避免猜测结构。

## 通用 Envelope（v0.1）
以下字段为稳定字段，除非升级版本，不做破坏性变更：

- `ok` (bool)
- `code` (int, 可选，默认 200)
- `error` (object, 仅当 ok=false)
  - `code` (int)
  - `message` (string)
- `data` (object, 可选，默认 {})
- `meta` (object, 可选)
  - `trace_id` (string, 若有)
  - `intent` (string, 若有)
  - `etag` (string, 若有)
  - `elapsed_ms` (int, 若有)

注意：`trace_id`/`etag` 等可选字段在不同环境可能缺失，前端必须容错。

## 1) login
### 稳定 data 字段
- `token` (string)
- `token_type` (string, e.g. "Bearer")
- `expires_at` (int, epoch seconds)
- `user` (object)
  - `id` (int)
  - `name` (string)
  - `login` (string)
  - `groups` (array of string, optional)
  - `lang` (string, optional)
  - `tz` (string, optional)
  - `company_id` (int|null, optional)
  - `allowed_company_ids` (array of int, optional)
- `system` (object)
  - `intents` (array of {name, description})

### 示例（脱敏）
```json
{
  "ok": true,
  "data": {
    "token": "<token>",
    "token_type": "Bearer",
    "expires_at": 1700000000,
    "user": {
      "id": 2,
      "name": "Demo User",
      "login": "demo",
      "groups": ["base.group_user"],
      "lang": "zh_CN",
      "tz": "Asia/Shanghai",
      "company_id": 1,
      "allowed_company_ids": [1]
    },
    "system": {
      "intents": [
        {"name": "system.init", "description": "系统初始化"}
      ]
    }
  },
  "meta": {
    "trace_id": "xxxxxx"
  }
}
```

## 2) system.init
### 稳定 data 字段
- `user` (object)
  - `id` (int)
  - `name` (string)
  - `groups_xmlids` (array of string)
  - `lang` (string)
  - `tz` (string)
  - `company_id` (int|null)
- `nav` (array)
- `nav_meta` (object)
  - `fingerprint` (string)
- `default_route` (object)
- `intents` (array of string)
- `feature_flags` (object)
- `preload` (array)

### 示例（脱敏）
```json
{
  "ok": true,
  "data": {
    "user": {
      "id": 2,
      "name": "Demo User",
      "groups_xmlids": ["base.group_user"],
      "lang": "zh_CN",
      "tz": "Asia/Shanghai",
      "company_id": 1
    },
    "nav": [],
    "nav_meta": {"fingerprint": "<fp>"},
    "default_route": {"menu_id": null},
    "intents": ["system.init", "ui.contract"],
    "feature_flags": {"ai_enabled": true},
    "preload": []
  },
  "meta": {
    "etag": "<etag>",
    "trace_id": "xxxxxx"
  }
}
```

## 3) ui.contract
### 稳定 data 字段
- `views` (object, optional)
- `fields` (object, optional)
- `buttons` (array, optional)
- `actions` (array, optional)
- `permissions` (object, optional)

### 示例（脱敏）
```json
{
  "ok": true,
  "data": {
    "views": {},
    "fields": {},
    "buttons": [],
    "actions": [],
    "permissions": {}
  },
  "meta": {
    "etag": "<etag>",
    "intent": "ui.contract",
    "trace_id": "xxxxxx"
  }
}
```

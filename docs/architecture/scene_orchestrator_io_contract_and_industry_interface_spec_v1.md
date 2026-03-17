# Scene Orchestrator 输入/输出契约与行业编排接口规范 v1

日期：2026-03-15  
范围：`Scene Orchestrator` 运行时输入输出契约、行业编排接口、合并优先级

---

## 1. 目标

本规范用于把“编排边界”落到可执行接口，明确：

1. `Scene Orchestrator` 的标准输入契约（Input Contract）
2. `Scene-ready Contract` 的标准输出契约（Output Contract）
3. 行业 `Profile / Policy / Provider` 的接口定义
4. 编排执行顺序与 merge 优先级规则
5. 运行时守卫与错误降级行为

---

## 2. 核心原则

1. 前端只消费 `Scene-ready Contract`。
2. 原生契约（`UI Base Contract`）只能作为编排输入，不得直接透传前端。
3. 行业扩展只能通过 `Profile + Policy + Provider` 接口接入。
4. 平台编排引擎拥有最终 schema 裁决权。

---

## 3. 输入契约（Input Contract）

### 3.1 顶层结构

```json
{
  "scene_key": "projects.list",
  "runtime": {
    "user_id": 2,
    "role_code": "pm",
    "company_id": 1,
    "contract_mode": "user",
    "scene_channel": "stable"
  },
  "base_contract": {
    "contract_kind": "ui_base",
    "asset_ref": {
      "source": "runtime|asset",
      "asset_id": 0,
      "asset_version": "h-xxxx",
      "asset_hash": "sha1..."
    },
    "facts": {
      "views": {},
      "fields": {},
      "search": {},
      "actions": {},
      "permissions": {},
      "workflow": {},
      "validator": {}
    }
  },
  "composition": {
    "profile": {},
    "policies": {},
    "providers": []
  },
  "delivery": {
    "enabled": true,
    "surface": "default"
  }
}
```

### 3.2 子契约要求

- `base_contract.facts.views`：至少含当前 scene 必需视图事实。
- `base_contract.facts.permissions`：必须存在（可空对象，不可缺失）。
- `composition.profile`：必须提供 `scene_key` 对应 profile。
- `composition.policies`：允许为空，但需返回空对象而非 `null`。

---

## 4. 输出契约（Output Contract）

### 4.1 标准结构

```json
{
  "scene": {
    "key": "projects.list",
    "title": "项目列表",
    "layout": {"kind": "list"}
  },
  "page": {
    "route": "/s/projects.list",
    "zones": [
      {"name": "header", "blocks": []},
      {"name": "toolbar", "blocks": []},
      {"name": "main", "blocks": []}
    ]
  },
  "blocks": [],
  "actions": [],
  "search_surface": {},
  "workflow_surface": {},
  "permission_surface": {},
  "meta": {
    "compile_verdict": {
      "ok": true,
      "base_contract_bound": true,
      "issues": []
    },
    "source_trace": {
      "base_contract_source": "runtime|asset",
      "profile_source": "industry|platform_default",
      "provider_hits": []
    }
  }
}
```

### 4.2 输出硬约束

1. `scene/page/actions/meta` 必须存在。
2. `permission_surface` 必须输出（可空对象，不可缺失）。
3. `meta.compile_verdict` 必须输出。
4. 输出中禁止原样透传整包 `base_contract`。

---

## 5. 行业编排接口规范

## 5.1 Scene Profile Schema

```json
{
  "scene_key": "projects.list",
  "title": "项目列表",
  "scene_type": "list",
  "layout": {"kind": "list"},
  "zones": ["header", "toolbar", "main"],
  "block_templates": ["list.main", "stats.summary"]
}
```

必填：`scene_key/scene_type/layout/zones`。

## 5.2 Policy Schema

```json
{
  "action_policy": {
    "primary": ["create_project"],
    "secondary": ["export"],
    "hidden_by_role": {"finance": ["create_project"]}
  },
  "search_policy": {
    "default_filters": ["my_projects"],
    "default_group_by": ["stage_id"]
  },
  "workflow_policy": {
    "highlight_states": ["risk", "blocked"]
  },
  "navigation_policy": {
    "workspace_entry": true,
    "priority": 80
  }
}
```

## 5.3 Provider Interface

Provider 统一签名：

```python
def provide(scene_key: str, runtime: dict, context: dict) -> dict:
    return {
        "blocks": [],
        "actions": [],
        "hints": [],
        "metrics": {},
        "diagnostics": {}
    }
```

约束：

- Provider 不得直接改写 `base_contract.facts`。
- Provider 只产出增强数据（blocks/actions/hints/metrics）。

---

## 6. 编排执行顺序

标准顺序：

1. `Input Normalize`
2. `Grammar Validate`
3. `Semantic Validate`
4. `Base Fact Bind`
5. `Profile Apply`
6. `Policy Apply`
7. `Provider Merge`
8. `Surface Build`
9. `Permission/Workflow Gate`
10. `Output Compile`

---

## 7. Merge 优先级规则

从低到高：

1. 平台默认规则（Platform Default）
2. 原生能力事实（Base Fact）
3. 行业 Profile
4. 行业 Policy
5. Provider 运行时增强
6. 权限与治理裁决（最终裁决层）

冲突处理：

- 权限裁决始终高于 action/profile/provider。
- Policy 可以隐藏 action，但不能新增无权限 action。
- Provider 可以追加 block，不能删除必需安全区块（如 permission 提示区块）。

---

## 8. 失败与降级策略

### 8.1 可降级失败

- provider 执行失败
- 非关键 policy 缺失
- 辅助 surface 缺失

处理：记录 `meta.compile_verdict.issues`，输出降级可用页面。

### 8.2 不可降级失败

- scene_key 无效
- 必需 base facts 缺失（如关键视图事实）
- permission 判定不可用

处理：返回可诊断错误契约，不返回伪成功页面。

---

## 9. 运行时验证门禁建议

新增/扩展 verify 项：

1. `verify.scene.orchestrator.input.schema.guard`
2. `verify.scene.orchestrator.output.schema.guard`
3. `verify.scene.orchestrator.base_fact_binding.guard`
4. `verify.scene.orchestrator.industry_interface.guard`
5. `verify.frontend.no_base_contract_direct_consume.guard`

---

## 10. 版本策略

- Input contract 版本：`scene_orchestrator_input_v1`
- Output contract 版本：`scene_ready_contract_v1`
- Profile schema 版本：`scene_profile_v1`
- Policy schema 版本：`scene_policy_v1`
- Provider interface 版本：`scene_provider_v1`

不兼容变更必须升级版本并保留兼容窗口。

---

## 11. 最终结论

`Scene Orchestrator` 的职责不是搬运原生契约，而是把原生能力事实、行业策略与治理裁决编译为前端唯一可执行语言：`Scene-ready Contract`。


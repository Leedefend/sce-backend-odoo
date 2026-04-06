# app_config_engine 承载 Capability Registry Core 设计稿 v1

- version: `v1`
- date: `2026-04-06`
- status: `design-freeze`
- layer target: `platform / app_config_engine`

## 1. 决策结论

`app_config_engine` 作为平台配置与契约引擎，正式承载 `Capability Registry Core` 子域。

边界定义：

- 平台拥有：`schema`、`contribution loader`、`merge`、`binding`、`policy`、`projection`、`lint/guard/freeze`。
- 行业模块拥有：`capability contribution definitions`（仅贡献定义，不拥有主注册表与主投影）。

## 2. 目标与非目标

### 2.1 目标

- 统一能力资产模型（平台标准 schema）。
- 统一注册主权（平台唯一 registry）。
- 统一绑定关系（scene/intent/contract/exposure）。
- 统一策略语义（visibility/permission/release/lifecycle）。
- 统一运行时投影（list/matrix/workspace/governance）。
- 统一治理门禁（lint/snapshot/freeze/guard）。

### 2.2 非目标

- 不在 registry core 内执行行业业务规则。
- 不在本批次重写前端消费代码。
- 不引入行业模块作为 registry 主容器。

## 3. 模块结构（宿主：app_config_engine）

```text
addons/smart_core/app_config_engine/
├─ capability/
│  ├─ schema/
│  │  ├─ capability_schema.py
│  │  ├─ binding_schema.py
│  │  └─ policy_schema.py
│  ├─ core/
│  │  ├─ registry.py
│  │  ├─ contribution_loader.py
│  │  ├─ merge_engine.py
│  │  ├─ ownership.py
│  │  └─ freeze.py
│  ├─ bindings/
│  │  ├─ scene_binding.py
│  │  ├─ intent_binding.py
│  │  ├─ contract_binding.py
│  │  └─ exposure_binding.py
│  ├─ policy/
│  │  ├─ visibility_policy.py
│  │  ├─ permission_policy.py
│  │  ├─ release_policy.py
│  │  └─ lifecycle_policy.py
│  ├─ projection/
│  │  ├─ capability_list_projection.py
│  │  ├─ capability_matrix_projection.py
│  │  ├─ workspace_projection.py
│  │  └─ governance_projection.py
│  ├─ lint/
│  │  ├─ schema_lint.py
│  │  ├─ binding_lint.py
│  │  ├─ release_lint.py
│  │  └─ ownership_lint.py
│  └─ services/
│     ├─ capability_registry_service.py
│     ├─ capability_query_service.py
│     └─ capability_runtime_service.py
```

## 4. 能力对象 schema 草案

```python
Capability = {
  "identity": {
    "key": "project.dashboard.enter",
    "name": "项目驾驶舱",
    "domain": "project",
    "type": "entry",
    "version": "v1"
  },
  "ownership": {
    "owner_module": "smart_core",
    "source_module": "smart_construction_core",
    "source_kind": "industry_contribution"
  },
  "ui": {
    "group_key": "project_management",
    "label": "项目驾驶舱",
    "icon": "briefcase",
    "sequence": 40,
    "tags": ["project", "dashboard"]
  },
  "binding": {
    "scene": {"entry_scene_key": "projects.dashboard"},
    "intent": {"primary_intent": "project.dashboard.enter"},
    "contract": {"subject": "scene", "contract_type": "entry_contract"},
    "exposure": {"workspace_tile": True, "nav_app": "projects"}
  },
  "permission": {
    "required_roles": ["pm"],
    "required_groups": ["smart_construction_core.group_sc_cap_project_read"],
    "access_mode": "execute"
  },
  "lifecycle": {
    "status": "ga",
    "deprecated": False,
    "replacement_key": ""
  },
  "release": {
    "tier": "top",
    "slice": "FR-3",
    "exposure_mode": "default"
  }
}
```

字段约束：

- `identity.key` 全局唯一。
- `ownership.owner_module` 必须是平台主控模块。
- `source_module` 仅表示贡献来源，不代表 owner。
- `binding` 必须结构化，禁止松散字段漂移。

## 5. 注册与合并机制

### 5.1 contribution 输入协议

行业/平台模块暴露：

```python
def get_capability_contributions(env, user=None) -> list[dict]:
    ...
```

### 5.2 合并规则

- Rule-A `owner-define`：主对象仅 owner 定义。
- Rule-B `extension-patch`：非 owner 仅可补充白名单字段（ui/release 部分字段）。
- Rule-C `override-allowlist`：仅白名单 key 可 override，且需审计记录。

### 5.3 冻结与快照

- `registry snapshot`
- `per-role matrix snapshot`
- `release slice snapshot`

## 6. 运行时投影接口

- `CapabilityQueryService.list_capabilities_for_user(user, context)`
- `CapabilityQueryService.build_capability_matrix_for_user(user, context)`
- `CapabilityRuntimeService.build_workspace_projection(user, context)`
- `CapabilityRegistryService.get_registry_snapshot()`

## 7. 治理门禁（guard）

- `schema_lint`：字段合法性与必填约束。
- `ownership_guard`：禁止行业模块拥有 registry 主容器。
- `binding_guard`：scene/intent/contract/exposure 绑定完整性。
- `release_guard`：deprecated/replacement/slice 一致性。
- `freeze_guard`：冻结能力面不可无审批漂移。

## 8. 迁移步骤（Batch A/B/C）

### Batch A（本批次）

- 完成结构设计与 schema 草案冻结。
- 固化迁移顺序与 guard 清单。

### Batch B（核心迁移）

- 在 `app_config_engine/capability/core` 实现 `contribution_loader + merge_engine + registry`。
- 把现有 capability 定义改造成 contribution source。
- 接入 `ownership_lint + schema_lint`。

### Batch C（运行接管）

- 把现有 `capability_provider` 的运行时读取切换为 `CapabilityQueryService`。
- 接入 `projection` 输出层（list/matrix/workspace）。
- 增加 `freeze/snapshot` 与 release gate。

## 9. 验收标准（后续实现批次）

- 平台 registry 单一 owner。
- 行业模块只提交 contribution。
- 无 legacy runtime fallback 直连行业桥接。
- 前端消费标准 projection 契约。
- guard 全绿并可重复执行。

## 10. 风险与回滚

风险：

- 旧模块若仅实现 legacy hook，会在切换后失效。
- binding 结构化后可能暴露历史能力定义缺口。

回滚原则：

- 每批次保持可回退；先落 guard 再切运行路径。
- 以 snapshot diff 作为回滚触发证据。

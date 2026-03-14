# 场景编排层平台/行业分层落地（Round 3）

## 目标

在 Round 1/2 基础上，将 `projects.list` 与 `projects.ledger` 的场景内容从 registry fallback 主体中抽离，改为行业 provider 注入，进一步压缩“平台机制与行业内容混放”。

## 本轮变更

### 平台层（机制）

- 扩展定位器：`addons/smart_scene/core/provider_locator.py`
  - 新增 `resolve_scene_registry_content_path`。

### 行业层（内容）

- 新增行业 provider：`addons/smart_construction_scene/services/scene_registry_content.py`
  - 提供 `list_scene_entries()`，承载：
    - `projects.list`
    - `projects.ledger`

### 接线与兼容

- 更新 `addons/smart_construction_scene/scene_registry.py`
  - 新增动态加载行业 provider 的能力。
  - 从 fallback 主体中移除 `projects.list / projects.ledger` 内联定义。
  - 通过 provider 注入并按 `code` 去重覆盖，保持结果稳定。

## 验证结果

- `make verify.scene.schema` PASS
- `make verify.scene.contract.semantic.v2.guard` PASS
- `make verify.page_orchestration.target_completion.guard` PASS
- `make verify.project.dashboard.contract` PASS
- `make verify.workspace_home.orchestration_schema.guard` PASS

## 结论

`projects.list / projects.ledger` 已进入“平台注入机制 + 行业内容 provider”模式，满足本轮分层目标。

## 下一步（Round 4 建议）

1. 继续抽离其他 scene fallback（如 `project.management`、`risk.center`）到行业 provider。
2. 将 scene content provider 形状纳入 schema guard。
3. 形成统一 `scene content provider` 目录规范与自动发现机制。


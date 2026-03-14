# 场景编排层平台/行业分层落地（Round 4）

## 目标

继续推进 scene registry 场景内容分层，将 `project.management` 与 `risk.center` 从 fallback 主体抽离到行业 provider，并在加载链路加入基础形状校验。

## 本轮变更

### 行业内容 provider 扩展

- 文件：`addons/smart_construction_scene/services/scene_registry_content.py`
- 新增场景条目：
  - `project.management`
  - `risk.center`

### registry 注入链路增强

- 文件：`addons/smart_construction_scene/scene_registry.py`
- 增强 `_load_scene_registry_content_entries()`：
  - 对 provider 条目执行最小形状校验：
    - 必须有 `code`
    - `target` 至少具备 route/menu/action/model 中之一
  - 无效条目自动丢弃，防止污染 fallback 合并结果

### fallback 主体收口

- 从 `load_scene_configs()` 的 fallback 主体中移除：
  - `project.management`
  - `risk.center`

## 验证建议

- `make verify.scene.schema`
- `make verify.scene.contract.semantic.v2.guard`
- `make verify.page_orchestration.target_completion.guard`

## 结论

Round 4 完成后，核心高频场景的 registry 内容进一步从“混合 fallback 主体”迁移到“行业 provider + 平台注入”，分层边界更清晰。


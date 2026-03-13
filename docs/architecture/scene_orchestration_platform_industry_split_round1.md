# 场景编排层平台/行业分层落地（Round 1）

## 目标

按 `scene_orchestration_layer_design_v1` 要求，完成首批“平台级内核 vs 行业级内容”拆分，覆盖 `workspace.home` 编排链路。

## 分层结果

- 平台侧（机制）：`addons/smart_scene/core/provider_locator.py`
  - 负责 provider 解析顺序与回退策略。
- 行业侧（内容）：`addons/smart_construction_scene/services/workspace_home_scene_content.py`
  - 承载 `workspace.home` 业务模板、优先级与文案语义。
- 平台兼容适配：`addons/smart_core/core/workspace_home_data_provider.py`
  - 仅保留向行业 provider 的代理与兼容 fallback，不再承载行业内容定义。

## 执行策略

1. `smart_core` 编排器优先通过 `smart_scene` 定位器加载行业 provider。
2. 行业 provider 不可用时回退 legacy provider，保证链路稳定。
3. 逐步把其他 scene 的行业内容迁移到 `smart_construction_scene`，平台层保留机制与 schema。

## 验收标准

- 现有编排验证 guard 全部通过。
- `workspace.home` 输出行为不回退。
- 新增分层文件可被后续 scene 扩展复用。

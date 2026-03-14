# smart_scene 平台编排内核能力状态（Round 7）

## 目标

在完成平台/行业分层迁移后，补齐 `smart_scene` 平台侧核心引擎的最小可运行能力。

## 本轮新增能力（平台层）

- `scene_resolver.py`
  - 提供 `resolve_scene_identity()`，统一 scene/page 身份解析。
- `structure_mapper.py`
  - 提供 `map_zone_specs_to_blocks()`，将 zone specs 标准化。
- `layout_orchestrator.py`
  - 提供 `apply_zone_priority()`，按策略生成 zone priority。
- `capability_injector.py`
  - 提供 `inject_extension_blocks()`，支持增量扩展 block 注入。
- `scene_contract_builder.py`
  - 提供 `build_scene_contract()`，统一 Scene Contract 组装。
- `scene_engine.py`
  - 提供 `build_scene_contract_from_specs()`，形成 resolver→mapper→layout→contract 的最小闭环。

## 接线落地

- `project_dashboard_service.py`
  - 已接入 `smart_scene.core.scene_engine` 生成 contract，保留 fallback 兼容。
- `workspace_home_contract_builder.py`
  - 已接入 `smart_scene.core.scene_engine` 做输出链路预接线（当前保留原输出主链，记录引擎 shape 诊断）。
- `smart_scene/schemas` + `smart_scene/services`
  - 已新增 `scene_contract_schema.py` 与 `contract_guard.py`，形成平台侧契约 shape 校验最小闭环。

## 验证结果

- `make verify.project.dashboard.contract` PASS
- `make verify.workspace_home.orchestration_schema.guard` PASS
- `make verify.scene.schema` PASS
- `make verify.scene.contract.semantic.v2.guard` PASS
- `make verify.page_orchestration.target_completion.guard` PASS

## 当前状态判断

- 已达成：平台编排内核“最小可跑”能力。
- 未完成：
  - Scene Contract v1 字段级强校验接线
  - provider shape guard 独立 target
  - 更多 scene 统一接入 `scene_engine`

## 下一步建议

1. 增加 provider shape guard（make target），补齐平台治理护栏。
2. 将 `workspace.home` 编排输出链从“预接线”升级为 `scene_engine` 主输出路径。
3. 扩展更多 scene 统一接入 `scene_engine`（list/form/search/kanban 代表样本）。

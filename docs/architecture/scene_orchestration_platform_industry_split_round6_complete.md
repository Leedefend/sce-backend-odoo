# 场景编排层平台/行业分层落地（Round 6 · 完整迁移）

## 目标

完成 scene registry fallback 的行业条目“完整迁移”：
- 行业场景事实统一进入行业场景编排数据层（provider）
- registry fallback 主体仅保留平台最小保底条目

## 本轮完成

### 1) 行业 provider 完整承载场景条目

文件：`addons/smart_construction_scene/services/scene_registry_content.py`

本轮已承载包含以下类别在内的完整条目：
- 项目类：`project.management` `projects.intake` `projects.list` `projects.ledger` `projects.dashboard`
- 工作台类：`my_work.workspace` `contracts.workspace` `finance.workspace` `cost.analysis` `risk.center`
- 业务入口类：`task.center` `contract.center` `finance.center` 等
- 成本/财务类：`cost.*` `finance.*`
- 门户类：`portal.*`

### 2) registry fallback 主体最小化

文件：`addons/smart_construction_scene/scene_registry.py`

`load_scene_configs()` 中 fallback 主体已收敛为仅两项平台保底：
- `default`
- `scene_smoke_default`

其余行业条目统一通过 provider 注入。

### 3) provider 注入链路仍保持形状校验

文件：`addons/smart_construction_scene/scene_registry.py`

`_load_scene_registry_content_entries()` 保留最小 shape 过滤：
- 必须有 `code`
- `target` 至少包含 route/menu/action/model 之一

## 验证结果

- `make verify.scene.schema` PASS
- `make verify.scene.contract.semantic.v2.guard` PASS
- `make verify.page_orchestration.target_completion.guard` PASS
- `make verify.project.dashboard.contract` PASS
- `make verify.workspace_home.orchestration_schema.guard` PASS

## 结论

本轮已完成“从混合 fallback 到行业场景编排数据层”的完整迁移目标：
- 平台层保留机制与保底
- 行业层承载场景事实与编排内容

满足《scene_orchestration_layer_design_v1》中“平台机制 + 行业内容”边界要求。

# 场景编排层平台/行业分层落地（Round 5）

## 目标

继续收敛 scene registry fallback 主体中的行业内容条目，迁移高频工作台类场景到行业 provider，缩小“平台机制与行业内容混放”范围。

## 本轮迁移条目

迁移到 `addons/smart_construction_scene/services/scene_registry_content.py`：

- `contracts.workspace`
- `finance.workspace`
- `cost.analysis`
- `my_work.workspace`

## 代码变更

### 行业层（内容）

- 文件：`addons/smart_construction_scene/services/scene_registry_content.py`
- 扩展 `list_scene_entries()`，纳入本轮 4 个高频条目。

### registry 主体（收口）

- 文件：`addons/smart_construction_scene/scene_registry.py`
- 从 fallback 主体删除上述 4 个内联场景定义。
- 保持 provider 注入合并逻辑不变（按 `code` 去重覆盖）。

## 验证结果

- `make verify.scene.schema` PASS
- `make verify.scene.contract.semantic.v2.guard` PASS
- `make verify.page_orchestration.target_completion.guard` PASS
- `make verify.project.dashboard.contract` PASS
- `make verify.workspace_home.orchestration_schema.guard` PASS

## 当前剩余混放状态（摘要）

fallback 主体中仍存在一批行业场景条目（如 `task.center`、`contract.center`、`finance.*` 部分），建议后续按“高频优先 + 风险可控”继续分批迁移。

## 下一步建议（Round 6）

1. 迁移 `task.center / contract.center / finance.center`。
2. 给 `scene_registry_content.py` 增加 provider schema guard（独立 make target）。
3. 输出 fallback 主体剩余条目自动清单（便于阶段验收）。

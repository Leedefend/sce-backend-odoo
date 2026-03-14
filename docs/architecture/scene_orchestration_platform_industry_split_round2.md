# 场景编排层平台/行业分层落地（Round 2）

## 目标

在 Round 1（`workspace.home`）基础上，完成 `project.management` / `project.dashboard` 链路的“平台机制 + 行业内容”分层落地。

## 本轮变更

### 平台层（机制）

- 新增平台通用内核：`addons/smart_scene/core/dashboard_orchestration_kernel.py`
  - 提供单 block zone 编排能力（`build_single_block_zones`）。
- 扩展 provider 定位器：`addons/smart_scene/core/provider_locator.py`
  - 新增 `resolve_project_dashboard_scene_content_path`。

### 行业层（内容）

- 新增行业场景内容：`addons/smart_construction_scene/services/project_dashboard_scene_content.py`
  - 承载 `project.management.dashboard` 的 scene/page 元信息与 zone-block 内容定义。

### 兼容与接线

- `addons/smart_construction_core/services/project_dashboard_service.py`
  - 编排流程改为：
    1) 读取行业 scene content
    2) 调用平台 orchestration kernel 组装 zones
    3) 保留 `ZONE_BLOCKS` 兼容常量以满足现有 verify guard
  - 业务数据解析/项目解析逻辑保持不变。

## 分层结果

- 平台层负责：编排机制、provider 定位、contract 组装流程。
- 行业层负责：场景语义内容（标题、zone 组织、block 映射策略）。
- 现有协议与路由保持不变（无迁移成本）。

## 验证结果

- `make verify.project.dashboard.contract` PASS
- `make verify.page_orchestration.target_completion.guard` PASS
- `make verify.scene.contract.semantic.v2.guard` PASS

## 下一步（Round 3 建议）

1. 将更多场景（`projects.list` / `projects.ledger`）迁移至行业内容 provider。
2. 在平台层补 `Scene Contract v1` 结构抽样器并纳入固定验证链。
3. 逐步清理 `smart_core` 中行业内容残留，仅保留兼容代理。


# SCEMS v1.0 Phase 2：`finance.workspace` 场景落地报告

## 1. 目标
补齐 V1 主导航目标场景 `finance.workspace`，形成最小可用资金管理工作台入口。

## 2. 实施内容
- `scene_registry.py` 新增 `finance.workspace` fallback scene（路由 `/s/finance.workspace`，承接 `finance.center` menu/action）。
- `sc_scene_orchestration.xml` 新增 `sc_scene_finance_workspace`。
- `sc_scene_layout.xml` 新增 `sc_scene_version_finance_workspace_v2`，`layout.kind=workspace`。

## 3. 验证结果
- `python3 -m py_compile addons/smart_construction_scene/scene_registry.py` ✅
- `make verify.project.form.contract.surface.guard` ✅
- `make verify.scene.catalog.governance.guard` ✅

## 4. 下一步
- 补齐 `risk.center` 后，完成 Phase 2 四个待补齐 workspace 场景收口。


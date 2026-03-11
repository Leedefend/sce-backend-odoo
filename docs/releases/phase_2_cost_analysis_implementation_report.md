# SCEMS v1.0 Phase 2：`cost.analysis` 场景落地报告

## 1. 目标
补齐 V1 主导航目标场景 `cost.analysis`，形成最小可用工作台入口。

## 2. 实施内容
- `scene_registry.py` 新增 `cost.analysis` fallback scene（路由 `/s/cost.analysis`，承接到成本台账 action/menu）。
- `sc_scene_orchestration.xml` 新增 `sc_scene_cost_analysis`。
- `sc_scene_layout.xml` 新增 `sc_scene_version_cost_analysis_v2`，`layout.kind=workspace`。

## 3. 验证结果
- `python3 -m py_compile addons/smart_construction_scene/scene_registry.py` ✅
- `make verify.project.form.contract.surface.guard` ✅
- `make verify.scene.catalog.governance.guard` ✅

## 4. 下一步
- 继续补齐 `finance.workspace` 与 `risk.center`。


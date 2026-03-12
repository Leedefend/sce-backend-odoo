# SCEMS v1.0 Phase 2：`risk.center` 场景落地报告

## 1. 目标
补齐 V1 主导航目标场景 `risk.center`，形成最小可用风险提醒工作台入口。

## 2. 实施内容
- `scene_registry.py` 新增 `risk.center` fallback scene（路由 `/s/risk.center`，承接风险钻取 action）。
- `sc_scene_orchestration.xml` 新增 `sc_scene_risk_center`。
- `sc_scene_layout.xml` 新增 `sc_scene_version_risk_center_v2`，`layout.kind=workspace`。

## 3. 验证结果
- `python3 -m py_compile addons/smart_construction_scene/scene_registry.py` ✅
- `make verify.project.form.contract.surface.guard` ✅
- `make verify.scene.catalog.governance.guard` ✅

## 4. 结论
- Phase 2 计划中 4 个待补齐 workspace 场景（`contracts.workspace` / `cost.analysis` / `finance.workspace` / `risk.center`）已全部落地到最小可用版本。


# SCEMS v1.0 系统资产盘点（System Asset Inventory）

## 1. 盘点范围
- 代码资产：后端模块、前端应用、脚本
- 契约资产：scene/capability/intent/export
- 文档资产：发布、运维、演示、验收
- 验证资产：verify 脚本、基线、产物

## 2. 代码资产清单（初版）

### 2.1 后端
- `addons/smart_core`
- `addons/smart_construction_core`
- `addons/smart_construction_scene`

### 2.2 前端
- `frontend/apps/web`

### 2.3 运维与验证脚本
- `scripts/verify`
- `scripts/ops`
- `scripts/test`

## 3. 契约与导出资产
- `docs/contract/exports/scene_catalog.json`
- `docs/contract/exports/intent_catalog.json`
- `docs/product/delivery/v1/construction_pm_v1_scene_surface_policy.json`

## 4. 关键文档资产
- 总发布蓝图：`docs/releases/construction_system_v1_release_plan.md`
- 运行与发布：`docs/ops/releases/README.md`
- 演示文档目录：`docs/demo`

## 5. 验证资产（当前关键）
- `make verify.scene.catalog.governance.guard`
- `make verify.phase_next.evidence.bundle`
- `make verify.runtime.surface.dashboard.strict.guard`
- `make verify.project.form.contract.surface.guard`

## 6. 风险与待补项（盘点结论）
- 需补齐发布专用文档：部署指南、演示脚本、验收清单
- 需固化 V1 专属验证入口（dashboard/route/permission）
- 需建立 v1 发布证据目录与归档规范

## 7. 下一步动作
- 输出：`docs/releases/release_gap_analysis.md`
- 建立阶段任务看板并映射到 Phase 1~6


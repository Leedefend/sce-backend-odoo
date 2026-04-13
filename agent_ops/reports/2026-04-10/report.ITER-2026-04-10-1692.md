# ITER-2026-04-10-1692 Report

## Batch
- Batch: `P1-Batch21`
- Mode: `implement`
- Stage: `user-menu convergence for delivery`

## Architecture declaration
- Layer Target: `Frontend contract-consumer runtime + startup navigation delivery`
- Module: `system.init navigation output / frontend sidebar delivery`
- Module Ownership: `smart_core + frontend/apps/web`
- Kernel or Scenario: `scenario`
- Reason: 将技术可点击全量菜单收敛为可交付正式导航。

## Change summary
- 新增菜单收敛服务：`addons/smart_core/delivery/menu_delivery_convergence_service.py`
  - 支持分类：`delivery_user` / `delivery_admin` / `hidden_demo` / `hidden_technical` / `hidden_governance`
  - 执行演示/技术/治理/非正式入口过滤与 `项目台账（试点） -> 项目台账` 重命名。
- 接入后端导航接口：`addons/smart_core/controllers/platform_menu_api.py`
  - `/api/menu/tree`、`/api/menu/navigation` 均输出收敛后的导航。
  - 响应 `meta.delivery_convergence` 提供隐藏/保留/重命名差异。
- 同步 system.init 导航生成：`addons/smart_core/delivery/menu_service.py`
  - release navigation 同步应用收敛策略，确保前端缓存导航与接口导航一致。
- 前端消费收口：`frontend/apps/web/src/composables/useNavigationMenu.ts`
  - 强制依赖 `nav_explained` 正式导航契约，不再回落 raw `nav_fact`。
- 新增验证与快照脚本：`scripts/verify/menu_delivery_convergence_audit.py`
  - 产出 `artifacts/menu/delivery_user_navigation_v1.json`
  - 产出 `artifacts/menu/delivery_admin_navigation_v1.json`
  - 产出 `artifacts/menu/menu_convergence_diff_v1.json`

## Verification result
- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-10-1692.yaml` ✅
- `python3 scripts/verify/v2_app_governance_gate_audit.py --json` ✅ (`27/27 PASS`)
- `node scripts/verify/unified_system_menu_click_usability_smoke.mjs` ✅
  - artifact: `artifacts/codex/unified-system-menu-click-usability-smoke/20260411T152259Z/summary.json`
  - result: `leaf_count=28`, `fail_count=0`
- `python3 scripts/verify/menu_delivery_convergence_audit.py` ✅
  - baseline: `66`
  - delivery_user: `27`
  - delivery_admin: `212`

## Risk analysis
- 结论：`PASS`
- 风险级别：medium-low
- 说明：普通用户导航完成明显收敛且 smoke 持续全绿；管理员导航仍保留技术/治理面，符合运维可见性预期。

## Rollback suggestion
- `git restore addons/smart_core/controllers/platform_menu_api.py`
- `git restore addons/smart_core/delivery/menu_delivery_convergence_service.py`
- `git restore addons/smart_core/delivery/menu_service.py`
- `git restore addons/smart_core/core/delivery_menu_defaults.py`
- `git restore frontend/apps/web/src/composables/useNavigationMenu.ts`
- `git restore scripts/verify/menu_delivery_convergence_audit.py`

## Next suggestion
- 进入 `ITER-1693`：冻结正式入口页面清单，补齐错误态/空态/trace_id 页面级交付证据并生成评审文档。

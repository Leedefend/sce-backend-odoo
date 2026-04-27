# Menu Owner Signal Residual Exemption Batch 20260427

## 1. 本轮变更
- 目标：收口 `verify.menu.scene_resolve.container` 暴露的 2 个 owner-signal 残余菜单。
- 完成：
  - 将 `smart_construction_core.menu_sc_project_quick_create` 加入 menu scene 覆盖豁免。
  - 将 `smart_construction_demo.menu_sc_project_list_showcase` 加入 menu scene 覆盖豁免。
  - 固化原因：两者均为双轨规范下的 `action/menu` 兼容入口，`scene_key` 不能单独作为 scene owner signal。
- 未完成：旧验证脚本中仍存在 demo showcase 与 `projects.list` 的历史绑定，留到下一批次单独清理。

## 2. 影响范围
- 模块：`docs/ops/verify`、`docs/ops/iterations`
- 启动链：否
- contract/schema：否
- default_route：否
- Odoo 运行时代码：否

## 3. 风险
- P0：无，未改运行时代码。
- P1：豁免项若未来被产品定义为正式 scene 入口，需要从豁免清单移除并补真实 owner signal。
- P2：`scripts/verify/fe_menu_scene_key_smoke.js` 与 `scripts/verify/fe_scene_core_openable_guard.js` 仍含 demo showcase 旧绑定，可能影响后续旧 guard。

## 4. 验证
- `node --check scripts/verify/fe_menu_scene_resolve_smoke.js`：PASS
- `make verify.menu.scene_resolve.container DB_NAME=sc_demo E2E_LOGIN=demo_pm E2E_PASSWORD=demo ARTIFACTS_DIR=/mnt/artifacts`：PASS
- `git diff --check -- docs/ops/verify/menu_scene_exemptions.yml docs/ops/iterations/menu_owner_signal_residual_exemption_batch_20260427.md docs/ops/iterations/delivery_context_switch_log_v1.md`：PASS

## 5. 产物
- scene resolve artifact：`artifacts/codex/portal-menu-scene-resolve/20260427T032620`
- docs：`docs/ops/iterations/menu_owner_signal_residual_exemption_batch_20260427.md`

## 6. 回滚
- 方法：回退本批次提交，或从 `docs/ops/verify/menu_scene_exemptions.yml` 删除新增的两个 xmlid。
- 数据/升级：无需 `-u`，无需重启。

## 7. 下一批次
- 目标：清理旧验证脚本中的 demo showcase canonical scene 绑定，避免 guard 与双轨契约冲突。
- 前置条件：继续以 `navigation_dual_track_contract_v1.md` 的 owner-signal 规则为准。

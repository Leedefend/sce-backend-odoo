# Menu Dual Track Verify Guard Cleanup Batch 20260427

## 1. 本轮变更
- 目标：清理旧验证脚本中 demo showcase 与 canonical `projects.list` 的历史绑定。
- 完成：
  - `fe_menu_scene_key_smoke.js` 改为检查 canonical `smart_construction_core.menu_sc_root -> projects.list`。
  - `fe_scene_core_openable_guard.js` 改为要求 `projects.list` 使用 `smart_construction_core.action_sc_project_list`。
  - `fe_scene_core_openable_guard.js` 的静态读取源改为当前 scene registry content 权威文件。
  - 保留 demo showcase 作为旧 `action/menu` 轨入口，不再作为 canonical scene guard 依据。
- 未完成：未改运行时 scene registry 或导航契约。

## 2. 影响范围
- 模块：`scripts/verify`、`docs/ops/iterations`
- 启动链：否
- contract/schema：否
- default_route：否
- Odoo 运行时代码：否

## 3. 风险
- P0：无，未改运行时代码。
- P1：若旧环境仍依赖 demo showcase 作为 `projects.list` 目标，新的 guard 会暴露该环境与双轨规范不一致。
- P2：`fe_menu_scene_key_smoke.js` 对缺失菜单仍采用 SKIP 语义，本批次只修正目标身份，不扩大 guard 严格度。

## 4. 验证
- `node --check scripts/verify/fe_menu_scene_key_smoke.js scripts/verify/fe_scene_core_openable_guard.js`：PASS
- `node scripts/verify/fe_scene_core_openable_guard.js`：PASS
- `make verify.portal.menu_scene_key_smoke.container DB_NAME=sc_demo E2E_LOGIN=demo_pm E2E_PASSWORD=demo ARTIFACTS_DIR=/mnt/artifacts`：PASS
- `git diff --check -- scripts/verify/fe_menu_scene_key_smoke.js scripts/verify/fe_scene_core_openable_guard.js docs/ops/iterations/menu_dual_track_verify_guard_cleanup_batch_20260427.md docs/ops/iterations/delivery_context_switch_log_v1.md`：PASS

## 5. 产物
- scene key artifact：`artifacts/codex/portal-shell-v0_8-6/20260427T033036`
- docs：`docs/ops/iterations/menu_dual_track_verify_guard_cleanup_batch_20260427.md`

## 6. 回滚
- 方法：回退本批次提交，恢复两个验证脚本的旧 target/marker。
- 数据/升级：无需 `-u`，无需重启。

## 7. 下一批次
- 目标：继续扫描菜单规范化剩余验证目标，确认是否还有 `scene_key` 被当作 owner signal 的旧断言。
- 前置条件：以 `navigation_dual_track_contract_v1.md` 的 owner-signal 规则为准。

# Menu Navigation Verify Docs Batch 20260427

## 1. 本轮变更
- 目标：补齐 `/api/menu/navigation` 字段快照验证目标的运维说明。
- 完成：
  - 在 `docs/ops/verify/README.md` 记录 `verify.menu.navigation_snapshot.container`。
  - 在 `docs/ops/verify/README.md` 记录 `verify.menu.navigation_snapshot` host 模式。
  - 明确 required fields、artifact 路径、host artifact 权限规避方式。
- 未完成：未改验证脚本与 Makefile。

## 2. 影响范围
- 模块：`docs/ops/verify`、`docs/ops/iterations`
- 启动链：否
- contract/schema：否
- default_route：否
- Odoo 运行时代码：否

## 3. 风险
- P0：无，文档-only。
- P1：如果后续脚本字段集变化，需要同步更新 README。
- P2：host/container artifact 权限仍取决于本地目录 owner，文档已给出 `ARTIFACTS_DIR` 规避方式。

## 4. 验证
- `git diff --check -- docs/ops/verify/README.md docs/ops/iterations/menu_navigation_verify_docs_batch_20260427.md docs/ops/iterations/delivery_context_switch_log_v1.md`：PASS
- `rg -n "verify.menu.navigation_snapshot|menu-navigation-field-snapshot|native_action_id|compatibility_used" docs/ops/verify/README.md`：PASS

## 5. 产物
- docs：`docs/ops/verify/README.md`
- docs：`docs/ops/iterations/menu_navigation_verify_docs_batch_20260427.md`

## 6. 回滚
- 方法：回退本批次提交，或删除 README 中新增的 menu navigation field snapshot 说明。
- 数据/升级：无需 `-u`，无需重启。

## 7. 下一批次
- 目标：继续扫描当前 verify summary/gate 是否已经纳入 `menu_navigation_field_snapshot` 结果。
- 前置条件：只更新当前 gate/summary 消费路径，不修改历史归档记录。

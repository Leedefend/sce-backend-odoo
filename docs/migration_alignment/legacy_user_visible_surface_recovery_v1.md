# 历史用户可见面与业务恢复重放说明 v1

## 目标

历史用户恢复不能只停留在列表展示。当前口径要求同时恢复：

- 用户可见面：按用户维护 Excel 的列顺序展示用户名、姓名、手机号、建立时间、所属部门、角色、状态等。
- 真实账号主体：历史用户导入为 `res.users`，启用用户可登录。
- 业务能力：历史角色和用户维护可见面投影到新系统默认业务角色组，能力组只作为角色组背后的平台维护底座。
- 项目范围：历史项目范围事实挂接到用户，并尽可能解析到新系统项目访问。

登录次数和最近登录时间只作为静态备份库的展示字段，不作为业务恢复是否成功的核心验收项。

## 输入资产

- 历史用户资产：`migration_assets/10_master/user/user_master_v1.xml`
- 用户上下文 payload：
  - `artifacts/migration/fresh_db_legacy_user_profile_replay_payload_v1.csv`
  - `artifacts/migration/fresh_db_legacy_user_role_replay_payload_v1.csv`
  - `artifacts/migration/fresh_db_legacy_department_replay_payload_v1.csv`
- 项目范围 payload：
  - `artifacts/migration/fresh_db_legacy_user_project_scope_replay_payload_v1.csv`
- 用户维护可见面 Excel：
  - `artifacts/migration/user_visible_surface/user_maintenance_page1.xlsx`
  - `artifacts/migration/user_visible_surface/user_maintenance_page2.xlsx`

## 重放顺序

在目标库上执行：

```bash
DB_NAME=sc_partner_acceptance make history.users.rebuild
DB_NAME=sc_partner_acceptance make fresh_db.legacy_user_context.replay.write
DB_NAME=sc_partner_acceptance make history.real_users.normalize.write
DB_NAME=sc_partner_acceptance make history.legacy_user_visible_surface.overlay.write
DB_NAME=sc_partner_acceptance make fresh_db.legacy_user_project_scope.replay.write
DB_NAME=sc_partner_acceptance make history.legacy_user_access.projection.write
DB_NAME=sc_partner_acceptance make history.legacy_user_recovery.probe
```

如果用户维护 Excel 不在默认路径，可通过 `LEGACY_USER_VISIBLE_SURFACE_FILES` 指定逗号分隔文件列表。

## 当前验收库结果

`sc_partner_acceptance` 当前探针结果为 `PASS`：

- 用户档案：101 条，101 条已绑定真实用户，66 条启用。
- 历史用户资产：101 个 `migration_assets.legacy_user_sc_*` 外部 ID。
- 历史角色：330 条全部绑定用户，315 条可映射到默认业务角色组。
- 历史用户业务角色：101 个已绑定真实用户的档案中，97 个已投影到默认业务角色组，4 个因无角色/项目事实保持未投影。
- 项目范围：90871 条全部绑定用户，60747 条匹配项目，17453 条当前有效范围已应用项目访问。
- 样例用户 `wutao`、`chenshuai`、`hujun`、`shuiwujingbanren` 均可从档案追溯到真实用户。

## 已知边界

仍有 15 条历史角色没有安全投影，因为角色名不能稳定映射到新系统默认业务角色组；这些事实保留在历史角色模型中，不丢弃。另有 4 个历史用户缺少角色和项目事实，暂不自动赋权。项目范围中未匹配项目的记录也保留原始 `project_legacy_id`，后续应随项目主数据口径继续收敛。

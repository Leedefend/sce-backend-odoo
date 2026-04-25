# 历史用户重建运行手册 v1

## 目标

将仓库内已准备好的真实历史用户资产包 `user_sc_v1` 一键重建到目标数据库。

当前默认资产：

- XML: `migration_assets/10_master/user/user_master_v1.xml`
- Manifest:
  - `migration_assets/manifest/user_asset_manifest_v1.json`
  - `migration_assets/manifest/user_external_id_manifest_v1.json`
  - `migration_assets/manifest/user_validation_manifest_v1.json`

## 一键入口

仅允许通过 Make 入口执行：

```bash
DB_NAME=sc_demo make history.users.rebuild
```

也可单独做资产校验：

```bash
make history.users.verify
```

## 行为

`history.users.rebuild` 会执行：

1. 校验 `user_sc_v1` 资产包 hash / manifest / XML 结构。
2. 将 `user_master_v1.xml` 内联送入 Odoo shell。
3. 幂等创建/更新 `res.users`。
4. 同步 `ir.model.data`：
   - `module = migration_assets`
   - `name = legacy_user_sc_*`
5. 输出最终统计：
   - 总用户数
   - active / inactive 数
   - XMLID 数
   - 样本记录

## 幂等规则

- 优先按 `ir.model.data(module=migration_assets, name=legacy_user_sc_*)` 绑定。
- 若 XMLID 尚不存在，则按 `login=legacy_*` 查找并复用。
- 重复执行会更新现有记录，不会再额外创建一批同 login 用户。

## 边界

- 只处理历史用户主数据。
- 不赋权：
  - `groups_id`
  - `sc_role_profile`
  - `department/post`
- 不导入项目、成员、合同等其他历史资产。
- 禁止在 `prod` 环境执行。

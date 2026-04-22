# 模块初始化与 bootstrap 审计 v1

## 1) 初始化入口

### `smart_construction_core`

- manifest 声明：`pre_init_hook`、`post_init_hook`
- `pre_init_hook`：保护历史税 XMLID（迁移到 legacy module 名称，避免升级清理）
- `post_init_hook`：
  - `ensure_core_taxes`
  - `_archive_default_project_stages`
  - `_ensure_signup_defaults`
  - `_task_sc_state_backfill`

结论：安装期 bootstrap 行为明确，偏“数据自愈 + 默认参数补齐”。

### `smart_core`

- 通过 extension loader 在 `system.init`/intent 注册阶段收集外部模块 contribution。
- 当前已采用 contribution 路径（不再直接写平台 registry）。

结论：平台注册主权已在 loader 层统一。

### `smart_enterprise_base` / bundles

- 通过 `smart_core_extend_system_init` 向 `ext_facts` 注入企业启用与 bundle 信息。
- 仍保留兼容命名钩子，但写入面已收敛到 `ext_facts`。

## 2) bootstrap 风险

1. `post_init_hook` 逻辑较多，若新环境数据量大，初始化窗口可能变长。
2. `system.init` 扩展来源多模块并存，需持续防止“主结构写入越界”。
3. bundle/enterprise 的 `ext_facts` 注入依赖 action/menu xmlid，需与菜单升级同步。

## 3) 审计结论

- 初始化链路存在且可解释。
- 第一优先级仍是运行态 smoke 可达性；在其前不建议扩大 bootstrap 重构范围。


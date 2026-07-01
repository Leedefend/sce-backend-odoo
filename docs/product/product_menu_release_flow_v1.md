# 产品菜单发布流程 v1

本文定义施工产品菜单从变更、验证到日常开发服务器发布的固定流程。目标是让“正式产品菜单”可解释、可重放、可门禁，而不是依赖某次数据库手工调整。

## 发布对象

产品菜单发布只覆盖 P1/P2/P3 中经过确认的菜单事实：

| 对象 | 发布归属 | 事实来源 | 发布要求 |
| --- | --- | --- | --- |
| 正式产品菜单 | P1 行业标准产品 | `smart_construction_core` 菜单 XML、action、产品策略、发布合同 | 必须进入产品菜单蓝图和发布门禁 |
| 系统配置入口 | P0/P1 配置能力 | 配置中心、菜单配置、字段配置、审批配置、权限配置 | 必须保留可恢复路径，不得被低代码彻底隐藏 |
| 用户确认菜单偏好 | P2 用户产品 | `smart_construction_custom` 或客户模块 | 可重放、可审计，不反向污染行业标准 |
| 运行时租户菜单配置 | P3 低代码配置 | 当前租户数据库运行时记录 | 允许存在，但必须分层为 `user_config`，不得并入正式产品 |
| 历史验收/迁移入口 | P4/P2 过渡承载 | 历史验收菜单、内部归档、用户核对入口 | 不得挂在正式产品中心下作为产品能力 |

## 禁止事项

- 不得在日常开发服务器删除或覆盖用户运行时配置来换取门禁通过。
- 不得把无 XMLID、由业务用户创建的租户菜单并入正式产品目录。
- 不得让 `system.init` 对产品菜单做业务搬家、解包、合并、排序等语义后处理。
- 不得只改 `ir.ui.menu` 就宣称前端产品菜单已发布；自定义前端以产品策略和 DeliveryEngine 输出为准。
- 不得把历史承载入口挂在正式产品中心下。

## 变更入口

### 原生菜单变更

适用场景：

- 新增正式业务入口。
- 调整菜单父级、名称、顺序、权限组。
- 归档历史验收入口。

常见文件：

- `addons/smart_construction_core/views/menu_business_taxonomy.xml`
- `addons/smart_construction_core/views/menu_user_acceptance_cleanup.xml`
- `addons/smart_construction_core/views/menu_contract_product_release.xml`
- 各业务模型视图 XML。

### 产品策略变更

适用场景：

- 自定义前端菜单显示名、分组、合并入口发生变化。
- 多个办理入口需要按业务分类合并。
- action 存在但前端发布路径不符合产品语义。

常见文件：

- `addons/smart_construction_core/models/support/product_policy_sync.py`
- `addons/smart_construction_core/data/product_policy_menu_sync.xml`

### 用户配置变更

适用场景：

- 客户确认的菜单偏好、表单偏好、字段显隐需要长期保留。

要求：

- 沉淀到 `smart_construction_custom` 或客户模块。
- 不写回 P1 行业标准菜单。
- 不覆盖 P3 管理员后续显式保存的运行时配置。

## 本地发布门禁

菜单发布前必须先升级相关模块，再运行总门禁：

```bash
make mod.upgrade MODULE=smart_construction_core DB_NAME=sc_demo CODEX_NEED_UPGRADE=1 CODEX_MODULES=smart_construction_core
make verify.product.menu.release.ready DB_NAME=sc_demo
```

正式产品总发布门禁 `verify.product.release.ready` 已固定依赖
`verify.product.menu.release.ready`。因此正式发布不能绕过菜单发布流程；专项菜单变更可以单独先跑
`verify.product.menu.release.ready`，进入总发布时仍会再次纳入总门禁。

`verify.product.menu.release.ready` 固定包含：

- `verify.product.menu.catalog`
- `verify.system_init.menu_boundary.guard`
- `verify.platform.release_policy.runtime`
- `verify.product.surface.clean`

门禁通过标准：

| 指标 | 要求 |
| --- | --- |
| `needs_review_count` | `0` |
| `business_config_legacy_count` | `0` |
| `business_config_legacy_active_count` | `0` |
| `formal_center_inactive_history_count` | `0` |
| `internal_history_business_visible_count` | `0` |
| `ordinary_business_system_config_visible_count` | `0` |
| `runtime_user_menu_without_xmlid_count` | 本地标准库应为 `0`；日常开发服务器允许存在，但必须归入 `user_config` |
| system.init 菜单边界 | PASS，产品菜单语义只由 DeliveryEngine/产品策略负责 |
| 低代码运行时边界 | PASS，`product_release`、`tenant_runtime`、`developer_draft` 来源分明 |

## 生成物

发布门禁会刷新：

- `artifacts/product/product_menu_catalog_runtime_v1.json`
- `docs/product/product_menu_catalog_v1.md`
- `docs/product/product_menu_blueprint_v1.md`

其中 `docs/product/product_menu_blueprint_v1.md` 是回答“正式产品菜单长什么样”的主文档。

## 日常开发服务器发布

日常开发服务器发布必须执行同一套门禁，不能只拉代码或只重启服务。

```bash
ssh root@1.95.85.92 'cd /opt/projects/repos/sce-backend-odoo && git status --short && git pull --ff-only origin main'
ssh root@1.95.85.92 'cd /opt/projects/repos/sce-backend-odoo && make mod.upgrade MODULE=smart_construction_core DB_NAME=sc_demo CODEX_NEED_UPGRADE=1 CODEX_MODULES=smart_construction_core'
ssh root@1.95.85.92 'cd /opt/projects/repos/sce-backend-odoo && make odoo.recreate'
ssh root@1.95.85.92 'cd /opt/projects/repos/sce-backend-odoo && make verify.product.menu.release.ready DB_NAME=sc_demo'
ssh root@1.95.85.92 'cd /opt/projects/repos/sce-backend-odoo && docker compose -p sc-backend-odoo-dev ps && curl -I --max-time 10 http://127.0.0.1:18081/web/login | head -5'
```

服务器门禁可能因为真实租户运行时配置生成与本地不同的菜单文档。处理规则：

- 可以恢复 `docs/product/product_menu_catalog_v1.md` 和 `docs/product/product_menu_blueprint_v1.md` 的服务器工作区漂移。
- 不得删除数据库里的用户运行时菜单。
- `runtime_user_menu_without_xmlid_count > 0` 时，必须确认它们计入 `user_config`，不是 `formal_product`。

恢复生成文档漂移：

```bash
ssh root@1.95.85.92 'cd /opt/projects/repos/sce-backend-odoo && git checkout -- docs/product/product_menu_catalog_v1.md docs/product/product_menu_blueprint_v1.md && git status --short'
```

## 回滚标准

出现以下任一情况，不允许继续发布：

- 正式产品中心下再次出现 inactive 历史残留。
- 业务配置下出现 legacy/history 菜单。
- 配置中心、菜单配置、字段配置等恢复入口不可达。
- system.init 菜单边界门禁失败。
- 日常开发服务器用户运行时菜单被归类为正式产品菜单。
- 服务健康检查失败或登录页非 `200 OK`。

回滚优先级：

1. 回滚本次菜单 XML/产品策略提交。
2. 重新升级模块。
3. 重启服务。
4. 重新执行 `make verify.product.menu.release.ready DB_NAME=sc_demo`。

## 收口判定

菜单发布流程满足以下条件时可收口：

- 本地和日常开发服务器均通过 `verify.product.menu.release.ready`。
- 日常开发服务器健康检查通过。
- 产品菜单蓝图显示正式中心下 inactive 历史残留为 `0`。
- 服务器工作区无非预期代码漂移。
- 用户运行时配置保留在 `user_config` 边界内。

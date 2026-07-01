# 业务列表配置发布边界

## 结论

正式交付给用户使用的业务列表页面，发布时必须已经有业务列表配置基线。这个配置不是用户个人偏好，也不是运行时兜底结果，而是产品、行业模块或客户模块发布出来的正式业务配置。

列表配置的权威承载是：

`ui.business.config.contract.contract_json.view_orchestration.views.tree.columns`

用户在配置工作台里后续调整列表字段时，仍然写回同一个承载，只是形成新的运行时配置版本。也就是说，发布基线配置和管理员后续调整配置是同一条配置链路的两个阶段，不是两套边界。

## 分层关系

| 层级 | 角色 | 来源/承载 | 对正式业务列表字段的权限 |
| --- | --- | --- | --- |
| 产品发布基线配置 | 产品、行业模块、客户模块随发布写入的默认业务配置 | `ui.business.config.contract` published `view_orchestration.views.tree.columns` | 定义初始字段集合和顺序 |
| 管理员配置调整 | 业务配置管理员在配置工作台调整列表字段 | 同一条 `ui.business.config.contract`，新版本发布 | 替换或调整字段集合和顺序 |
| 配置页面审计 | 配置面读取当前有效配置 | `BusinessConfigListSearchAuditHandler.business_config_list_columns` | 只读展示配置事实 |
| 用户办理面 | 用户打开业务列表页面 | `ui.contract.v2.layoutContract.listProfile.columns` | 必须完全消费配置事实 |
| 个人 UI 偏好 | 当前用户局部体验 | `sc.user.view.preference` | 只能影响 UI-only 能力，不能定义业务字段集合和顺序 |
| 运行态建议/原生视图 | 配置草稿来源、开发期建议、技术页面默认 | Odoo native view、`app.view.config`、runtime backend contract | 只能生成发布基线或草稿建议，不能越过已发布配置 |

## 不变量

1. 正式业务列表页面发布后，`ui.business.config.contract` 中必须存在有效的 tree/list 字段配置。
2. 配置页面看到的 `business_config_list_columns` 必须与用户办理面最终 `layoutContract.listProfile.columns` 完全一致，包括顺序。
3. `layoutContract.listProfile.fact_columns`、`preference_policy.must_request_columns` 不能成为另一套字段事实；它们只能服务于取数，不能和用户可见列分叉。
4. legacy visible、native tree tail、contract governance、已有 generated profile、extension hook 都不得在正式配置之后增删改用户可见列。
5. `sc.user.view.preference` 不参与发布基线，不参与管理员业务配置版本，不参与业务字段权威判断。
6. 如果正式业务列表页面缺少发布基线配置，这是发布缺口，应该由覆盖门禁拦截，而不是运行时 fallback 接管。

## 两类审计

### 覆盖审计

`make verify.business_config.coverage`

用于回答：正式业务页面是否已经具备发布基线配置。缺配置属于发布缺口。

### 对齐审计

`make verify.business_config.list_config_boundary`

用于回答：已经发布的列表配置是否被用户办理面精确消费。该门禁只审计 `ui.business.config.contract` 中已发布的 tree/list 配置合同，不扫描无配置 action，也不把 runtime suggested defaults 当业务配置。

显式历史载体字段名不得进入已发布列表配置，包括 `legacy_attachment_ref`、`legacy_line_attachment_ref`、`legacy_attachment_name`、`legacy_attachment_path`、`creator_legacy_user_id`、`legacy_residual_reason`。既有 `p1_visible_*` / `legacy_visible_*` 过渡字段在完全稳定化前仍按技术标签泄漏规则治理：用户可见标签不得暴露技术字段名或 P1 可见字段身份。

## 运行时兜底的边界

允许存在 runtime suggested defaults，但它只能用于：

- 开发期生成初始配置草稿。
- 配置工作台中给管理员提供建议。
- 技术页面或未产品化页面的临时展示。

不允许用于：

- 替代正式业务列表发布基线。
- 在用户办理面覆盖已发布业务配置。
- 让配置面和办理面显示两套字段。

## 术语修正

“有配置时怎样”不是完整边界。正确表述是：

正式业务列表页面发布时必须有业务列表配置基线；管理员后续配置是对这条基线的版本化调整；用户办理面必须始终以当前有效业务配置为唯一字段权威。

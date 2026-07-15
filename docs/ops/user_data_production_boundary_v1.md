# 历史用户与 Demo 数据生产边界 v1

## 结论范围

本报告记录 `USER-PRE-01` 的事实、裁决和可重复操作边界。原日常库
`sc_demo` 始终只读；所有模块升级、账号停用和验证只允许发生在由
`DBA-REC-01` 逻辑恢复得到的 `sc_user_data_rehearsal`。

`DBA-REC-01` 的仓库外证据清单 SHA256 为
`bca6d19a80a25acd53b02b7d88fcf5d03179a43d10bfc7cd59022a88c742104a`。
日常源库业务指纹在一致性快照前后均为
`28cd1ab4d10a8d261497bc429414b119f4647bcb040300185f2cba7bc8e0d1a1`。

## 用户能力职责矩阵

| 能力 | 当前权威实现 | 试点状态 | 试点必需 | 边界 |
| --- | --- | --- | --- | --- |
| 创建用户 | Odoo `res.users` 与运行时用户管理扩展 | 可用 | 是 | 新建必须显式提供初始密码，不再存在共享默认密码 |
| 停用用户 | `res.users.active` | 可用 | 是 | 停用同时推进 token epoch，使既有业务 token 失效 |
| 密码重置 | Odoo 用户管理与审批岗位新增人员向导 | 可用 | 是 | 密码必须由操作人或受控运行时显式提供 |
| 公司分配 | `company_id/company_ids` | 可用 | 是 | 变更推进 token epoch，不复用旧公司上下文 |
| 角色分配 | Odoo `res.groups` / 正式角色与 capability 组 | 可用 | 是 | 禁止根据 login 或 demo alias 自动授予角色 |
| 项目成员关系 | 正式项目成员/项目范围关系 | 可用 | 是 | 本任务不改变历史项目范围 |
| 权限变更审计 | Odoo 写入审计与用户组关系 | 可用 | 是 | 保留历史用户身份及 `create_uid/write_uid` |
| 批量导入 | 历史迁移工具 | 可后置 | 否 | 不作为试点用户日常管理入口 |
| 自定义前端管理 | 运行时用户管理表面 | 基础可用 | 否 | 完整用户管理产品化后置 |

## 恢复副本事实

恢复副本实际规模以运行时盘点为准，而不是早期估计值。Odoo active-context
口径为公司 2、内部用户 113（含停用）、项目 747、合同 12,671、结算 3,416、
付款申请 34,891、付款执行 38,565、付款台账 12,194、附件 608,210。包含
inactive/archive 行的物理业务指纹口径为用户 115、项目 923、合同 12,671、
结算 3,416、付款申请 34,897、付款执行 38,565、付款台账 12,194、附件
609,258。两个口径用途不同，不得互相视为数据漂移。

`smart_construction_demo` 已处于 `uninstalled`，其 XML ID 数量为 0，五个固定
前端验收账号均不存在。仍有 1 个 login 前缀符合 demo 候选规则的历史用户：

| 脱敏 login ref | XML ownership | active | create/write 引用 | followers | 裁决 |
| --- | ---: | ---: | ---: | ---: | --- |
| `ea74a2b526641e95` | 0 | 是 | 43 | 2 | 保留身份、禁止登录、移除业务组，不删除历史审计身份 |

候选账号 dry-run 计划 SHA256 为
`34ceb7566cd54fa810ad0976da4e1bb19d548e87444c28c194927e513b5b436b`。
计划只允许停用 1 个用户，删除 0 个用户。任何集合漂移都会使 apply 失败。

## 角色解析事实与修复

旧 resolver 审计曾发现无权威组用户会落入 `default_owner`，构成权限提升风险。
修改后的隔离副本最终审计覆盖 112 个内部用户：业务配置管理员 13、财务 9、
项目经理 18、项目成员 65、受限用户 7。来源为 explicit group 40、capability
role 65、no authoritative role 7；受限用户中 active 1 个，且没有可用于自动授权的
明确历史角色名称。

无权威组默认 owner 是生产权限提升缺陷。本次移除 login alias 自动授予角色，
并将无权威角色的用户解析为 `restricted/受限用户`。受限用户权威 release 与
delivery navigation 均为空。正式角色仍只由 Odoo 用户组、capability 和产品策略
解析；本任务不猜测、不自动补齐历史用户角色。需要业务负责人确认的历史用户应由
正式管理员显式分组后才能获得业务导航。

## Demo 去除操作契约

只允许通过以下入口执行：

```bash
make verify.user_data.production_boundary
make user_data.demo_impact_report DB_NAME=sc_user_data_rehearsal
make user_data.demo_removal.plan DB_NAME=sc_user_data_rehearsal
make user_data.demo_removal.apply DB_NAME=sc_user_data_rehearsal
make verify.user_data.post_demo_removal DB_NAME=sc_user_data_rehearsal
```

`apply` 默认不可执行，且必须同时满足：

- 数据库精确等于 `sc_user_data_rehearsal`；
- `SC_ENVIRONMENT=user_data_rehearsal`；
- 显式二次确认值；
- 审阅后的 plan SHA256；
- 精确相等的停用/删除 ID 集合；
- 配对备份 manifest 存在且 checksum 匹配。

脚本拒绝 `sc_demo`、`sc_frontend_acceptance`、`postgres` 和空数据库。候选用户
报告只输出技术 ID、计数和不可逆 login 指纹，不输出姓名、login 或联系方式。

## 指纹与允许变化

去 Demo 前后必须比较业务计数、金额摘要、核心关系、附件与 filestore。允许变化
仅限已审阅候选用户的 `active`、密码摘要、用户组、allowed company 和 token epoch。
不允许删除该用户、partner、followers 或任何 `create_uid/write_uid` 历史引用。

历史数据本身存在关系整理债务，例如部分结算缺合同、历史付款申请缺正式结算关系、
部分付款执行缺正式申请关系。这些是源数据既有事实，不是本任务产生的漂移；后续应在
数据连续性与历史对账任务中处理，禁止在用户边界工具中自动修复。

## 隔离应用结果

隔离副本执行结果为：deactivate 1、delete 0、Demo module `uninstalled`、active
demo candidate 0。候选用户保留原 user/partner 身份、2 条 follower 关系及全部
43 条 create/write 审计引用；`active=false`、业务组 45→0、token epoch 0→1。
Odoo 在撤销全部业务组时同步移除了该用户 1 条讨论频道成员关系，这是禁止登录所需的
明确白名单变化，不涉及业务记录或历史审计字段。

应用后完整物理业务集合与源结构指纹逐项一致：公司、用户、项目、合同、结算、付款
申请、付款执行、台账、附件和 followers 的 count 与 ID digest 均未变化；合同、结算、
申请、执行、台账金额摘要未变化；公司关系与项目收藏关系未变化。用户组关系仅从
2,794 减至 2,749，差值精确等于候选用户原 45 个组。filestore 仍为 500 个文件、
10,732,629 bytes，没有新增缺失文件。

最终角色解析不再出现 owner 默认提升。唯一仍 active 且无权威角色的历史内部用户被
明确限制为无业务导航，须由正式管理员确认职责并分配正式组后方可使用；系统不会根据
login 或旧 demo alias 猜测权限。

判定：`USER_DATA_READY_FOR_RC02`。该判定只覆盖用户/Demo 生产边界，不等价于历史
业务关系已完成对账，也不授权修改原 `sc_demo`。

## 试点运维边界

首批试点可以由受控管理员使用 Odoo 后台管理用户。自定义用户管理前端、组织架构、
复杂批量导入、邀请、SSO、MFA、通讯录和通知均不属于本任务。任何新用户必须显式
设置密码、公司和正式角色；停用或降权后必须重新获取 navigation/capability，旧业务
token 不得继续操作。

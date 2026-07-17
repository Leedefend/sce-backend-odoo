# LC-PRO-02 统一变更集、草稿预览与发布闭环

## 基线与范围

- 权威基线：`origin/main@2fedf582ba2bd04e2c9e165c7b328bbc85415a84`
- 开发分支：`feature/low-code-change-set-preview-publish-v1`
- 本分支只处理低代码配置工作台、可逆配置合同及其验收工具；没有修改普通业务 ACL、record rule、角色策略、金额公式、业务状态机或 70 个普通业务导航叶节点。
- `PROD-IMG-01` 继续暂停；本分支完成后不启动后续生产候选任务。

## 前端责任拆分

| 路由组件 | 修改前 | 修改后 | 裁决 |
| --- | ---: | ---: | --- |
| `BusinessConfigSurfaceView.vue` | 1474 行 | 600 行 | 路由、生命周期和控制器装配留在根组件；草稿、发布、作用域、整改、模板分别拆分 |
| `MenuConfigView.vue` | 3718 行 | 1198 行 | 菜单树适配、草稿转换、树编辑、模板和样式分别拆分 |

新增 Vue 文件均未超过 600 行。菜单样式按组件责任拆分为 `style.css`、`table.css` 和 `responsive.css`，没有产生新的千行替代文件。

## 变更集契约与状态机

新增正式模型：

- `ui.business.config.change.set`
- `ui.business.config.change.set.item`
- `ui.business.config.mutation.audit`

状态机为：

```text
draft -> validating -> ready -> publishing -> published
   |          |          |             |
   +----------+--------> failed <------+
   +------------------> discarded
published ----------------------------> superseded（由新回滚批次替代）
```

变更集绑定创建用户、公司、角色、数据库和过期时间。变更项记录配置类型、action/view 作用域、基线版本、基线 payload hash、草稿 payload、差异摘要、风险、校验和发布结果。用户、公司、角色或数据库不匹配均拒绝；过期变更集不能继续预览或发布。

三个新增模型同时配置 owner/company record rule。同组的另一管理员即使绕过工作台、直接使用原生 ORM，也无法搜索到其他创建者的变更集、变更项或写入审计；意图处理器的作用域校验不是唯一隔离层。

### 可逆与高风险操作边界

进入统一变更集的可逆配置：表单、列表、搜索、分析，以及已有菜单的显隐、名称、顺序和父级调整。

继续走独立高风险通道的操作：创建自定义字段、创建原生菜单/action、审批运行规则和步骤、删除或停用结构对象、批量补齐、跨环境整改。统一暂存接口收到这些类型时返回 `HIGH_RISK_OPERATION_REQUIRED`，不会把它们包装成可原子回滚的普通配置。

## 草稿预览与安全打开

预览通过短期、创建者专属的 preview token 将草稿上下文叠加到页面契约解析；token 同时绑定公司、角色和数据库，默认 20 分钟过期。草稿不修改正式 published 合同，不创建正式版本，不进入其他用户的导航或普通运行态缓存。

安全打开和真实预览的浏览器证据均使用后端 mutation audit 记录实际配置模型的 `create/write/unlink`，不再只靠前端函数名或文案判断。结果：

- 打开当前生效页面前后，正式合同、版本、published 状态、payload hash 不变；
- 正式配置 mutation count 和 latest mutation id 不变；
- 草稿预览的正式合同写入数、正式版本写入数和正式配置写入数均为 0；
- 退出预览后恢复正式运行态。

AST 门禁扫描 38 个正式前端文件、40210 个 AST 节点和 140 条导入关系；编辑器直接加入 `publish: true`、预览依赖发布服务两项负向自测均会失败。只有统一发布模块允许进入正式发布通道。

## 原子发布、冲突与回滚

发布前统一校验全部变更项，并要求幂等 `request_id`。后端对变更集行加锁，并按目标获取事务级 advisory lock；每项再次比较正式 payload hash。旧 hash 返回 409 和逐项冲突摘要。

可逆配置在同一数据库 savepoint 内发布。任一项校验、写入或发布后运行态验证失败，整个集合回滚，变更集进入 `failed`，不会留下部分正式发布。成功后权威重读并记录每项 post-publish hash 和 runtime verification 结果。

回滚以已发布变更集为单位，先比较 post-publish hash，冲突时返回 409；成功时生成新的回滚批次并保留历史版本。新建的合同配置回滚为停用，新增菜单策略回滚为删除策略；不会删除自定义字段或原生菜单。

## 历史环境债务裁决

- action 1019/1020 均由 `smart_construction_demo` 提供，只属于 showcase 演示入口，不是正式权威菜单分母。覆盖门禁通过 XML-ID 来源只读识别并从正式交付分母排除，同时在报告中保留 `excluded_showcase_actions`、缺口和来源证据；没有向 `sc_demo` 补 fixture 数据。
- 后端为菜单配置统一输出 `source_kind` 与 `source_label`。正式合同显示“已发布配置”，历史兼容来源显示“历史兼容配置”；前端不再自行翻译 legacy 来源编码，原始来源事实保持不变。

## 验收结果

### LC-PRO 管理员旅程

- LC-J01–LC-J10：PASS，64/64 断言、10/10 旅程、19/19 动作、9/9 截图；console error 与 request failure 均为 0。
- LC-J11：表单、列表、菜单三类修改进入同一个变更集，差异统一展示。
- LC-J12：另一管理员、另一公司、另一角色和普通用户均不能读取或消费草稿；普通用户持有 token 仍被拒绝。
- LC-J13：草稿预览显示变更，正式页面、版本和其他用户运行态保持不变，正式配置写入为 0。
- LC-J14：三类可逆配置一次原子发布，只形成一个发布批次，逐项运行态验证通过。
- LC-J15：包含非法字段时统一校验失败，所有正式配置均不生效。
- LC-J16：两个管理员基于同一 hash 修改，后发布者获得 409 和冲突详情。
- LC-J17：按发布批次回滚，全部可逆配置恢复并生成新回滚批次。
- LC-J18：自定义字段、原生菜单创建和审批规则不能混入普通批量发布。

### 权限、响应式与回归

- 业务配置管理员、平台管理员：授权能力按现有权限事实可用；无配置权限普通用户直达工作台返回 403，且不泄露目录、模型、版本或配置数量。
- 1440、1920、2560、768、390 五种尺寸工作台矩阵通过；axe critical/serious、页面横向溢出、console/pageerror/unhandled rejection 均为 0。
- J02–J13：PASS。J09–J11 共覆盖 72 个响应式/故障恢复场景；required 金额、dirty guard、409、关系链和 My Work 权威重读保持通过。
- 权威导航：finance 42、project member 9、PM 14、owner 5，共 70/70；action 876/menu 606 继续拒绝。
- 低代码 unit 聚合：8 组测试分别为 11、5、6、9、61、17、45、5 项，全部通过。
- 真实 Odoo 事务测试：`business_config_change_set` 7 个方法（模块日志共 9 tests），0 failure、0 error。
- 门禁清单：扫描 31 个文件、12 个组件、30 个 intent、151 个断言；聚合入口负向自测通过。

## 开发环境说明

- 开发库 `sc_demo` 的公司币种已从 USD 修正为 CNY，并完成 `smart_core`、`smart_construction_core`、`smart_construction_custom` 升级；已有会计分录本身均为 CNY，没有进行金额换算。后端已重启且健康检查为 HTTP 200。
- `sc_demo` 仍有一条与本分支无关的历史用户菜单可达性数据漂移：用户吴涛可见组织架构但没有 `hr.employee` 读取权，另有两条结算引用其不可读项目。隔离验收库和 70/70 正式矩阵均通过；本分支没有为消除该环境漂移而修改 ACL 或 record rule。
- 开发 PostgreSQL 目录存在既有 orphan `pg_rewrite` 记录，导致本轮修改前的 `pg_dump` 失败。币种修改使用单事务并在升级后做了运行态验证；该目录健康问题需作为独立运维债务处理。

## 交付状态

- `make ci.local.quick`：PASS。
- 唯一一次完整 `make ci`：PASS，最终阶段为 `v1.1 PR quality gate passed`。
- `git diff --check`、frontend lint、strict typecheck、production build：PASS。
- 双远端推送、PR、远端 quality gate 与 merge SHA 在发布步骤完成后由最终交付报告记录。

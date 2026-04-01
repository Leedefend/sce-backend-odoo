# smart_construction_custom

## 模块定位

`smart_construction_custom` 是一个**面向特定客户交付**的定制层模块。

它的定位不是：

- 行业通用业务事实模块
- 平台内核模块
- 场景编排模块
- 前端渲染模块

它当前更适合作为：

- 客户级角色/权限装配层
- 客户级组织与人员矩阵映射层
- 客户级交付配置入口

一句话：

> 这个模块用于承接“某一家客户如何使用系统”的定制差异，而不是承接“行业通用业务事实是什么”。

---

## 当前模块实际内容

当前模块已落地的内容主要是三类：

### 1. 角色矩阵组

位置：

- `security/role_matrix_groups.xml`

用途：

- 定义客户侧更容易理解的角色组
- 把角色组映射到 `smart_construction_core` 的能力组

示例：

- 项目中心-只读 / 经办 / 审批
- 合同中心-只读 / 经办 / 审批
- 结算中心-只读 / 经办 / 审批
- 付款中心-只读 / 经办 / 审批
- 角色-业主 / 项目经理 / 财务 / 管理层

### 2. 权限装配

位置：

- `security/ir.model.access.csv`

用途：

- 将合同、结算、付款等核心对象的访问权限，挂到角色/能力组上

说明：

- 这部分属于高风险治理域
- 后续调整必须走受控批次，不能在普通低风险迭代里随意改

### 3. 初始化与策略胶水

位置：

- `models/security_policy.py`
- `hooks.py`
- `data/security_policy_actions.xml`
- `data/customer_company_departments.xml`
- `data/customer_posts.xml`
- `data/customer_users.xml`
- `data/customer_user_relations.xml`
- `data/customer_user_authorization.xml`

用途：

- 安装后自动补 implied groups
- 应用角色矩阵
- 给 demo 用户挂角色组

说明：

- 这部分是“交付装配胶水”
- 不属于行业业务事实本身
- 四川保盛客户初始化的 canonical path 已切到安装期数据文件加载
- 四川保盛客户授权矩阵的 canonical path 也应通过安装期数据文件重放
- `sc.security.policy` 里的 customer bootstrap 方法保留为兼容/运维兜底，而不是首选装载路径

---

## 边界职责

本模块后续应遵守下面的职责边界。

### 应该承接的内容

- 客户组织与岗位对应的角色矩阵
- 客户特定的用户分层
- 客户交付期的权限装配规则
- 客户级 bootstrap / 初始化装配
- 客户交付说明文档

### 不应该承接的内容

- 行业通用业务模型
- 行业通用业务事实数据
- 场景编排语义
- 前端页面结构
- 平台内核公共能力

---

## 推荐的内部职责拆分

虽然当前代码量不大，但从设计上建议把这个模块理解成三层，而不是一个混合黑盒：

### A. 客户角色治理

关注：

- 客户有哪些角色
- 每个角色对应哪些能力
- 哪些角色只读 / 经办 / 审批

典型内容：

- `role_matrix_groups.xml`

### B. 客户权限装配

关注：

- 哪些模型对哪些角色开放读写删改

典型内容：

- `ir.model.access.csv`

### C. 客户交付 bootstrap

关注：

- 安装后默认如何装配
- 哪些 demo / 测试用户默认挂哪些组

典型内容：

- `hooks.py`
- `models/security_policy.py`
- `data/security_policy_actions.xml`

---

## 后续交付完善顺序

后面按客户交付链完善时，建议严格按下面顺序推进。

### 第一阶段：企业基础信息

需要你提供：

- 企业名称
- 是否多公司
- 是否存在分子公司 / 事业部
- 企业业务范围

目标：

- 明确这个模块服务的是哪一家企业、哪一层组织

### 第二阶段：组织架构

需要你提供：

- 一级部门
- 二级部门
- 关键业务部门

目标：

- 明确哪些部门参与：
  - 项目
  - 合同
  - 成本
  - 付款
  - 结算

### 第三阶段：人员与岗位矩阵

需要你提供：

- 人员名单
- 岗位
- 所属部门
- 一个用户是否兼多个岗位

目标：

- 明确用户、岗位、部门三者的映射关系

### 第四阶段：角色与权限矩阵

需要你提供：

- 哪些岗位只读
- 哪些岗位经办
- 哪些岗位审批
- 哪些岗位可看驾驶舱 / 报表 / 配置

目标：

- 把客户岗位翻译成系统角色组和能力组

### 第五阶段：菜单与入口

需要你提供：

- 这家客户第一阶段最先使用哪些主流程
- 哪些入口必须先上线
- 哪些入口可以延后

目标：

- 让菜单、首页、预发布入口与客户真实使用路径一致

### 第六阶段：试运行数据

需要你提供：

- 企业
- 部门
- 用户
- 项目
- 合同 / 付款 / 结算样本

目标：

- 支撑可演示、可培训、可验证的最小闭环

---

## 你后续最先提供什么

如果你还没有完整资料，最先给下面三类就够继续推进：

### 最小输入包

- 企业组织架构图
- 人员岗位清单
- 角色权限对应表

只要这三样明确，后续就能继续把这个模块按“客户交付链”往下收口。

---

## 当前约束

本模块当前包含高风险安全域内容：

- `security/**`
- `ir.model.access.csv`
- 安装时权限写入逻辑

因此：

- 普通低风险迭代只允许补文档、治理、输入清单
- 真正的角色/ACL 重构必须走受控高风险批次

---

## 当前推荐口径

今后讨论 `smart_construction_custom` 时，统一按这个口径理解：

> 它是特定客户交付模块，用来承接客户组织、人员、角色、权限和交付 bootstrap，而不是行业通用业务事实模块。

---

## 公司与部门 Bootstrap 规格

下面这部分是后续真正做系统落地时应直接遵守的 bootstrap 规格。

### 1. 公司 bootstrap

当前客户公司：

- `四川保盛建设集团有限公司`

目标：

- 在系统中建立一个明确的企业根节点
- 后续部门、用户、角色装配都挂到这个公司下

推荐导入字段：

- `company_name`
- `company_code`
  - 当前可先留空，后续若客户提供统一简称再补
- `active`
  - 默认 `true`
- `source`
  - 建议标记为 `customer_bootstrap`
- `notes`
  - 可记录“来源于客户组织确认稿”

当前建议主键口径：

- 以 `company_name = 四川保盛建设集团有限公司` 作为自然主键

### 2. 部门 bootstrap

当前确认的正式部门：

- `经营部`
- `工程部`
- `财务部`
- `行政部`
- `成控部`
- `项目部`

推荐导入字段：

- `department_name`
- `department_code`
  - 当前可先留空
- `parent_department`
  - 当前这 6 个先全部挂公司根节点
- `company_name`
- `active`
  - 默认 `true`
- `department_type`
  - 建议预留，当前可先按：
    - `functional`
    - `project`
- `notes`

推荐初始映射：

- `经营部` -> `functional`
- `工程部` -> `functional`
- `财务部` -> `functional`
- `行政部` -> `functional`
- `成控部` -> `functional`
- `项目部` -> `project`

### 3. 项目部特殊规则

`项目部` 在本客户场景下不是普通占位部门，必须按特殊规则处理：

- 它是正式部门
- 允许用户仅属于 `项目部`
- 允许后续扩展为项目侧独立核算或项目侧组织归属
- 后续用户导入时，不应强行把 `项目部 only` 用户归并到其他职能部门

当前已确认的 `项目部 only` 用户存在，因此这个规则必须保留。

### 4. 导入顺序

后续正式实现时，顺序必须固定：

1. 公司
2. 部门
3. 用户基础信息
4. 用户主部门
5. 用户附加部门
6. 岗位属性
7. 系统角色

不要跳过公司/部门直接导用户，否则后续角色装配会反复返工。

### 5. 不应进入公司/部门表的内容

以下内容不能混进公司或部门导入：

- `公司员工`
  - 它只是成员桶，不是部门
- `管理员角色`
- `通用角色`
  - 它们属于系统角色，不属于组织架构
- `董事长 / 总经理 / 财务经理 / 财务助理`
  - 它们属于岗位，不属于部门

### 6. 当前可直接落地的导入草案

#### 公司表

| company_name | active | source |
| --- | --- | --- |
| 四川保盛建设集团有限公司 | true | customer_bootstrap |

#### 部门表

| department_name | parent_department | company_name | department_type | active |
| --- | --- | --- | --- | --- |
| 经营部 | ROOT | 四川保盛建设集团有限公司 | functional | true |
| 工程部 | ROOT | 四川保盛建设集团有限公司 | functional | true |
| 财务部 | ROOT | 四川保盛建设集团有限公司 | functional | true |
| 行政部 | ROOT | 四川保盛建设集团有限公司 | functional | true |
| 成控部 | ROOT | 四川保盛建设集团有限公司 | functional | true |
| 项目部 | ROOT | 四川保盛建设集团有限公司 | project | true |

### 7. 后续实现注意事项

真正进入实现批次时，建议拆成两步：

#### Step A

- 先只做公司与部门的 bootstrap
- 不碰角色与 ACL
- 验证组织树可见、可查、可挂用户

当前仓库已落地第一版手动 bootstrap 入口：

- 模型方法：
  - `sc.security.policy.bootstrap_customer_company_departments()`
- Server Action：
  - `Bootstrap Customer Company and Departments`

当前实现特征：

- 手动触发
- 幂等 upsert
- 仅处理：
  - `res.company.name`
  - `res.company.sc_is_active`
  - `hr.department.name`
  - `hr.department.company_id`
  - `hr.department.parent_id = ROOT`
  - `hr.department.sc_is_active`
- 不自动写入：
  - 岗位
  - 系统角色
  - ACL
  - 用户归属

因此，这一版实现只解决“公司根节点 + 一级部门树”问题，不会把角色与权限治理提前卷进来。

#### Step B

- 再做用户岗位与系统角色装配
- 最后才接权限治理

## 用户 Baseline Import 规格

在公司与部门 bootstrap 已经就位后，下一步用户导入必须按下面的语义执行。

### 1. 当前冻结的用户基线

来源：

- `tmp/用户维护 (1).xlsx`

当前冻结结论：

- workbook 可见行：`200`
- 有效用户：`20`
- 这 `20` 个用户已经被视为当前客户可导入基线

特殊结构同样冻结，不视为异常：

- 多部门用户：`4`
- `项目部 only` 用户：`3`
- 只有岗位/系统角色、无正式部门信号：`2`

### 2. 用户导入字段语义

后续实现时，用户导入至少要支持这些字段：

- `login`
- `display_name`
- `mobile`
- `company_name`
- `primary_department`
- `extra_departments`
- `posts`
- `system_roles`
- `status`
- `notes`

推荐语义：

- `company_name`
  - 固定映射到 `四川保盛建设集团有限公司`
- `primary_department`
  - 用户主归属部门
- `extra_departments`
  - 用户附加归属部门
  - 只用于保留真实多部门结构
- `posts`
  - 企业岗位属性
  - 不是系统角色
- `system_roles`
  - 系统装配角色
  - 不属于企业组织结构

### 3. 主部门与附加部门规则

后续实现时必须区分：

- 主部门
- 附加部门

原因：

- 当前客户已接受真实多部门用户存在
- 如果不拆主附部门，后续用户树、统计口径和角色装配都会混乱

当前规则：

- 单部门用户：
  - 该部门直接写入 `primary_department`
- 多部门用户：
  - 需要保留一个 `primary_department`
  - 剩余部门写入 `extra_departments`
- `项目部 only` 用户：
  - `primary_department = 项目部`
  - 不强行归并到其他职能部门
- role-only 用户：
  - 允许 `primary_department` 为空
  - 后续通过备注或人工治理补足

### 3.1 当前系统实现边界

这里有一个已经确认的实现边界，不能忽略：

- 当前系统用户模型只提供一个正式部门字段：
  - `res.users.sc_department_id`
- 当前仓库里还没有“附加部门”字段或关联表

这意味着：

- `primary_department` 当前可以直接映射进现有系统
- `extra_departments` 当前还不能忠实写入现有用户模型

所以在后续真正进入用户 bootstrap 实现时，必须遵守：

- 可以先实现：
  - 用户基础信息
  - 公司归属
  - 主部门归属
- 不可以假装已经支持：
  - 多部门真实落库
  - 附加部门写入

对于当前已确认的 `4` 个多部门用户，后续要么：

- 先只落主部门并保留治理备注
- 要么单开新的组织能力批次，为附加部门增加正式承载结构

在附加部门能力未补齐前，不允许把多部门用户“清洗”为单部门真相。

### 4. 岗位与系统角色规则

岗位与系统角色不能混用。

岗位层只允许：

- `董事长`
- `总经理`
- `副总经理`
- `项目负责人`
- `临时项目负责人`
- `财务经理`
- `财务助理`

系统角色层只允许：

- `管理员角色`
- `通用角色`

实现要求：

- `posts` 进入用户岗位属性
- `system_roles` 进入角色装配层
- 不能把岗位写成部门
- 不能把系统角色写成岗位

当前冻结的系统角色映射：

- `管理员角色`
  - 映射到 `角色-业务系统管理员`
  - 表示企业业务系统内的最高权限
  - 不 implied `base.group_system`
- `通用角色`
  - 映射到 `角色-业主`
  - 作为企业业务系统内部普通使用者的默认承载路径

### 5. 当前特殊用户保留规则

后续实现必须原样保留下面三类用户，而不是“清洗掉”：

#### 多部门用户：4

- `duanyijun / 段奕俊`
- `chentianyou / 陈天友`
- `jiangyijiao / 江一娇`
- `chenshuai / 陈帅`

#### 项目部 only 用户：3

- `wutao / 吴涛`
- `lidexue / 李德学`
- `hujun / 胡俊`

#### role-only 用户：2

- `admin / admin`
- `shuiwujingbanren / 税务经办人`

这些用户的现状已经被客户确认符合业务实际，所以后续 bootstrap 逻辑必须：

- 保留多部门
- 保留 `项目部 only`
- 允许 role-only 暂时无正式部门

### 6. 推荐导入顺序

用户层正式实现时，顺序建议固定为：

1. 公司
2. 部门
3. 用户基础信息
4. 用户主部门
5. 用户附加部门
6. 用户岗位属性
7. 用户系统角色

不要直接把角色装配和用户创建混成一步。

### 7. 当前实现边界

截至当前仓库版本，`smart_construction_custom` 已实现：

- 公司 bootstrap
- 部门 bootstrap
- 用户 baseline bootstrap（仅主部门）

尚未实现：

- 用户创建/更新
- 附加部门写入
- 岗位属性写入
- 系统角色装配写入

因此，后续下一张实现任务应只聚焦：

- 多部门正式承载结构
- 不提前卷入 ACL 或 record rule

### 8. 当前已落地的用户 bootstrap 入口

当前仓库已落地第二个手动 bootstrap 入口：

- 模型方法：
  - `sc.security.policy.bootstrap_customer_users_primary_departments()`
- Server Action：
  - `Bootstrap Customer Users (Primary Department Only)`

当前实现范围：

- upsert 当前冻结的 `20` 名有效用户
- 写入：
  - `name`
  - `login`
  - `phone`
  - `active`
  - `company_id`
  - `company_ids`
  - `sc_department_id`

当前实现规则：

- 多部门用户按确认后的第一个部门写入主部门
- 附加部门不落库，只进入 `deferred_extra_departments`
- role-only 用户允许不写主部门

这意味着当前用户 bootstrap 已经可以支持：

- 公司归属
- 主部门归属
- 用户基础信息

但仍然不能宣称已经支持：

- 多部门真实承载
- 岗位属性落库
- 系统角色装配落库

这样可以避免一开始就把组织、角色、权限三层混在一起。

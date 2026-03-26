# Sprint 0 模块边界重排方案 v1

- 日期：`2026-03-26`
- 状态：`Approved for Execution Planning`
- 适用范围：`Sprint 0 / 公司 + 组织`

## 一、问题判定

当前 `Sprint 0` 的目标是正确的，但实现归属是错误的。

错误点：
- 将 `res.company / hr.department / role / user enablement` 的实现放入了 `addons/smart_construction_core`

这违反了行业模块边界：
- `smart_construction_core` 是施工行业域模块
- 公司、组织、用户、角色属于企业主数据与启用底座
- 这些能力应由基础模块拥有，行业模块只能消费

结论：
- 当前未提交的 `smart_construction_core` 中公司/组织相关改动，不得作为正式实现继续推进
- Sprint 0 必须先做模块边界回收，再继续实现

## 二、正确模块归属

### 1. 基础模块拥有

建议新增独立基础模块：

`addons/smart_enterprise_base`

负责：
- `res.company` 业务扩展字段
- `hr.department` 业务扩展字段
- 企业启用菜单入口
- 基础启用 contract
- 企业主数据 guard

原因：
- 该能力不应依赖施工行业域
- 后续其他行业线也需要复用
- `smart_construction_bootstrap` 现阶段只承载 fresh db bootstrap，不适合作为长期主数据模块

### 2. 行业模块消费

`addons/smart_construction_core` 只负责：
- 读取 `company_id / department_id / user / role`
- 在项目、任务、支付、结算等业务对象中消费这些主数据
- 校验施工业务动作是否满足主数据前置条件

禁止：
- 在 `smart_construction_core` 内新增公司、组织、角色的真源实现
- 在行业模块内形成第二套公司/组织入口

### 3. 定制模块归属

`addons/smart_construction_custom`

继续负责：
- 角色矩阵映射
- 项目侧能力差异化定制

不负责：
- 企业组织主数据真源

## 三、Sprint 0 正确落地结构

### Layer Target

- `Fact Layer`
- `Contract Layer`
- `Entry Layer`
- `Interaction Layer`
- `Verify Layer`

### Module

- `addons/smart_enterprise_base`
- `scripts/verify`
- `docs`
- `smart_construction_core` 仅允许做消费接线，不允许做真源实现

### Reason

把“公司 + 组织”收口成用户可见的启用闭环，同时保证企业主数据不污染行业模块边界。

## 四、本轮用户可见主题

唯一主题：

`企业启用：先建立公司，再建立组织架构`

## 五、用户路径

1. 管理员登录系统
2. 进入“公司管理”主入口
3. 创建公司
4. 保存成功并看到结果
5. 点击“组织架构”进入下一步
6. 创建一级部门
7. 创建二级部门
8. 返回组织列表查看结果

## 六、双验收标准

### A. 工程验收

- 新基础模块安装/升级通过
- `verify.product.enablement.sprint0` 通过
- 不破坏 `smart_construction_core` 现有链路

### B. 用户验收

必须能由人走通：

`进入 → 创建公司 → 保存 → 打开组织架构 → 创建部门树 → 查看结果`

只过 A 不过 B，视为未完成。

## 七、模块级任务拆分

### Batch 0A：边界回收

- 停止继续向 `smart_construction_core` 写入公司/组织真源实现
- 将当前 WIP 视为废弃草稿
- 在文档中冻结新的模块归属

完成标志：
- 所有人对模块边界有统一口径

### Batch 0B：基础模块建壳

在 `addons/smart_enterprise_base` 建立：
- manifest
- models
- views
- security
- verify 接入

完成标志：
- 公司与组织的实现载体从行业模块切换为基础模块

### Batch 0C：公司闭环

在基础模块内完成：
- `res.company` 扩展字段
- 公司统一入口
- 公司创建/编辑
- 保存后的成功反馈
- “下一步去组织架构”的显式动作

完成标志：
- 用户可从公司页进入组织架构

### Batch 0D：组织闭环

在基础模块内完成：
- `hr.department` 扩展字段
- 部门树入口
- 公司归属约束
- 负责人约束
- 失败提示
- 组织树列表与表单

完成标志：
- 用户能创建至少三级部门结构并立即看到结果

### Batch 0E：契约与验证

在基础模块内完成：
- 最小 enablement contract
- Sprint 0 guard
- 用户路径 smoke

完成标志：
- 系统能同时通过工程验收和用户验收

## 八、明确不做

- 不在 Sprint 0 推进用户设置真源实现
- 不在 Sprint 0 推进角色矩阵重构
- 不在 Sprint 0 推进项目/任务
- 不在 Sprint 0 扩展 evidence / risk / dashboard 深链

## 九、执行顺序

固定顺序：

`边界回收 → 基础模块建壳 → 公司闭环 → 组织闭环 → 契约与验证`

未完成前一段，禁止进入下一段。

## 十、当前执行结论

下一步不应继续补 `smart_construction_core` 里的公司/组织代码。

下一执行动作应为：

`创建 smart_enterprise_base 模块方案并迁移 Sprint 0 实现载体`

# 智能施工企业管理系统 v1.0 发布路线图（Release Plan）

- 版本：`v1.0`
- 目标：发布第一套可部署、可演示、可实际使用的施工企业项目管理系统

## 一、发布目标

### 1）产品名称

**智能施工企业管理系统**

```
Smart Construction Enterprise Management System
```

简称：

```
SCEMS v1.0
```

### 2）产品定位

面向施工企业项目管理核心业务的数字化管理系统。

主要服务对象：

- 项目经理
- 项目经营人员
- 财务协同人员
- 分管领导

核心目标：

```
让施工企业项目管理过程透明化、风险可见化、决策可数据化。
```

## 二、V1 发布范围

V1 必须形成完整业务闭环。

包含业务域：

```
项目管理
合同管理
成本控制
资金管理
任务协同
风险提醒
```

### 1）主导航结构

V1 导航固定为：

```
我的工作
项目台账
项目管理
合同管理
成本控制
资金管理
风险提醒
```

非核心模块：

```
配置中心
数据中心
系统治理
```

不进入主导航。

### 2）核心业务场景

V1 至少交付 4 个核心场景。

#### 场景 1：我的工作

作用：

```
承接用户日常待办与快速入口
```

功能：

```
待办任务
我的项目
快捷入口
风险提醒摘要
```

#### 场景 2：项目台账

作用：

```
管理所有项目
```

功能：

```
项目列表
项目筛选
项目搜索
点击进入项目控制台
```

#### 场景 3：项目驾驶舱

这是整个系统的核心页面。

必须包含 7 个区块：

```
项目基本信息
关键指标
项目进度
合同执行
成本控制
资金情况
风险提醒
```

页面结构：

```
Header
Metrics
Progress
Contract
Cost
Finance
Risk
```

#### 场景 4：业务工作台

包含三个业务域：

```
合同中心
成本控制
资金管理
```

功能：

```
合同执行
预算成本
付款申请
资金流
```

## 三、系统架构结构

系统采用五层结构：

```
领域模型层
服务聚合层
能力层
场景编排层
前端渲染层
```

### 1）领域模型层

基于 Odoo 模型。

核心模型：

```
project.project
construction.contract
project.cost
payment.request
project.task
risk.signal
```

职责：

```
业务数据
状态管理
关系管理
权限控制
```

### 2）服务聚合层

新增服务类：

```
ProjectDashboardService
ContractSummaryService
CostAnalysisService
FinanceSummaryService
RiskDetectService
```

职责：

```
聚合数据
计算指标
检测风险
生成 dashboard 数据
```

### 3）能力层

系统能力抽象：

```
project.dashboard.view
contract.execution.summary
cost.deviation.analysis
finance.payment.summary
risk.alert.detect
task.pending.summary
```

能力用于：

```
场景组合
权限控制
功能复用
```

### 4）场景编排层

核心 Scene：

```
my_work.workspace
projects.ledger
project.management
contracts.workspace
cost.analysis
finance.workspace
risk.center
```

Scene 负责：

```
用户入口
业务上下文
页面结构
能力组合
```

### 5）前端渲染层

前端基于 Vue3。

组件类型：

```
SceneView
DashboardView
RecordList
RecordForm
BlockComponent
```

Block 类型：

```
HeaderBlock
MetricBlock
ProgressBlock
TableBlock
AlertBlock
```

## 四、产品投放策略

采用 Scene Delivery Policy。

产品面：

```
construction_pm_v1
```

投放规则。

主导航：

```
project.management
projects.ledger
my_work.workspace
contracts.workspace
cost.analysis
finance.workspace
risk.center
```

隐藏：

```
config.*
data.*
internal.*
```

## 五、角色权限设计

V1 固定角色：

```
项目经理
项目成员
合同管理人员
财务协同人员
管理层查看
系统管理员
```

权限控制包括：

```
模型访问
记录规则
Block visibility
Capability access
```

## 六、系统验证体系

必须建立验证体系。

验证类型：

```
contract verify
scene route verify
permission verify
smoke test
```

新增 verify：

```
verify.project.dashboard.contract
verify.project.dashboard.route
verify.project.dashboard.permission
verify.portal.navigation
```

## 七、部署体系

部署环境：

```
dev
test
prod
```

必须提供：

```
Docker 部署
数据库初始化
模块安装脚本
升级脚本
回滚方案
```

文档：

```
docs/deploy/deployment_guide_v1.md
```

## 八、演示与验收

### 1）演示脚本

文件：

```
docs/demo/system_demo_v1.md
```

演示流程：

```
登录系统
进入我的工作
查看项目台账
进入项目控制台
查看合同执行
查看成本情况
查看资金情况
查看风险提醒
```

### 2）用户验收清单

文件：

```
docs/releases/user_acceptance_checklist.md
```

检查项：

```
导航正确
项目可进入
控制台正常
合同数据正确
成本数据正确
资金数据正确
风险提醒正确
权限正确
```

## 九、发布阶段计划

整个发布分为 6 个阶段。

### Phase 0：发布范围冻结

输出：

```
release_scope_v1.md
system_asset_inventory.md
release_gap_analysis.md
```

### Phase 1：产品导航收口

任务：

```
实现 Scene Delivery Policy
确定 construction_pm_v1
固定主导航
```

### Phase 2：核心场景闭环

完成：

```
我的工作
项目台账
项目驾驶舱
业务工作台
```

### Phase 3：角色权限体系

完成：

```
ACL
block visibility
角色矩阵
演示数据
```

### Phase 4：前端体验稳定

完成：

```
统一页面框架
统一 block 组件
统一交互规范
```

### Phase 5：验证与部署

完成：

```
verify scripts
deployment guide
demo script
acceptance checklist
```

### Phase 6：试运行与首发

执行：

```
小范围试运行
收集反馈
发布 v1.0
```

## 十、首发成功标准

系统达到以下状态：

```
可部署
可演示
可培训
可实际使用
```

用户可以完成完整业务路径：

```
登录
→ 我的工作
→ 项目台账
→ 项目驾驶舱
→ 查看合同
→ 查看成本
→ 查看资金
→ 识别风险
```

## 十一、下一步立即执行任务

第一轮任务：

```
冻结 V1 发布范围
完成系统资产盘点
输出发布缺口分析
确定 construction_pm_v1 导航
确认核心场景清单
```

第二轮任务：

```
实现 project.management scene
实现 project.dashboard contract
实现 ProjectDashboardService
实现 7 个 dashboard blocks
```

第三轮任务：

```
实现 我的工作
实现 合同中心
实现 资金管理
实现 权限控制
```

## 十二、核心发布原则

系统必须遵循以下原则：

```
需求先进入 Scene
Scene 再组合 Capability
Capability 通过 Contract 暴露
Service 实现业务逻辑
Delivery Policy 控制产品投放
```

一句话总结：

```
需求 → 场景 → 能力 → 契约 → 服务 → 页面 → 发布
```

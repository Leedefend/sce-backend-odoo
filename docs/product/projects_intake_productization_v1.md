# 项目立项页面产品化迭代说明 v1

## 1. 目标
- 将“项目立项”从一次性完整录入，收敛为“最小创建管理对象”。
- 默认以最少字段完成创建，再在项目驾驶舱持续补充业务信息。

## 2. 本轮收口范围
- 立项表单结构重排（必填/可选分层）。
- 创建默认值规范化（经理、阶段、状态）。
- 创建后项目骨架初始化（轻量）。

## 3. 最小创建口径
- 必填：
  - `name`（项目名称）
  - `manager_id`（项目经理）
- 可选：
  - `owner_id`（业主单位）
  - 项目标识与计划字段

## 4. 创建后初始化语义
- 立项成功后由 `ProjectInitializationService` 执行轻量骨架初始化：
  - `project_task_root`：创建“项目根任务（Project Root Task）”（若无任务）。
  - `project_cost_ledger`：`deferred`（按业务事件驱动生成，不做伪造台账）。
  - `project_finance_ledger`：`deferred`（按资金业务事件驱动）。
  - `project_risk_profile`：`derived`（由风险模型/计算视图承载）。

## 5. 兼容性边界
- 不变：
  - 场景 key 与路由协议
  - 核心 ACL / scene governance / delivery policy
  - 项目编码与生命周期主机制
- 变更：
  - 立项页文案与字段分组
  - 创建默认值与初始化服务

## 6. 后续迭代建议
- v1.1：补充“快速创建项目”弹层（仅名称+经理）。【已落地】
- v1.2：创建后统一跳转 `project.management` 并带 `project_id`。
- v1.3：立项模板化（按项目类型预置结构与规则）。

## 7. v1.1 实施结果（本轮）
- 新增向导模型：`project.quick.create.wizard`
- 新增入口动作：`action_project_quick_create_wizard`
- 新增菜单：`快速创建项目`
- 创建后返回：`/s/project.management?project_id=<id>`

## 8. 项目生命周期定义
项目生命周期：

- `draft`
  - 立项创建完成。
- `active`
  - 出现以下任一事件：
    - 创建合同
    - 创建任务
    - 创建成本记录
- `closing`
  - 项目进入收尾阶段。
- `closed`
  - 项目归档。

## 9. 初始化服务触发规则
触发时机：
- `Project.create()`

执行流程：
- `ProjectCreationService`
- `ProjectInitializationService`
- 创建 `root task`

## 10. 初始化数据最小原则
初始化仅创建最小结构：

- 允许：
  - `root task`
- 禁止：
  - 虚假成本
  - 虚假资金
  - 虚假风险

原则：
- 系统不生成伪业务数据。

## 11. v1.2 实施结果（本轮验收）
- `projects.intake` 已形成双入口：
  - 快速创建（最小字段）
  - 标准立项（完整字段）
- 快速创建页面已按 `intake_mode=quick` 收敛为最小可见字段：
  - `name`
  - `manager_id`
  - `owner_id`
- 快速创建主按钮语义已切换为“创建并进入项目驾驶舱”。
- 创建成功后已跳转到：
  - `/s/project.management?project_id=<id>`

## 12. 本轮已知问题记录（暂不处理）
- 现象：在前序前端异常阶段，出现“创建成功但跳转失败”，用户重复点击后产生多条测试项目。
- 事实：`api.data` 返回成功即已落库，异常发生在前端跳转链路。
- 处理策略：本轮仅记录，不做数据清理；后续统一处理：
  - 测试数据清理
  - 快速创建防重复提交护栏

# 五层架构核心边界 v1

## 目标
冻结系统五层边界，确保后续迭代不再偏离“后端编排、前端消费”主路径。

## 五层定义
1. **Business Truth Layer（业务事实层）**
   - 负责：模型、状态机、约束、业务方法、权限事实。
   - 禁止：输出 UI 结构、前端渲染策略。

2. **Native Expression Layer（原生表达层）**
   - 负责：Odoo 原生 form/tree/kanban/search、modifiers、按钮表达。
   - 禁止：角色化产品编排。

3. **Native Parse Layer（原生解析层）**
   - 负责：保真解析原生视图为结构化 native 输出。
   - 禁止：注入角色策略、场景特判、前端展示策略。

4. **Contract Governance Layer（契约治理层）**
   - 负责：统一契约出口、策略裁剪、可追踪映射证据。
   - 禁止：创建业务事实、承担场景产品体验决策。

5. **Scene Orchestration Layer（场景编排层）**
   - 负责：按角色/任务编排页面、区块、动作。
   - 禁止：直接解析 XML、直接读 parser 内部私有结构。

## 前端消费铁律
- 前端直接消费对象是**场景编排结果契约**（例如 `page_orchestration_v1` 及其 action/data schema）。
- `native_view/semantic_page` 是编排输入，不是前端直接决策源。
- 前端不得以 `sceneKey/model` 硬编码决定页面结构。

## 交付链路
`Business Truth -> Native Expression -> Native Parse -> Contract Governance -> Scene Orchestration -> Frontend`

## 禁止项（必须守）
1. 前端按 `sceneKey` 写页面结构分支。
2. 前端按具体 `model` 写产品语义分支（除通用组件能力探测外）。
3. Scene 层直接消费 parser 私有结构。
4. Governance 层回写业务事实。

## 迭代准入
每次前端迭代必须在说明中声明：
- Layer Target: Frontend Layer
- 输入契约：场景编排结果字段
- 禁止新增：scene/model 硬编码分支


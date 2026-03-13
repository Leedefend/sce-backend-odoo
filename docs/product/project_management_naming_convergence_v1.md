# project.management 命名收口说明 v1

## 1. 背景
- 历史阶段中，`project.management` / `project.management.dashboard` 在页面与文档中使用过“项目管理控制台”命名。
- 随着产品表达统一，该场景主叙事已收口为“项目驾驶舱”。

## 2. 本次调整目标
- 主产品名称统一为：`项目驾驶舱`。
- “项目管理控制台”降级为历史旧名，仅用于迁移说明与历史沟通，不再作为主显示标题。

## 3. 协议兼容边界
- 本次仅做命名收口，不做协议迁移。
- 不变项：
  - scene key: `project.management`
  - page key: `project.management.dashboard`
  - 主路由: `/s/project.management`
  - 数据源与 contract 主结构

## 4. 可见层统一范围
- 页面主标题：统一为“项目驾驶舱”。
- 菜单标题：统一为“项目驾驶舱”。
- scene/ui label：统一为“项目驾驶舱”。
- 页面说明文案与演示路径文案：统一为“项目驾驶舱”。
- 侧边导航收敛：`projects.dashboard` 作为历史兼容别名，不在导航中重复展示，仅保留 `project.management` 作为主入口。

## 5. 风险与回滚
- 风险：依赖旧文案断言的自动化脚本可能需同步更新。
- 回滚策略：仅回滚文案资源，不影响协议与路由。

# 我的工作与公司驾驶舱场景页范式 v1

## 范围

当前已进入真实实现打磨的两个非原生场景页是：

- `my_work.workspace`：我的工作
- `dashboard.company`：公司驾驶舱

它们都不是普通模型列表/表单，不能仅靠原生 Odoo view 支撑。

## 场景页类型

### 任务工作台型

代表页面：`my_work.workspace`

用户目标是进入后直接处理事项，而不是先选择模型。页面必须承载：

- 待办聚合
- 分组/筛选/搜索
- 单条进入业务对象
- 批量完成
- 失败重试与重放证据

实现方式：

- 产品入口保留 `/my-work`
- 场景入口补齐 `/s/my_work.workspace`
- 前端页面为 `MyWorkView`
- 后端主数据接口为 `my.work.summary`
- 操作接口为 `my.work.complete` / `my.work.complete_batch`
- 有 `page_orchestration_v1` 时优先走 `PageRenderer`
- 无法满足复杂操作时保留专用交互实现作为 fallback

### 契约仪表盘型

代表页面：`dashboard.company`

用户目标是查看公司级经营态势，并从指标卡进入明细。页面必须承载：

- 公司级指标
- 快捷入口
- 风险/预警列表
- 原生明细入口

实现方式：

- 场景入口为 `/s/dashboard.company`
- 统一进入 `SceneView`
- `SceneView` 识别 `dashboard.company.enter`
- 前端通过 `SceneContractBlockGridView` 请求后端契约
- 后端由 `dashboard.company.enter` 返回 scene contract
- 前端转成 `PageRenderer` 可消费的 `page_orchestration_v1`

## 统一入口规则

所有正在打磨的场景页必须有 scene key，并且至少有一个 `/s/<sceneKey>` 可打开入口。

允许同时保留产品短路径，例如 `/my-work`，但短路径不能成为唯一入口。

当前入口：

- `/my-work` -> `MyWorkView`
- `/s/my_work.workspace` -> `MyWorkView`
- `/s/dashboard.company` -> `SceneView` -> `SceneContractBlockGridView`

## 数据与动作边界

前端可以做：

- 布局编排
- 展示格式化
- 操作状态反馈
- 路由上下文携带

前端不应该做：

- 业务事实计算
- 权限裁剪
- 业务状态推导
- 从页面文案反推出动作目标

动作目标必须来自：

- 后端 contract target
- scene registry
- 菜单树 action/menu 元数据

## 验收清单

每个场景页至少验证：

- 登录后直接打开 scene route。
- 刷新后仍能恢复数据。
- 主要 CTA 能进入下一业务页面。
- loading/error/empty/idle 状态明确。
- 没有重复标题和重复导航。
- 不遮挡、不重叠、可滚动。

## 本轮落地

- 为 `my_work.workspace` 增加 `/s/my_work.workspace` 场景入口。
- 明确 `my_work.workspace` 是任务工作台型，`dashboard.company` 是契约仪表盘型。

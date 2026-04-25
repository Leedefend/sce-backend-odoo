# 导航双轨契约规范 v1

## 1. 目标

本规范用于冻结自定义前端与后端在导航层的职责边界，明确：

- `action/menu` 是否允许继续存在
- `scene` 在当前阶段的定位
- 两者如何衔接
- 前后端各自依赖什么信号做判断
- 哪些混用方式被明确禁止

本规范用于解决当前已经出现的混线问题：

- 旧 `act_window` 菜单被前端改名成 scene 标题
- 带 `scene_key` 的旧 action 菜单被错误跳转到 `/s/:sceneKey`
- 用户无法判断自己打开的是原生动作页还是场景编排页

---

## 2. 核心结论

### 2.1 动作菜单允许存在

`action/menu` 仍然是合法主入口。  
场景化过程不能粗暴替代所有原生菜单。

### 2.2 scene 允许存在，但必须是独立入口

`scene` 是产品编排入口，不等于任意带 `scene_key` 的菜单节点。  
`scene` 只能由明确的 scene contract 节点承载。

### 2.3 当前必须采用双轨制

导航体系在现阶段必须明确分为两条链：

- `action/menu` 轨
- `scene` 轨

两条链可以互相映射，但不得互相伪装。

### 2.4 定稿口径

本项目正式采用以下定稿口径：

- `action = native source of truth`
- `scene = compiled delivery surface`

含义是：

- 原生 action/view 继续作为事实源存在
- scene 由后端从选中的原生 action/view 编译生成
- 前端优先消费 scene 作为用户主入口
- 但 action 轨必须保留，不能被 scene 全量替代

---

## 2.5 什么成立，什么不成立

### 成立

后端把**选中的原生动作视图**加工成场景化输出，作为用户主入口。

### 不成立

后端把**所有原生动作视图**都直接等价替换成 scene。

原因：

- 原生 action 是能力真源
- scene 是产品化编排层，不是 CRUD 最小单元
- 不是每个 action 都值得提升为 scene

---

## 2.6 编译原则

scene 只能来自“被声明为 canonical entry 的 action/menu”，不能无边界扩张。

允许：

- 原生 action/view -> 后端编译 -> scene contract
- scene route -> target -> 回落到 canonical action

不允许：

- 任意 action 因带 `scene_key` 自动升级为 scene
- demo/showcase action 编进 canonical scene
- 用 scene 去反向篡改原生 action 身份

---

## 3. 双轨定义

## 3.1 Action/Menu 轨

语义：

- 打开某个原生 `ir.actions.act_window`
- 打开某个原生 `ir.ui.menu`
- 打开某个原生 record/form/list/kanban

典型路由：

- `/m/:menuId`
- `/a/:actionId`
- `/r/:model/:id`

后端 owner：

- `ui.contract(menu)`
- `ui.contract(action_open)`
- `ui.contract(model)`

事实定位：

- native source of truth

前端 owner：

- 菜单解析器
- `ActionView`
- `ContractFormPage`
- `RecordView`

显示规则：

- 显示原菜单标题
- 显示原 action 标题
- 按原生 contract 渲染 list/form/kanban

禁止：

- 仅因节点带 `scene_key` 就改成 scene 标题
- 仅因节点带 `scene_key` 就改跳 `/s/:sceneKey`

---

## 3.2 Scene 轨

语义：

- 面向产品化编排的用户入口
- 以 `scene_key` 为稳定身份
- 最终可落到 action/menu/record/route

典型路由：

- `/s/:sceneKey`

后端 owner：

- `system.init / app.init`
- scene registry
- scene provider / scene ready contract

事实定位：

- compiled delivery surface

前端 owner：

- `SceneView`
- scene registry consumer

显示规则：

- 显示 scene label
- scene route 只打开 scene 页面
- scene 再由 target 决定最终嵌入 action/form/record

禁止：

- scene 节点伪装成原生菜单叶子
- scene 标题反向覆盖普通 action 菜单标题

---

## 4. Owner Signal（唯一判定信号）

### 4.1 真正的 scene owner signal

只有满足以下任一条件，节点才可被视为 `scene` 入口：

- `meta.scene_source = scene_contract`
- `meta.action_type = scene.contract`

这两项是前后端共同认可的 owner signal。

### 4.2 明确不是 owner signal 的字段

以下字段不能单独作为 scene owner 判定依据：

- `scene_key`
- `sceneKey`
- `meta.scene_key`

原因：

- 它们可能只是兼容映射
- 可能只是 native menu/action 与 scene 的关联线索
- 不能据此改变入口语义

### 4.3 强规则

结论必须定死：

- `scene_key` 不是 owner signal
- `scene_source=scene_contract / action_type=scene.contract` 才是 owner signal

---

## 5. 前后端共同遵守的规则

## 5.1 后端规则

后端必须：

- 为真正的 scene 节点显式输出：
  - `scene_source=scene_contract`
  - 或 `action_type=scene.contract`
- 为 canonical scene 显式保留来源关系：
  - `primary_action`
  - `fallback_strategy`
  - `source_ref`
- 为 action/menu 节点保留原生标题与原生 target
- 不把旧 demo/showcase action 静默并入 canonical scene 主入口

后端禁止：

- 仅通过补 `scene_key` 就把普通菜单升级为 scene 节点
- 让同一个用户侧入口同时既表现为 scene、又表现为旧 act_window
- 把所有 native action 无差别 scene 化

## 5.2 前端规则

前端必须：

- 仅基于 owner signal 决定：
  - 是否显示 scene 标题
  - 是否走 `/s/:sceneKey`
- 普通 action/menu 节点保持原标题、原链路
- `ui.contract` 只负责页面渲染，不负责入口身份判定

前端禁止：

- 看到 `scene_key` 就改标题
- 看到 `scene_key` 就改跳 scene route
- 把同一菜单在不同地方表现成不同入口类型

---

## 6. 当前仓库中的典型案例

## 6.1 canonical 项目列表

canonical 项目列表当前应被视为 `scene` 轨入口：

- `scene_key = projects.list`
- route = `/s/projects.list`
- target 最终应落到 `action_id = 452`

这条链的表头语义来自：

- `ui.contract(action_open=452)`
- `list_profile.columns`
- `list_profile.column_labels`

## 6.2 旧 demo showcase 菜单

当前仓库中仍存在旧 demo 菜单：

- `menu_id = 343`
- `menu_xmlid = smart_construction_demo.menu_sc_project_list_showcase`
- `action_id = 536`
- `action_xmlid = smart_construction_demo.action_sc_project_list_showcase`
- 标题 = `项目列表（演示）`

这条链属于 `action/menu` 轨，不属于 canonical `projects.list` scene。

因此：

- 它不能被前端改名成 `项目列表`
- 它不能被前端强行解释成 `/s/projects.list`
- 它与 `452 / projects.list` 不能继续混线

---

## 7. 路由衔接规则

### 7.1 从菜单进入

如果菜单节点满足 scene owner signal：

- 进入 `/s/:sceneKey`

否则：

- 进入 `/m/:menuId`
- 再由 menu/action 解析进入 `/a/:actionId` 或 record/form

### 7.2 从 scene 进入

scene 进入后：

- `SceneView` 读取 scene target
- target 可落到：
  - action
  - menu
  - record
  - route

但这是 scene 内部编排，不改变 scene 入口身份。

### 7.3 从 action 进入

直接进入 `/a/:actionId` 时：

- 不因 query 或 node 上存在 `scene_key` 而自动改成 scene 页面
- 除非当前入口本身就是 scene owner 节点

---

## 8. 当前阶段的落地要求

### 8.1 允许并存

当前阶段允许：

- 旧 action/menu 继续存在
- 新 scene/canonical 入口继续存在

并且必须明确分工：

- 用户主入口优先使用 scene
- 原生 action/menu 作为事实源与兼容入口保留

### 8.2 不允许混名

不得再出现：

- 旧 action 菜单显示成 scene 标题
- scene 菜单显示成旧 action 标题

### 8.3 不允许混链

不得再出现：

- 点击旧 action 菜单却进入 scene route
- 点击 scene 菜单却进入旧 act_window route

---

## 9. 后续清理策略

清理顺序必须是：

1. 先冻结 owner signal
2. 再审菜单树中哪些节点是 scene_contract
3. 再把 demo/showcase action 从用户主导航中剥离或降级
4. 最后再做页面显示对齐

禁止反过来做：

- 一边改页面表头
- 一边继续改入口语义

---

## 10. 一句话规范

动作菜单与场景入口必须双轨并存、明确信号、严禁混用；  
`scene_key` 只是关联线索，不是入口 owner signal。

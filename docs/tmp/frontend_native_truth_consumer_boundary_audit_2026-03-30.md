# 前端 Native Truth Consumer Boundary 审计（临时）

日期：2026-03-30  
范围：`ActionView` / `ListPage` / `PageToolbar`  
目标：识别前端哪些地方仍在重复推导或自编排已经可由后端 native truths 表达的页面事实，哪些属于正常渲染职责，哪些才是未来 optimization composition 的合法承接点。

## 一、结论摘要

当前前端不是“没消费后端 contract”，而是处于一种混合状态：

- 已消费 backend native truths
- 但仍在前端二次聚合、二次分层、二次命名
- 还保留了少量硬编码页面结构与批量动作

因此下一步前端并不是“全部推倒重写”，而是：

1. 回收对已存在 native truths 的重复推导
2. 保留纯渲染职责
3. 等后端最小 optimization composition contract 出来后，再回收真正的页面层级编排

## 二、审计口径

每个前端行为按三类判定：

- **A. 重复推导 native truth**
  - 应后续回收
- **B. 合法展示层加工**
  - 可保留在前端
- **C. 暂时承担 optimization composition 占位**
  - 不应长期保留，但需要等后端 optimization contract 再回收

## 三、审计对象

### 1. [ActionView.vue](/mnt/e/sc-backend-odoo/frontend/apps/web/src/views/ActionView.vue)

角色现状：

- runtime 汇总层
- scene/action contract consumer
- 同时也承担了不少 list surface 的二次组织

### 2. [ListPage.vue](/mnt/e/sc-backend-odoo/frontend/apps/web/src/pages/ListPage.vue)

角色现状：

- 列表页容器
- header / toolbar / summary / batch bar / table 的页面结构拥有者

### 3. [PageToolbar.vue](/mnt/e/sc-backend-odoo/frontend/apps/web/src/components/page/PageToolbar.vue)

角色现状：

- 工具栏实际页面编排者
- 当前承担最多的前端自编排责任

## 四、逐项审计

### A. 搜索能力与搜索展示

#### A1. `ActionView` 从 `sceneReadyListSurface.searchPanel` 重新生成 `listSearchPanelOptions`

判定：**A. 重复推导 native truth**

依据：

- [ActionView.vue](/mnt/e/sc-backend-odoo/frontend/apps/web/src/views/ActionView.vue)
  - `listSearchPanelOptions`
  - `listSearchPanelCountLabel`
- 后端已有：
  - `search_surface.searchpanel`

问题：

- 前端仍在把 searchpanel rows 再加工成展示 chips
- 还在前端补 `单选/多选` 文案与计数

边界判断：

- 如果后端后续给出稳定 display rows，这部分应回收
- 当前属于重复推导，不应长期保留

#### A2. `ActionView` 对 searchable fields 做 searchpanel 去重

判定：**A. 重复推导 native truth**

依据：

- [ActionView.vue](/mnt/e/sc-backend-odoo/frontend/apps/web/src/views/ActionView.vue)
  - `searchPanelKeys`
  - `searchPanelLabels`
  - searchable-field 去重逻辑

问题：

- 去重规则属于 search composition truth
- 不应由前端自己决定“searchable fields 和 searchpanel 的重叠怎么消解”

结论：

- 后续应由后端决定去重后的展示 truth

#### A3. 搜索框输入、回车、提交行为

判定：**B. 合法展示层加工**

依据：

- [PageToolbar.vue](/mnt/e/sc-backend-odoo/frontend/apps/web/src/components/page/PageToolbar.vue)
  - input state
  - composition event
  - submitSearch

结论：

- 这是纯前端交互职责
- 不属于后端应接管的页面编排

### B. 当前条件区

#### B1. `PageToolbar.activeStateChips`

判定：**C. 暂时承担 optimization composition 占位**

依据：

- [PageToolbar.vue](/mnt/e/sc-backend-odoo/frontend/apps/web/src/components/page/PageToolbar.vue)
  - `activeStateChips`
  - 将 route preset / search / quick / saved / group / sort 聚合成单一区

问题：

- 后端 native truths 已能提供这些条件事实
- 但“当前条件区”是否独立存在、顺序如何、显示哪些项，本质上是 optimization composition

结论：

- 这不是单纯前端越权，也不是纯渲染
- 它是在缺少 optimization contract 时的前端暂代编排
- 后续应由后端 `active_conditions` contract 替代

### C. 快速筛选 / 已保存筛选 / 分组查看 / 分面维度

#### C1. `PageToolbar` 固定分块模板

判定：**C. 暂时承担 optimization composition 占位**

依据：

- [PageToolbar.vue](/mnt/e/sc-backend-odoo/frontend/apps/web/src/components/page/PageToolbar.vue)
  - 固定存在：
    - `推荐筛选`
    - `搜索模式`
    - `可搜索字段`
    - `快速筛选`
    - `已保存筛选`
    - `分组查看`
    - `分面维度`

问题：

- backend native truths 已能提供每类材料
- 但“它们在页面上应分成哪些 section、顺序是什么”当前由前端模板固定

结论：

- 这块是最核心的前端自编排区
- 后续必须收回到后端 `toolbar_sections`

#### C2. 单个 chip 点击触发对应回调

判定：**B. 合法展示层加工**

依据：

- `onApplyContractFilter`
- `onApplySavedFilter`
- `onApplyGroupBy`

结论：

- 这是正常的交互绑定
- 不属于前端越权编排

### D. 排序与显示文案

#### D1. 排序 summary 的中文文案与来源展示

判定：**B. 合法展示层加工，已接近 native truth 消费**

依据：

- 当前后端已给：
  - `list_surface.default_sort.raw`
  - `field`
  - `direction`
  - `display_label`
- 前端展示：
  - subtitle
  - toolbar summary
  - active state

结论：

- 如果前端只是消费 `display_label`，属正常渲染
- 如果还在自行拼字段友好名，则应继续回收

当前状态：

- 这部分已经较接近正确边界

### E. 批量动作区

#### E1. `ListPage` 的 `批量归档 / 批量激活 / 批量删除` 模板

判定：**A/C 复合：前端越权 + optimization 占位**

依据：

- [ListPage.vue](/mnt/e/sc-backend-odoo/frontend/apps/web/src/pages/ListPage.vue)
  - 模板直接写死：
    - `批量归档`
    - `批量激活`
    - `批量删除`
  - `showArchive`
  - `showActivate`
  - `showDelete`

问题：

- 后端现在只给了：
  - `action_surface.batch_capabilities`
- 但前端已经把“页面上要显示哪些 batch actions”决定掉了

结论：

- 这是当前最明确的前端越权点之一
- 后续必须等后端 `batch_actions` contract，再收掉硬编码按钮

#### E2. selection state、选中条数、checkbox 行为

判定：**B. 合法展示层加工**

结论：

- 这些属于列表交互层
- 即使后端给出 batch capabilities，也仍应由前端处理选中状态

### F. 列表视觉与表格布局

#### F1. `ListPage` 的 header / toolbar / summary strip / batch bar / table 固定顺序

判定：**C. 暂时承担 optimization composition 占位**

依据：

- [ListPage.vue](/mnt/e/sc-backend-odoo/frontend/apps/web/src/pages/ListPage.vue)
  - 固定顺序拼接页面结构

问题：

- 原生 truths 可以支撑其中大部分能力
- 但“页面层级顺序”仍是前端自己组织

结论：

- 这是页面结构编排责任
- 后续应部分转移给后端 optimization composition

#### F2. 表格、状态 badge、主副字段展示

判定：**B. 合法展示层加工**

结论：

- 这是前端渲染职责
- 后端不应接管具体 DOM/视觉实现

### G. 详情页 form/detail 消费

#### G1. 详情结构是否仍在前端自推导

判定：**当前已大幅改善，残余较少**

依据：

- 后端已提供 `form_surface`
- 当前详情页主要问题已不在基础结构缺失

结论：

- 详情页当前不是主要前端越权点
- 后续主战场仍在 list toolbar / batch / page hierarchy

## 五、回收优先级

### 第一优先级：必须回收

1. `PageToolbar` 固定 section 模板
2. `ListPage` 硬编码 batch actions
3. `ActionView` 对 search composition 的重复去重和重复分类

### 第二优先级：等待 optimization contract 后回收

1. `当前条件区`
2. `推荐筛选区`
3. `页面 header / toolbar / summary / batch / table` 的固定层级顺序

### 第三优先级：保留在前端

1. 输入框交互
2. 选中状态
3. 点击回调
4. 表格渲染
5. badge/styling

## 六、结论

现在的前端边界问题，不是“前端乱做了所有事情”，而是两种情况混在一起：

1. **确实越权的部分**
   - batch action 按钮硬编码
   - native search/list truth 的前端二次去重与二次分类

2. **暂时占位的 optimization composition**
   - 当前条件区
   - 快速筛选/已保存筛选/分组查看/分面维度的固定分层
   - 页面整体结构顺序

后续正确顺序不是直接删前端，而是：

1. 先定义最小 optimization composition contract
2. 再把前端的占位编排替换掉
3. 同时把明显越权的 native-truth 重复推导直接回收

一句话：

> 前端现在最大的问题不是“没消费 contract”，而是“消费了 contract 之后还在继续组织页面”；  
> 下一步应把“重复 native truth”与“暂代 optimization composition”分开处理。

# App Shell Navigation Contract 与产品化控制规范 v1

## 1. 目的

本规范用于冻结侧边导航（Sidebar Navigation）的架构边界、事实源定义、治理规则与迭代约束，确保后续导航产品化迭代不再偏离五层架构。

适用范围：
- `app.init` 启动契约
- 场景编排层（Shell 级导航编排）
- 行业导航策略（分组/命名/排序/角色入口）
- 前端侧边栏渲染

---

## 2. 核心结论

1. 前端侧边栏唯一消费事实源：`app.init.data.nav`。
2. 导航根事实源不是前端菜单配置，而是：
   - 场景事实（`scenes`）
   - 角色策略（`role_surface`）
   - 交付策略（delivery policy）
   - 行业导航产品策略（group mapping/label/order/visibility）
3. 导航契约属于 **Shell 级场景编排产物**，不属于单页 `scene_contract_v1`。
4. 单页契约允许输出轻量 `nav_ref`，禁止输出全量导航树。

---

## 3. 事实源分层

### 3.1 根事实源（Backend Runtime Inputs）

- `scenes`：可交付场景事实集合
- `role_surface`：角色候选与可见范围
- `delivery_policy`：运行环境与策略过滤
- `industry_nav_policy`：行业分组、命名、排序与入口提升策略

### 3.2 运行时输出事实源（Shell Contract Outputs）

由 `app.init` 输出：
- `nav`
- `nav_meta`
- `default_route`

前端侧边栏只消费上述输出，不自行推导。

---

## 4. 架构边界（Platform vs Industry）

### 4.1 平台层职责（必须）

平台层负责机制，不负责行业语义：
- 导航组装引擎
- 角色裁剪与交付过滤
- Shell 导航契约 shape
- 导航诊断信息与版本治理
- 策略注册与装载机制

### 4.2 行业层职责（必须）

行业层负责内容与策略：
- `scene -> nav_group` 映射
- 分组文案与分组顺序
- 导航入口显隐策略
- 角色主入口提升策略
- 行业导航 policy 版本演进

### 4.3 平台层禁止项（硬约束）

平台层禁止：
1. 硬编码行业分组文案；
2. 硬编码行业分组顺序；
3. 硬编码行业 `scene -> group` 映射；
4. 硬编码行业角色入口优先策略。

---

## 5. 契约边界规则

### 5.1 App Shell Navigation Contract（允许字段）

- `nav`
- `nav_meta`
- `default_route`
- 可选：`role_surface`

### 5.2 Page Scene Contract（允许字段）

- `scene/page/zones/blocks/actions/permissions/record/extensions/diagnostics`
- 可选：`nav_ref`（如 `active_scene_key/active_menu_key`）

### 5.3 Page Scene Contract（禁止字段）

- 禁止塞入全量导航树（`full nav tree`）
- 禁止复写 Shell 导航事实

### 5.4 前端锚定优先级（Sidebar Active Anchor）

前端计算侧边栏 active menu 时，推荐优先级如下：
1. 路由显式 `menu_id`
2. 页面契约 `scene_contract_v1.nav_ref.active_menu_id`
3. 按 `active_scene_key` 在 `app.init.nav` 中反查 menu

该规则用于保证“壳层导航事实”与“页面语义契约”联动一致。

---

## 6. 导航产品化控制模型

导航产品化采用“三段输入，一段输出”：

1. 场景事实输入（what exists）
2. 壳层策略输入（what is allowed）
3. 行业产品策略输入（how to organize）
4. 输出 Shell 导航契约（what frontend renders）

---

## 7. 诊断与可追踪性要求

`nav_meta` 至少应包含：
- `nav_source`
- `nav_policy_source`
- `nav_policy_provider`
- `nav_policy_version`
- `scene_nav_meta`（构建统计）

目标：在运行时可追踪“当前导航由哪套策略生成”。

此外，导航策略必须通过 schema guard，至少校验：
- `group_labels`（`str -> str`）
- `group_order`（`str -> int`）
- `group_aliases`（`str -> str`）

当策略不合法时，系统必须回退平台默认策略，并在 `nav_meta.scene_nav_meta` 中输出 `nav_policy_validation_ok=false` 与问题列表。

---

## 7.1 覆盖率报告要求

平台层应提供导航策略覆盖率报告能力，至少包含：
- provider 总数
- 可用 provider 数
- provider 来源（module/source/provider_key）
- policy version

用于每轮迭代确认“策略注册链路是否可用”。

---

## 8. 当前缺口与补齐顺序

### P0（立即）
- 将平台硬编码分组策略迁移到行业导航 policy 提供器。
- `nav_meta` 补齐 policy 来源字段。

### P1（短期）
- 增加导航策略 schema 校验（group label/order/alias/visibility）。
- 增加导航策略覆盖率报告。

### P2（中期）
- 增加 `nav_ref` 联动规范并接入页面契约。
- 增加 role-specific nav A/B policy 版本治理。

---

## 9. 一句话规范口径

侧边导航是壳层基于场景事实与产品策略生成的入口系统；
前端只消费它，平台只组装它，行业定义它的产品语义。

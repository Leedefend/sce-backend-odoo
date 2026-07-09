# 菜单配置与运行态导航边界 v1

本文件锁定菜单配置、产品发布菜单、低代码覆盖和最终导航之间的职责边界。后续代码、迁移、验收和生产升级必须按本文件判断，不能再用局部 UI 判断替代边界设计。

## 1. 分层职责

| 层级 | 回答的问题 | 权威来源 | 不允许回答的问题 |
| --- | --- | --- | --- |
| 原生菜单事实层 | Odoo 原始菜单、动作、父子关系、权限是什么 | `ir.ui.menu`、`ir.actions.*`、`res.groups` | 产品最终导航、用户配置后是否显示 |
| 产品发布基线层 | 新环境默认交付的产品菜单体系是什么 | 行业模块 XML、产品菜单蓝图、发布迁移、可重放产品策略 | 当前租户即时配置、个人偏好 |
| 低代码配置意图层 | 管理员希望对菜单做什么覆盖 | `ui.business.config.contract.menu_orchestration`，兼容回退 `ui.menu.config.policy` | 当前用户最终是否能看到菜单 |
| 运行态最终导航层 | 当前用户此刻实际看到什么 | 原生菜单事实 + 产品发布基线 + 低代码配置意图 + 权限 + 结构承载规则的最终投影 | 用户配置意图本身、产品发布基线是否被污染 |
| 配置面板展示层 | 管理员如何理解和修改配置 | 配置意图 + 运行态最终导航 + 审计原因 | 直接把 `policy.visible` 当成最终显示结论 |

## 2. 关键定义

### 产品发布基线

产品发布基线是新租户、新环境默认看到的产品菜单体系。它必须可由代码、数据 XML、迁移或发布合同重放。历史数据库里手工试配的低代码状态不能直接成为产品发布基线。

### 配置意图

配置意图表示管理员保存过的覆盖动作，包括：

- `configured_visible`: 管理员是否希望该菜单作为可见菜单入口。
- `custom_label`: 管理员希望显示的名称。
- `target_parent_menu_id`: 管理员希望移动到的上级。
- `sequence_override`: 管理员希望的排序。
- `role_group_ids`: 管理员希望限制的业务角色范围。

配置意图不是最终显示事实。它可以和最终显示状态不同。

### 运行态最终导航

运行态最终导航是前端主导航真正渲染的树。它必须由统一服务计算，不允许前端页面各自猜测。它需要同时考虑：

- 当前用户权限。
- 产品发布菜单。
- 已发布 `menu_orchestration`。
- 兼容 policy。
- 受保护系统配置入口。
- 父级承载规则。

### 父级承载菜单

父级承载菜单是本次错位的核心场景。

如果某个父级菜单自身的配置意图是隐藏，但它下面仍有最终可见子菜单，那么该父级必须在运行态最终导航中保留，用于承载子菜单。此时：

- `configured_visible = false`
- `runtime_visible = true`
- `runtime_visibility_reason = visible_descendant_carrier`
- 配置面板不能显示为“隐藏”
- 配置面板应显示为“显示中 · 承载子菜单”或等价用户文案

`物资与分包` 当前就是这个类型：自身 policy 可为隐藏，但因为下面有可见子菜单，主导航仍显示它。配置面板把它标成“隐藏”就是边界错误。

## 3. 状态模型

菜单配置面板必须拆分两个状态，不得再用一个标签混合表达。

| 字段 | 来源 | UI 用途 |
| --- | --- | --- |
| `configured_visible` | 低代码配置意图 | “显示菜单”开关当前值 |
| `runtime_visible` | 运行态最终导航 | 当前导航状态标签、筛选、统计 |
| `runtime_visibility_reason` | 运行态解释器 | 解释为什么显示或不显示 |
| `config_source` | 低代码配置源 | 显示运行来源：发布合同 / policy 回退 |
| `runtime_path` | 运行态最终导航 | 显示当前所在导航路径 |
| `configured_path` | 配置意图 | 显示保存后希望移动到哪里 |

允许的运行态状态：

| 状态 | 条件 | UI 标签建议 |
| --- | --- | --- |
| `visible_configured` | `configured_visible=true` 且 `runtime_visible=true` | 显示中 |
| `visible_carrier` | `configured_visible=false` 且 `runtime_visible=true` 且存在可见子菜单 | 显示中 · 承载子菜单 |
| `visible_release_navigation_group` | 产品发布导航使用合成分组，且该分组通过后端显式 `config_menu_id/config_ref` 映射到可配置菜单 | 显示中 · 产品导航分组 |
| `visible_protected` | 配置意图隐藏但系统保护要求保留 | 显示中 · 系统保护 |
| `hidden_configured` | `configured_visible=false` 且 `runtime_visible=false` | 已隐藏 |
| `hidden_permission` | 配置可见但当前用户无权限 | 当前用户不可见 |

配置中心边界：

- `配置中心` 是治理分组，可以作为主导航分组显示。
- `配置工作台` 是低代码配置主入口，必须在配置中心下可达。
- `菜单配置` 是低代码菜单恢复入口，必须受保护，避免管理员把配置能力彻底切断。
- `配置中心`、`配置工作台`、`菜单配置` 都是平台治理入口，显示名称和基础位置以产品发布定义为准；历史低代码 policy 即使保存了 `custom_label=配置中心`，运行态 overlay 也不能把 `配置工作台` 改成同名分组，避免形成 `配置中心 / 配置中心` 这类重复菜单。
| `configured_visible_runtime_absent` | 配置可见但最终导航因产品菜单重组、运行态投影或其他非权限原因未包含该菜单 | 当前未进入导航 |
| `candidate` | 无配置意图且不在最终导航 | 候选 |

菜单树筛选中的“已启用/已隐藏”必须基于 `runtime_visible`，不是基于 `configured_visible`。

## 4. 读写边界

### 读路径

菜单配置页加载时必须同时拿到两类数据：

1. 配置目录：可配置菜单集合，包括最终导航菜单、可恢复隐藏菜单、产品范围内候选菜单。
2. 运行态解释：最终导航树里的 menu id、路径、状态原因。

`ui.menu_config.panel.get` 必须直接返回最终运行态导航树 `runtime.tree`。菜单配置页展示树必须以 `runtime.tree` 为唯一导航结构权威；如果响应缺少 `runtime.tree`，前端必须失败关闭并提示契约缺失，禁止回退到 `session.menuTree`、AppShell 已渲染菜单或 `ir.ui.menu` 原生父子树。

配置面板禁止只读 `ui.menu.config.policy.visible` 后直接得出“当前隐藏”。

### 写路径

保存菜单配置只写配置意图：

- 保存 `configured_visible`
- 保存命名、排序、移动、角色范围
- 发布 `menu_orchestration` 版本

保存动作不直接写 `runtime_visible`。运行态显示必须由统一服务重新计算。

### 审计路径

审计结果必须同时输出：

- 配置意图统计：配置多少、显式隐藏多少、改名多少、移动多少。
- 运行态统计：当前最终显示多少、承载显示多少、权限不可见多少、候选多少。
- 错位解释：哪些菜单配置隐藏但运行态显示，原因是什么。

## 5. 前后端职责

后端必须提供统一解释结果。推荐在菜单配置 load/audit 输出中增加：

```json
{
  "runtime": {
    "visible_menu_ids": [295],
    "states": {
      "295": {
        "runtime_visible": true,
        "configured_visible": false,
        "runtime_visibility_reason": "visible_descendant_carrier",
        "runtime_path": "智慧施工管理平台/施工管理/物资与分包"
      }
    }
  }
}
```

### 分组菜单契约

分组菜单必须按 Odoo 原生结构处理，不能让前端靠名称或合成 id 猜测。

- 真实 Odoo 分组菜单：后端必须下发 `config_menu_id`、`config_ref={model:"ir.ui.menu", id}`、`configurable=true`、`node_kind=menu_group`。
- 产品发布合成分组：如果它投影的是一个真实 Odoo 分组菜单，后端必须映射到真实 `config_menu_id/config_ref`；如果不能写回真实菜单，后端必须下发 `configurable=false`、`synthetic=true`、`node_kind=navigation_group`。
- 配置面板只允许按后端 `config_menu_id/config_ref/runtime.states` 展示；禁止按 label、菜单 id 数值区间、AppShell 已渲染节点反推出“可配置/显示/隐藏”。
- 主导航和菜单配置面必须消费同一份后端最终导航事实。前端可以裁剪视图和展示交互，但不能生成新的菜单运行态事实；菜单配置展示树不得使用 session/AppShell 导航作为兼容回退。

工程守卫：

- `scripts/verify/lowcode_config_boundary_guard.py` 会拦截前端重新引入 `AppShell` 反推、label 匹配、合成 id 阈值判断、前端合成 runtime state。
- `scripts/verify/lowcode_config_boundary_guard.py` 会拦截菜单配置展示树回退 `session.menuTree/scopedNavigationTree()`，并要求后端 `panel.get` 输出 `runtime.tree`。
- `verify.business_config.unit` 必须包含该守卫；低代码边界相关改动必须先通过它。

前端只能消费这个解释结果：

- 开关显示 `configured_visible`
- 状态徽标显示 `runtime_visible` + `runtime_visibility_reason`
- 树筛选按 `runtime_visible`
- 统计拆成“配置隐藏”和“当前隐藏”

前端不得自行用 `policy.visible`、菜单名称、父子节点数量猜测最终显示状态。

## 6. 和主导航的关系

主导航必须消费运行态最终导航。菜单配置面板的“当前导航状态”也必须消费同一份运行态最终导航解释。

菜单配置面板的“可配置目录”可以是超集，但必须明确区分：

- 当前导航中显示的菜单
- 被配置隐藏但可恢复的菜单
- 产品候选菜单

因此，“菜单配置目录比主导航多”是允许的；“主导航显示但配置面板标为隐藏”是不允许的。

## 7. 门禁规则

必须新增或强化以下验收：

1. 固定样本：`物资与分包` 若在主导航显示，菜单配置面板不得标为“隐藏”。
2. 父级承载样本：构造父级 `configured_visible=false`、子级 `runtime_visible=true`，断言父级状态为 `visible_carrier`。
3. 系统保护样本：配置中心/菜单配置不能被彻底隐藏或变成不可达。
4. 配置意图统计和运行态统计必须分开，不得用同一个 hidden_count 表达两类含义。
5. 主导航最终树和菜单配置运行态状态必须来自同一后端解释服务。

## 8. 禁止事项

- 禁止把 `policy.visible=false` 直接翻译成“当前隐藏”。
- 禁止前端页面自行推导最终导航显示状态。
- 禁止把父级承载菜单当成普通隐藏菜单。
- 禁止把低代码运行时结果反向污染产品发布基线。
- 禁止只用“菜单配置目录顺序和主导航一致”作为合格标准；还必须验证每个节点的运行态状态一致。

## 9. 收口实施顺序

1. 后端菜单配置 load/audit 输出 `runtime.states`。
2. 前端 MenuConfigView 拆分配置开关和运行态徽标。
3. 更新低代码验收，固定覆盖 `物资与分包`。
4. 更新 full acceptance，把菜单状态一致性纳入强门禁。
5. 再处理生产/日常开发服务器升级。

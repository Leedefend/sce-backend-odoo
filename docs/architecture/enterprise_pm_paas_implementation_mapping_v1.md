# 企业级项目管理 PaaS 实施架构与现状映射 v1

状态：Implementation Baseline / 实施基线  
适用对象：当前仓库迭代、平台级内核重构拆解、模块边界冻结、任务规划

---

## 1. 文档定位

本文档回答的不是“理想平台应该长什么样”，而是：

1. 当前仓库已经有哪些平台资产。
2. 当前资产分别落在什么边界内。
3. 目标架构与当前实现之间还差什么。
4. 后端平台级内核重构应该按什么顺序推进。

目标蓝图见：

- `docs/architecture/enterprise_pm_paas_target_architecture_v1.md`

---

## 2. 当前系统事实

当前仓库不是从零起步的 `paas_*` 新平台，而是基于以下现实演进：

- Odoo 作为业务与数据底座；
- `addons/smart_core` 承载大量平台能力；
- `addons/smart_scene` 承载 scene runtime / orchestrator 能力；
- `addons/smart_construction_core` 等行业模块承载领域与场景；
- `frontend/apps/web` 承载 Portal Shell / SPA 前端；
- `docs/architecture`、`docs/product`、`scripts/verify`、`agent_ops` 已形成治理与验证链。

因此，当前最重要的不是重新命名，而是：

- 清晰识别平台资产；
- 冻结边界；
- 按主链收敛；
- 再决定是否做模块级重组。

---

## 3. Current-to-Target Mapping

### 3.1 当前模块到目标层映射

| 当前资产 | 当前职责 | 目标归属 |
| --- | --- | --- |
| `addons/smart_core` | intent、contract、frontend api、app config engine、delivery/permission 等平台能力 | Platform Kernel Layer |
| `addons/smart_scene` | scene identity、layout orchestration、contract builder、scene engine | Scene & Orchestration Layer |
| `addons/smart_construction_core` | 行业领域模型、行业服务、行业场景承接 | Scenario Product Layer |
| `frontend/apps/web` | shell、route、contract consumption、scene/page 渲染 | Frontend Layer |
| `scripts/verify` | 验证脚本、守卫、smoke、schema guard | Governance & Audit |
| `agent_ops` | 任务合同、风险守卫、报告、队列、连续迭代治理 | Governance & Audit |
| `docs/product/*` | 产品主线、场景定义、交付规范 | Product Governance |
| `docs/architecture/*` | 分层、contract、scene、runtime、freeze、boundary | Architecture Governance |

### 3.2 当前关键运行链

当前实际主链已经接近以下结构：

```text
frontend
  -> intent / frontend api / system init
  -> smart_core contract/runtime
  -> smart_scene orchestrator
  -> scene-ready contract
  -> frontend render
```

但仍存在以下现实问题：

- 部分能力还停留在 UI Base Contract 直接暴露阶段；
- 部分 scene 仍处于 fallback / 预接线状态；
- 平台与行业模块之间仍有能力重复和边界模糊；
- 文档中对终局能力的表述曾明显强于当前事实。

---

## 4. 当前已落地的关键资产

### 4.1 平台层资产

以 `docs/architecture/smart_core_inventory.md` 为基线，`smart_core` 已具备：

- intent / frontend api / contract controllers
- `ui_contract`、`load_contract`、`system_init` 等 handler
- app config engine 与 page assembler
- dashboard / dynamic config / registry 相关资产

这意味着“平台级内核”不是未来才有，而是已经存在，只是需要收敛和去混杂。

### 4.2 Scene 编排资产

以 `docs/architecture/scene_orchestration_kernel_capability_status_round7.md` 为基线，`smart_scene` 已具备：

- scene identity resolver
- structure mapper
- layout orchestrator
- capability injector
- scene contract builder
- scene engine 最小闭环

这说明 Scene Orchestrator 不是概念，而是已经具备最小可跑骨架。

### 4.3 运行时主链方向

以 `docs/architecture/intent_runtime_scene_orchestrator_integration_plan_v1.md` 为基线，系统已经明确：

- UI Base Contract 是中间事实；
- Scene-ready Contract 才是页面现实；
- 后续主链应继续向 `intent -> base contract -> scene orchestrator -> scene-ready contract` 收敛。

### 4.4 治理资产

当前仓库已形成三类治理资产：

- verify / smoke / gate
- docs 中的 boundary / freeze / contract 规范
- `agent_ops` 的任务合同、风险扫描、报告、连续迭代控制平面

这决定了后续重构不能脱离证据链裸奔。

---

## 5. 当前与目标之间的主要差距

### 5.1 命名层已经平台化不够，但这不是第一优先级

当前仍以 `smart_core` / `smart_scene` / `smart_construction_core` 为主命名，不符合理想化 `paas_*` 命名，但命名不是主矛盾。

### 5.2 能力边界仍有混合

当前主要风险在于：

- platform 与 industry 职责有重叠；
- contract runtime 与 scene/runtime 的主次关系未完全统一；
- frontend 在部分场景中仍承担了过多结构容错；
- 文档与实现有时存在“愿景先行，治理滞后”的偏差。

### 5.3 通用产品层还未完全显式化

目标架构中的“通用项目管理应用层”已在产品语义上存在，但在模块和能力归属上仍需要进一步收敛。

---

## 6. 当前阶段的冻结边界

在平台级内核重构开始前，以下边界应视为冻结：

### 6.1 五层边界冻结

- Platform Layer
- Domain Layer
- Scene Layer
- Page Orchestration Layer
- Frontend Layer

禁止跨层补功能来“临时跑通”。

### 6.2 Scene 运行时主链冻结

运行时方向冻结为：

```text
Intent Runtime
  -> UI Base Contract
  -> Scene Orchestrator
  -> Scene-ready Contract
  -> Frontend
```

允许渐进式迁移，不允许回退到“前端自行拼页面真相”。

### 6.3 行业模块边界冻结

行业模块只承接：

- 领域模型
- 行业规则
- 行业场景

禁止继续向行业模块复制：

- intent router
- contract engine
- scene registry
- permission / delivery 平台能力

### 6.4 治理与验证边界冻结

后续重构必须继续经过：

- verify / smoke / gate
- architecture docs
- `agent_ops` 任务合同、风险扫描、报告、停机规则

---

## 7. 对绝对化架构表述的修正

为了让文档真正能指导当前系统，以下表述必须统一修正。

### 7.1 关于统一意图

错误说法：

- 所有前后端交互都应合并成唯一 `/intent/execute`

当前正确说法：

- 业务动作统一通过 intent；
- 读取与运行时装配能力保留受控分层接口；
- 诊断、启动、元数据、场景目录不强行塞入单一动作接口。

### 7.2 关于自动化渲染

错误说法：

- 前端 100% 零硬编码自动渲染

当前正确说法：

- 常规业务页面优先契约/元数据驱动；
- 复杂工作台和特化页面允许受控自定义组件承接；
- 自定义不是默认路径，且必须保留治理出口。

### 7.3 关于 Odoo 原生前端

错误说法：

- 完全禁止任何 Odoo 原生页面存在

当前正确说法：

- 产品主前台默认以自定义前端承接；
- 原生页面可以作为过渡期或复杂场景补充，但不能成为长期主入口战略。

---

## 8. 后端平台级内核重构顺序

### Phase 0：资产冻结与事实盘点

目标：

- 盘清 `smart_core` / `smart_scene` / 行业模块的真实职责；
- 冻结当前主链与边界；
- 固化风险不可触碰范围。

完成标志：

- 本文档和目标架构文档成为统一入口；
- 重复能力和边界模糊点形成 backlog。

### Phase 1：运行时主链收敛

目标：

- 让更多入口稳定走 `intent -> base contract -> scene orchestrator -> scene-ready contract`；
- 清退直接暴露 base contract 的旧路径。

### Phase 2：平台内核职责归位

目标：

- 清理 `smart_core` 中混杂的临时逻辑；
- 将通用 runtime / policy / registry / contract builder 归位；
- 将行业特化逻辑从平台资产中剥离。

### Phase 3：通用项目能力显式化

目标：

- 把“项目管理共性能力”从行业特化中抬出来，形成稳定通用产品层。

### Phase 4：命名与模块重组

目标：

- 只有在前述边界稳定后，再决定是否引入 `paas_*` 模块重组或 package 命名升级。

---

## 9. 未来任务拆解建议

如果要策底重构后端平台级内核，建议优先拆成以下任务类型：

1. `platform_inventory`
   - 盘点平台能力、重复能力、临时桥接能力。
2. `runtime_mainline_convergence`
   - 收敛 intent / contract / scene 主链。
3. `industry_detachment`
   - 把行业逻辑从平台层剥离。
4. `common_project_kernel_extraction`
   - 显式提炼通用项目能力。
5. `governance_guard_extension`
   - 为平台级重构补齐更严格的 verify / guard / audit。

这些任务都应该继续通过 `agent_ops` 任务卡执行，而不是直接启动一轮“大重写”。

---

## 10. 结论

当前仓库离目标 PaaS 平台并不远，真正的问题不是“有没有方向”，而是“有没有把现状和目标之间的桥搭清楚”。

本实施基线的核心判断是：

- 现有系统已经有平台内核雏形；
- Scene Orchestrator 已经是事实资产；
- 前后端契约运行时已经具备主链方向；
- 真正缺的是清晰映射、边界冻结、渐进式重构路径。

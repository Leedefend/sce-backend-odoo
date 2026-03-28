# 企业级项目管理 PaaS 目标架构总纲 v1

状态：Target Architecture / 终局蓝图  
适用对象：架构评审、后端平台内核重构、产品化路线统一、对外技术说明

---

## 1. 文档定位

本文档定义企业级项目管理 PaaS 的目标架构，但不直接替代当前仓库的实施基线。

它回答三类问题：

1. 平台最终要收敛成什么形态。
2. 后端平台级内核应承担哪些稳定职责。
3. 后续重构时哪些方向可以推进，哪些原则不能破坏。

如果需要回答“当前仓库已经具备什么、下一阶段先改哪里、哪些边界必须冻结”，必须同时阅读：

- `docs/architecture/enterprise_pm_paas_implementation_mapping_v1.md`

---

## 2. 核心定位

目标系统不是传统 Odoo 二开集合，而是：

```text
Odoo 作为业务与数据底座
+ 平台级内核统一承载能力
+ Scene/Contract/Intent 运行时收敛交互
+ 行业产品包承载场景差异
+ 前端以契约和场景为主输入进行渲染
```

目标产物是一套可商业化、可复用、可插拔的企业级项目管理 PaaS 平台。

---

## 3. 目标架构原则

### 3.1 意图优先，但不做接口教条主义

统一意图是业务动作的主入口，但不是把所有读取、运行时装配、文件处理、系统诊断全部压成一个端点。

应收敛为：

- 业务动作：统一通过 Intent Runtime 进入。
- 读取型运行时能力：通过受控的 contract / metadata / scene 接口暴露。
- 系统级与诊断型能力：通过专用治理接口或验证脚本暴露。

### 3.2 契约优先于页面实现

前端不应推理业务结构，页面结构必须优先来自后端契约和 scene-ready contract。

### 3.3 元数据驱动为主，受控自定义为辅

常规 list / form / kanban / detail 优先元数据和契约驱动。复杂工作台、强交互页面、行业特化视图允许受控自定义承接，但必须保留退出条件和治理边界。

### 3.4 平台内核收敛，行业能力外挂

平台内核只承载通用能力，行业场景只承载领域差异。行业模块不得重复实现平台内核。

### 3.5 Odoo 作为底座，不作为前端战略

Odoo 提供 ORM、事务、权限基础、模块机制和业务数据承载；产品前台默认以自定义前端和契约消费为主，原生页面仅作为受控补充，不作为长期主入口。

### 3.6 先稳定边界，再推动重构

平台级重构必须基于明确边界、验证门禁、证据链和迁移路径进行，不能直接以“更理想的命名”替代“已运行的现实结构”。

---

## 4. 目标分层

目标采用六层架构，但需要与当前五层模型兼容理解。

```text
【Scenario Product Layer】
行业产品包 / 通用应用 / 可售卖场景包
        ↑ ↓
【Scene & Orchestration Layer】
scene 编排 / page orchestration / layout runtime / action orchestration
        ↑ ↓
【Platform Kernel Layer】
intent runtime / contract runtime / metadata center / event bus / permission / audit
        ↑ ↓
【Gateway & Security Layer】
认证 / 鉴权 / 限流 / 审计 / API policy / tenant context
        ↑ ↓
【Odoo Base Layer】
ORM / 模型 / 事务 / 数据持久化 / 原生模块复用
        ↑ ↓
【Infrastructure Layer】
容器 / PostgreSQL / Redis / 对象存储 / 监控 / 发布基础设施
```

### 4.1 与当前五层模型的对齐

| 目标层 | 当前仓库主语义 |
| --- | --- |
| Scenario Product Layer | Domain Layer 的行业产品面 + 产品化文档层 |
| Scene & Orchestration Layer | Scene Layer + Page Orchestration Layer |
| Platform Kernel Layer | Platform Layer |
| Gateway & Security Layer | Platform Layer 中的 API / auth / permission 子能力 |
| Odoo Base Layer | Odoo models / services / ORM runtime |
| Infrastructure Layer | deploy / db / cache / storage / monitor |

说明：

- 当前五层模型仍是实施期硬边界。
- 六层模型用于描述终局平台化结构和后端内核重构目标。

---

## 5. 平台级内核目标能力

后端平台级内核最终应收敛为六大稳定子系统。

### 5.1 Intent Runtime

职责：

- 统一业务动作入口
- 路由业务 intent
- 承接校验、权限、事务、审计
- 向 scene/runtime 输出可消费结果

不负责：

- 页面布局拼接
- 前端交互状态管理
- 行业场景特化逻辑

### 5.2 Contract Runtime

职责：

- 生成 UI Base Contract
- 输出字段、结构、动作、权限、数据载荷的后端事实
- 为 Scene Orchestrator 提供标准输入

不负责：

- 直接渲染页面
- 在领域层泄漏 UI 拼装逻辑

### 5.3 Scene Orchestrator

职责：

- 将 UI Base Contract 转换为 Scene-ready Contract
- 组装 zone / block / actions / workflow / search surfaces
- 管理 layout 策略、provider 输出和扩展 block 注入

### 5.4 Metadata Center

职责：

- 输出统一 metadata / dict / field semantic / view capability
- 支撑通用页面自动化渲染
- 为前端组件工厂提供稳定 schema

### 5.5 Governance & Audit

职责：

- verify / gate / evidence
- release / freeze / policy guard
- contract shape guard
- 风险扫描与运行时证据链

### 5.6 Platform Shared Services

职责：

- permission engine
- event bus
- delivery engine
- registry / provider registry / policy loader

---

## 6. 前后端交互目标模型

### 6.1 业务动作

建议长期收敛为：

```text
Frontend
  -> Intent Runtime
  -> Domain Service / Model
  -> Contract Runtime
  -> Scene Orchestrator
  -> Scene-ready Contract
  -> Frontend Renderer
```

### 6.2 读取型能力

读取型能力不强行塞入 Intent Runtime，应保留受控接口分层：

- metadata
- dict / semantic
- scene catalog / capability registry
- runtime bootstrap / system init

### 6.3 前端职责

前端只负责：

- 渲染
- 局部交互
- 参数收集
- 调用 intent / contract / metadata / runtime bootstrap

前端不负责：

- 推理业务规则
- 计算业务指标真相
- 生成最终页面结构

---

## 7. 平台产品化结构

目标产品结构建议稳定为三段：

```text
平台内核
  -> 通用项目管理应用
    -> 行业场景产品包
```

### 7.1 平台内核

承载所有跨行业复用能力：

- intent
- contract
- metadata
- scene runtime
- delivery / audit / policy

### 7.2 通用项目管理应用

承载所有项目型企业共性的业务语义：

- project
- task
- stage / milestone
- worklog
- dashboard / cockpit

### 7.3 行业场景包

承载差异化领域模型和交付策略：

- IT 研发
- 工程建造
- 维保
- 外包交付

---

## 8. 对当前重构的直接指导

### 8.1 可以重构的方向

- 平台内核职责归位
- intent / contract / scene runtime 的主链收敛
- 平台与行业模块重复能力去重
- provider registry / policy loader / contract builder 结构清理

### 8.2 不能破坏的边界

- 五层边界不能破坏
- Scene 层不能直接操作 ORM
- Frontend 不能承接业务真相计算
- 行业模块不能复制平台内核
- 核心金融 / ACL / manifest / migration 不能在本轮平台文档重构中被顺手改动

### 8.3 对命名重构的判断

如果后续要引入 `paas_*` 命名，不应先于能力边界重构进行。

优先级应为：

1. 先稳定能力边界。
2. 再稳定运行时主链。
3. 最后再决定模块命名是否迁移。

否则只会得到“名称更平台化、结构仍混杂”的伪重构。

---

## 9. 后端平台级内核重构入口条件

在启动彻底重构前，至少满足以下入口条件：

1. 当前到目标的模块映射已经冻结。
2. 平台内核与行业能力的重复点已盘点。
3. Scene-ready contract 已被确认是运行时主输出方向。
4. verify / gate / evidence 已覆盖主要重构风险。
5. 每批重构都能切成用户可见或运行时可验证的闭环。

---

## 10. 结论

这份文档定义的是平台终局，而不是当前仓库事实。

它的作用不是指导“今天直接重命名所有模块”，而是提供一个稳定判断标准：

- 什么能力必须进平台内核；
- 什么能力应留在场景层；
- 什么能力必须继续保持契约驱动；
- 后端平台级内核重构最终要收敛到什么结构。

# 后端契约收口迭代计划 v1.1.1（可执行版）

## 1. 背景与目标

- 背景：当前意图契约存在“登录负载偏重、启动链路语义不够单一、版本标识混用、能力语义未完全交付化”等问题。
- 总目标：将“混合型意图契约体系”收口为“分层清晰、边界稳定、前端可预测”的产品级契约体系。
- 本文定位：可直接进入批次执行的收口计划。
- 约束声明：本轮以契约收口为主，不主动新增或更改 canonical public intent 名称；`login/auth.login/app.init/bootstrap` 的 canonical/alias 清理仅在 P2 做治理标注，不作为本轮 breaking rename 范围。

## 2. 架构定位（执行前固定）

- `Layer Target`: Backend Intent Contract Layer / Scene Runtime Contract Layer / Product Governance Layer
- `Affected Modules`: `login` / `system.init` / `meta.intent_catalog`（新增）/ capability surface / scene governance metrics
- `Reason`: 降低启动复杂度、统一契约语义、增强交付可审计性。

## 3. 范围边界

### 3.1 In Scope

- 登录契约瘦身与语义化（P0-1）
- `system.init` 角色上下文统一（P0-2）
- 全局契约版本格式统一（P0-3）
- 启动链路唯一化（P0-4）
- `system.init` 分层、`workspace_home` 按需加载（P1-1/P1-2）
- intent 目录独立化、capability 交付标识、`default_route` 语义补全（P1-3/P1-5）
- alias/canonical、治理差异、场景指标统一、首页 block 化（P2）
- 与 `login/system.init` 直接相关的前端 `session store`、启动路由、schema 适配属于本轮范围。

### 3.2 Out of Scope（本轮不做）

- 新业务能力扩展
- 非契约主线的 UI 重构
- 与本目标无关的性能专项优化

## 4. 分层迭代任务清单

## P0（必须先做｜启动链路收口）

### P0 执行顺序（v1.1 建议）

- 默认顺序：`P0-1 -> P0-3 -> P0-2 -> P0-4`
- 顺序切换条件：
  - 若线上主痛点是角色漂移，采用 `P0-1 -> P0-2 -> P0-3 -> P0-4`
  - 若主痛点是契约杂乱和快照不可控，保持 v1.1 默认顺序

### P0-1 login 契约边界统一（瘦身 + 语义化）
- 目标：`login` 聚焦认证与启动指引，不承担系统发现。
- 改动：
  - 默认不返回 `system.intents`（仅 debug 模式返回）。
  - 新增 `bootstrap.next_intent=system.init`、`bootstrap.mode=full`。
  - 返回结构主干收口为 `session/user/entitlement/bootstrap`。
  - `groups` 默认隐藏，debug 模式可见。
- 兼容策略（必须执行）：
  - 兼容窗口：1 个迭代周期。
  - 三态契约模式：`contract_mode=default | compat | debug`
    - `default`：仅返回新结构。
    - `compat`：返回迁移期兼容字段（如顶层 `token`、旧位置信息）。
    - `debug`：附加 `groups/system.intents` 调试信息。
  - 兼容结束条件：
    - 前端 `session/auth/init` 链路全部切新结构。
    - login 契约快照 + restricted smoke 全通过。
    - compat 字段列入下个迭代删除清单。
- 验收：
  - `login` payload 体积下降。
  - 前端登录后仅调用 `system.init`。
  - 默认响应中无 `groups`、无 `system.intents`。
  - 默认返回结构断言：必须包含且仅包含主干结构 `session/user/entitlement/bootstrap/meta`（兼容字段仅在 `compat/debug` 模式出现）。

### P0-2 system.init 角色上下文统一
- 目标：消除 `executive/owner` 混用与上下文漂移。
- 改动：统一 `resolve_role(user)` 输出写入：
  - `role_surface.role_code`
  - `workspace_home.record.hero.role_code`
  - `page_orchestration.context.role_code`
- 角色真源规则（必须执行）：
  - 真源：`role_surface.role_code`
  - 其余位置仅为镜像派生，不允许局部 builder 二次推导 role。
  - 非显式 override 场景，禁止出现第二角色来源。
- 验收：三处 `role_code` 全量一致（含 system-bound 样本）。

### P0-3 契约版本统一（语义化）
- 目标：消除 `v0.1/v1/1.0.0` 混用。
- 改动：
  - 顶层 `meta.contract_version/schema_version` 统一语义化。
  - 子契约（如 `workspace_home`）统一同格式版本号。
- 版本职责分层（必须执行）：
  - `meta.contract_version`：该 intent 对外契约版本。
  - `meta.schema_version`：当前 JSON 结构版本。
  - `sub_contract.contract_version`：嵌套子契约版本。
  - 默认规则：`contract_version == schema_version`；仅在兼容壳存在时允许不同。
- 验收：不存在非语义化版本串。
  - 快照覆盖范围：`login/system.init/ui.contract` 三类主链契约快照中，不存在非语义化版本串。
  - 门禁脚本覆盖：新增/扩展版本职责扫描，检查 `meta.contract_version`、`meta.schema_version`、`sub_contract.contract_version` 的存在性与职责一致性。

### P0-4 启动链路唯一化（前后端约束）
- 目标：固定唯一启动流程 `login -> system.init -> ui.contract(按需)`。
- 改动：
  - login 返回 `bootstrap.next_intent`。
  - system.init 返回可解释 `default_route`。
  - 前端禁止绕过 init 直接拉其他 intent。
- 白名单例外（必须声明）：
  - 仅 dev/test：`session.bootstrap`
  - health/ping 类 intent
  - 已声明为 public/minimal 的只读页面
  - 以上例外不得进入主产品导航链路
- 验收：无“跳过 init”启动路径。

## P1（结构优化｜契约分层与瘦身）

### P1-1 system.init 四区块拆分
- 结构：`session/nav/surface/bootstrap_refs`
- 验收：字段归属清晰、无混杂字段。

### P1-2 workspace_home 改按需加载
- 默认只返回 `workspace_home_ref`。
- `system.init?with=workspace_home` 返回完整结构。
- 验收：默认 init 负载下降，页面结构走 `ui.contract`。
- 依赖约束（与 P1-5 绑定）：
  - 即使不预加载 `workspace_home`，前端仍可仅基于 `default_route` 进入首屏。
  - `default_route` 不得依赖 `workspace_home` 内嵌字段。

### P1-3 intent 目录独立化
- 新增 `meta.intent_catalog`。
- login/init 仅返回最小必要意图或 catalog 引用。
- 验收：login 不返回全量 intents。

### P1-4 capability 交付真实性增强
- 新增：`delivery_level/target_scene_key/entry_kind`。
- 验收：可区分独立能力与借用能力。

### P1-5 default_route 语义补全
- 结构含：`scene_key/route/reason`。
- 验收：前端不再推导 menu->scene。

## P2（治理增强｜长期演进能力）

### P2-1 intent canonical/alias 体系
- 验收：每个 intent 可追溯 canonical 归属。

### P2-2 surface_mapping 差异可证明
- 输出 before/after/removed。
- 验收：治理差异不再恒为 0。

### P2-3 scene 指标口径统一
- 统一字段：
  - `scene_registry_count`
  - `scene_deliverable_count`
  - `scene_navigable_count`
  - `scene_excluded_count`

### P2-4 首页 block 化
- 前端只消费 blocks 渲染。
- 验收：去除 hero/metrics/risk/ops 页面特例字段依赖。

## 5. 里程碑与节奏

- Week 1：P0-1/P0-3/P0-2（止血）
  - Exit：login 新结构可用、版本扫描 PASS、role 一致性 guard PASS。
- Week 2：P0-4/P1-1/P1-2（降复杂度）
  - Exit：启动主链唯一化、默认 init payload 下降且首屏不依赖 workspace_home 预加载。
- Week 3：P1-3/P1-4/P1-5（产品化）
  - Exit：intent catalog 可用、capability 真实性字段进契约快照、default_route 完整语义可消费。
- Week 4+：P2（平台化）
  - Exit：alias/canonical、治理差异、场景指标、首页 block 化进入持续门禁。

## 6. 执行依赖与风险

### 依赖
- 前端 session store 与启动路由需配套适配。
- 现有 smoke/guard 脚本需补充新契约字段断言。

### 风险
- 历史消费者可能依赖 `login.system.intents` 或 `user.groups`。
- strict 环境在受限 runner 上可能出现 live-fetch 失败噪音。

### 缓解
- 提供短周期兼容字段（带弃用说明）与开关。
- 在 CI 中区分“环境阻断”与“契约阻断”。

## 7. 验收矩阵（交付门禁）

- 功能门禁：P0 任务逐项达到验收标准。
- 契约门禁：
  - `login` 契约快照通过
  - `system.init` 角色一致性 guard 通过
  - 契约版本一致性 guard 通过
- 主线门禁：`verify.product.delivery.mainline` 保持 PASS（restricted），strict 在 live runner 复核。
- 兼容性门禁（新增，必须通过）：
  - 旧前端在 `compat` 模式可完成登录与启动。
  - 新前端在 `default` 模式仅消费新结构。
  - `debug` 模式仅用于调试，不进入产品主链。
  - compat 模式具备弃用提示和关闭开关。

## 8. 实施方式（审核后执行）

- 执行批次建议：
  1. Batch-A：P0-1 + 登录契约测试
  2. Batch-B：P0-3 + 版本一致性扫描
  3. Batch-C：P0-2 + 角色一致性 guard
  4. Batch-D：P0-4 + 前端启动链强约束
- 每个批次输出：
  - 代码改动
  - system-bound 验证结果
  - 文档与上下文日志更新

## 9. 审阅确认项（请确认）

- 是否同意按“P0-1 → P0-3 → P0-2 → P0-4”顺序执行（若角色漂移优先，可切回 P0-2 在前）。
- 是否允许 P0-1 保留短期兼容字段（例如顶层 token）用于平滑迁移。
- 是否要求在 P0 阶段同步更新前端 schema 与 session store（建议：是）。
- 是否确认采用“兼容窗口 + 默认新结构 + debug 附加信息”的三态策略，而非一次性硬切。

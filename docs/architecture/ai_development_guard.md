# AI开发守则 / Architecture Guard v1.0

适用范围：
- `SmartOdooPlatform`
- `Smart Construction Platform`

目标：
- 在 AI 辅助开发（Codex/LLM）下，保证架构演进可控，避免跨层污染与核心能力破坏。

## 一、核心原则

系统固定为五层：
- Platform Layer
- Domain Layer
- Scene Layer
- Page Orchestration Layer
- Frontend Layer

总原则：
- 功能可以扩展
- 架构不能破坏

## 二、AI开发基本规则

### 规则0：前端页面必须遵守原生视图复用规范

涉及前端页面、页面契约、视图渲染相关改动时，必须同时遵守：
- `docs/architecture/native_view_reuse_frontend_spec_v1.md`
- `docs/architecture/native_view_reuse_frontend_spec_v1.en.md`

硬约束：
- 页面基础结构优先复用 Odoo 原生视图
- 结构问题优先补后端语义解析，不先写前端特判
- 前端以语义契约为唯一结构输入
- 页面特例必须有准入理由与退出条件
- 同时必须遵守五层核心边界：`docs/architecture/five_layer_core_boundary_v1.md`

### 规则1：先做架构定位
任何改动前必须声明：
- `Layer Target`
- `Module`
- `Reason`

若无法确定层级，禁止开发。

### 规则2：禁止跨层实现功能
禁止：
- Frontend 直接访问 ORM
- Scene Layer 操作数据库
- Page Layer 实现业务逻辑
- Domain Layer 返回 UI 结构

正确调用链：
- Frontend -> Scene API -> Domain Service -> Model

### 规则3：平台能力必须进入 Platform Layer
以下能力统一归入 `addons/smart_core`：
- Intent Router
- Contract Engine
- Dashboard Builder
- Workflow Engine
- AI Engine
- Search Engine

行业模块禁止重复实现平台能力。

### 规则4：行业模块只负责业务领域
行业模块允许：
- 业务模型
- 业务规则
- 业务服务

行业模块禁止：
- 返回 UI 结构
- 定义页面布局
- 实现渲染逻辑

### 规则5：Scene 层只负责能力编排
Scene 层职责：
- 组织能力
- 定义入口
- 绑定页面

Scene 层禁止：
- 操作 ORM
- 写 SQL
- 实现业务规则

### 规则6：Page Orchestration 只描述结构
Page 层只负责：
- `scene/page/zone/block` 结构描述

Page 层禁止：
- 查询数据库
- 执行业务逻辑

### 规则7：Frontend 只负责渲染
前端职责：
- UI 渲染
- 交互
- API 调用

前端禁止：
- 实现业务逻辑
- 计算业务指标
- 直接访问数据库接口

## 三、AI提交前必填信息

每次改动需在提交说明/PR 中包含：
- `Layer Target`
- `Affected Modules`
- `Reason`

## 四、禁止 AI 自动修改的核心模块

以下目录默认禁止 AI 自动改动，需人工确认：
- `addons/smart_core/intent_router`
- `addons/smart_core/contract_engine`
- `addons/smart_core/api_gateway`
- `addons/smart_core/permission_engine`
- `addons/smart_core/scene_registry`

## 五、PR 审核规则

PR 描述必须包含：
- `Architecture Impact`
- `Layer Target`
- `Affected Modules`

缺失任一项，不允许合并。

## 六、自动架构检查（建议实施）

建议在 CI 增加规则：
- Scene Layer 禁止引用 ORM 基类
- Page Layer 禁止导入业务服务
- Frontend 禁止出现直接数据库接口访问（如 `/odoo/jsonrpc`）

## 七、AI任务提示模板

建议统一任务输入格式：

```text
Task: <任务描述>
Layer Target: <目标层>
Module: <模块>
Reason: <原因>
Constraints:
- 不允许修改 Platform Layer（如适用）
- 不允许返回 UI 结构（如适用）
```

## 八、架构违规处理

以下行为视为架构破坏，必须立即修复：
- 跨层调用
- UI 逻辑进入领域层
- 数据库访问进入 Scene 层
- 业务逻辑进入前端

## 九、最终架构原则

- 架构稳定 > 功能增加
- 模块清晰 > 实现速度
- 长期可扩展 > 短期便利

## 十、最终目标

通过该守则保障系统持续具备：
- 多行业扩展能力
- 动态页面能力
- AI 能力接入能力
- 平台化能力

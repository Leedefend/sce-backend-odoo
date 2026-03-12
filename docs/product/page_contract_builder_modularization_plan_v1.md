# Page Contract Builder 模块化拆分计划（V1）

## 背景

当前 `addons/smart_core/core/page_contracts_builder.py` 已承载多类职责（页面文案、section 结构、语义规则、模式推断等）。
为避免持续膨胀，本计划定义“先稳态、后拆分”的低风险路线。

## 总体目标

- 将“页面内容定义”与“组装调度逻辑”解耦。
- 保持现有 contract 输出结构兼容，不做一次性重构。
- 支持后续页面按模块增量回收，降低冲突与维护成本。

## 拆分范围（第一阶段）

- 拆分页面默认 contract 定义（`texts`/`sections`/`page_mode` 默认值）。
- 保留 builder 作为统一入口，只负责合并与兜底。
- 不触碰 scene registry / ACL / 认证 / 发布脚本主链路。

## 目标结构（建议）

```text
addons/smart_core/core/page_contracts/
  __init__.py
  login_contract.py
  project_management_contract.py
  projects_list_contract.py
  risk_center_contract.py
  registry.py
```

## 职责划分

- `*_contract.py`：页面级默认语义定义（文本、sections、模式、可选 hint）。
- `registry.py`：注册并暴露页面 contract 生成器映射。
- `page_contracts_builder.py`：
  - 读取 registry。
  - 合并 runtime context 与 fallback。
  - 维持旧接口与旧字段兼容。

## 渐进迁移步骤

1. 先抽取 `login` 到 `login_contract.py`（风险最低，体量小）。
2. builder 增加 registry 加载逻辑（保留旧内联定义作为 fallback）。
3. 对 `project.management`、`projects.list` 做第二批抽取。
4. 完成迁移后删除重复内联定义。

## 兼容性约束

- 不改变 `build_page_contracts()` 对外调用方式。
- 不改变既有 `schema_version` 和基础 envelope。
- 回归覆盖至少包含：
  - `make verify.frontend.build`
  - `make verify.frontend.typecheck.strict`
  - 与页面契约相关的现有 verify 链路。

## 风险与缓解

- 风险：迁移时 key 漏同步导致前端 fallback 回退。
  - 缓解：每页迁移后做 key 对照表与 smoke 校验。
- 风险：并行迭代导致 builder 与模块定义重复。
  - 缓解：规定“新页面仅新增到模块文件，不再扩展内联定义”。

## 本轮不做

- 不做一次性全页面拆分。
- 不调整核心契约协议层与运行态治理机制。

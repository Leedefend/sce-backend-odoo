# 场景编排输出验证清单 v1

## 1. 目的与范围

本清单用于判定后端“场景编排层输出”是否达到前端可直接消费标准。

判定依据：

- `docs/architecture/scene_orchestration_layer_design_v1.md`
- `docs/architecture/scene_contract_spec_v1.md`

适用范围：

- Scene Orchestration Layer（后端编排输出）
- 不包含前端视觉验收

---

## 2. 验证前置条件

- 当前分支为特性分支（非 `main/release`）。
- 使用 `dev/test` 环境执行。
- 本轮改动已完成并可生成契约输出。

---

## 3. P0 必过项（阻塞门禁）

### 3.1 主协议达标

命令：

```bash
make verify.page_orchestration.target_completion.guard
```

通过标准：

- `page_orchestration_v1` 作为主协议存在。
- `page_orchestration` 仅作为 legacy 兼容。

### 3.2 工作台编排结构达标

命令：

```bash
make verify.workspace_home.orchestration_schema.guard
```

通过标准：

- zone/block schema 合法。
- 异构角色（pm/finance/owner）优先级排序差异成立。
- `entry_grid` 等 block payload 不含非法字段。

### 3.3 页面编排契约 schema 达标

命令：

```bash
make verify.page_contract.orchestration_schema.guard
```

通过标准：

- 页面编排输出字段结构符合统一 schema。

### 3.4 动作语义达标

命令：

```bash
make verify.page_contract.action_schema_semantics.guard
```

通过标准：

- action 字段完整且可解释（intent/label/状态语义）。

### 3.5 数据源语义达标

命令：

```bash
make verify.page_contract.data_source_semantics.guard
```

通过标准：

- data source 语义完整且无未定义来源。

---

## 4. P1 强制项（生态一致性）

### 4.1 Scene 契约与语义一致性

命令：

```bash
make verify.scene.schema
make verify.scene.contract.semantic.v2.guard
```

通过标准：

- scene 定义、目录、契约 shape 一致。
- 语义 guard 无退化。

### 4.2 运行面板契约一致性

命令：

```bash
make verify.runtime.surface.dashboard.schema.guard
```

通过标准：

- runtime surface 报表结构符合 schema。

---

## 5. Scene Contract v1 结构抽检

抽检对象：

- `workspace.home`
- `project.management`
- 至少 1 个 list scene

抽检项（必须全部成立）：

1. 顶层字段存在：
   - `contract_version`
   - `scene/page/zones/blocks/actions/permissions/record/extensions/diagnostics`
2. `zones[].block_keys` 全部能在 `blocks` 中解析到。
3. `actions` 必含五类分组：
   - `primary/secondary/contextual/danger/recommended`
4. `permissions` 提供完整 verdict：
   - `can_read/can_edit/can_create/can_delete`
5. 未出现模型特判型前端依赖字段（后端泄漏 UI 特定实现）。

---

## 6. 前端“不得猜测”校验

判定问题（任一为“是”则不达标）：

- 前端是否仍需按模型名判断区块顺序？
- 前端是否仍需自行判定主次动作？
- 前端是否仍需猜测 zone 启用状态？
- 前端是否仍需拼接 scene 语义？

结论规则：

- 全部“否”才可进入前端体系迭代。

---

## 7. 达标等级

### Level A（可进入前端迭代）

- P0 全绿
- P1 全绿
- 抽检全绿
- 前端不得猜测校验全绿

### Level B（可继续后端补齐）

- P0 全绿
- P1 或抽检存在非阻塞缺口

### Level C（禁止切前端）

- 任意 P0 失败

---

## 8. 输出物要求

每轮验证必须输出：

1. 执行命令与结果清单
2. 失败项与根因
3. 修复项与文件路径
4. 回归结果
5. 最终等级（A/B/C）

建议报告路径：

- `docs/ops/audits/scene_orchestration_output_validation_report_<date>.md`

---

## 9. 一句话判定口径

只有当场景编排输出能稳定满足 `Scene Contract v1`，且前端不再承担场景语义猜测责任，才允许进入前端体系化迭代。


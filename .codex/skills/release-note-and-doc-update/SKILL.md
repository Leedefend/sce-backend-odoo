---
name: release-note-and-doc-update
description: 每个批次完成后同步文档、快照、阶段说明，避免代码与文档脱节。
metadata:
  short-description: 发布说明与文档同步（执行强化版）
---

# Release Note And Doc Update

## Use When
- 每个 Batch 完成（必须执行）
- 阶段收口（Phase / Milestone）
- contract / schema / 启动链 / 路由发生变化

---

## Update Order（强制顺序）

1. 先冻结本批次结果（代码 + snapshot）
2. 再更新文档（release note / iteration）
3. 最后记录验证产物路径

👉 未完成文档更新 = 本批次未完成

---

## Required Updates（必须项）

### 1. 本轮变更（What Changed）

- 批次目标（单一目标）
- 实际完成内容（精确到模块/文件/能力）
- 未完成项（若有必须说明）

### 2. 影响范围（Impact Scope）

- 涉及模块（addons / frontend / contract）
- 是否影响：
  - 启动链
  - contract/schema
  - default_route
  - public intent

### 3. 风险说明（Risk）

- 已知风险（明确列出）
- 风险级别（P0 / P1 / P2）
- 缓解策略（fallback / compat / 限制使用）

### 4. 验证结果（Verification）

- 执行命令
- 结果（PASS / FAIL）
- 失败项（如存在）

### 5. 产物路径（Artifacts）

- snapshot 路径
- logs 路径
- playwright / e2e 产物
- contract 导出

### 6. 回滚路径（Rollback）

- 对应 commit / tag
- snapshot 回退方式
- feature flag（如有）

### 7. 后续计划（Next Batch）

- 下一批次目标（唯一）
- 是否需要前置语义拍板
- 是否存在阻塞项

---

## Document Paths（标准路径）

### 迭代记录

- `docs/ops/iterations/phase_X_batch_Y.md`

### 发布说明

- `docs/ops/releases/phase_X_summary.md`
- `docs/ops/releases/templates/governance_incident_release_note_v1.md`（治理层缺陷复盘模板）

### 架构变更（如涉及）

- `docs/architecture/*`

### 契约与快照

- `artifacts/contract/*`
- `artifacts/codex/*`

---

## Output Template（强制结构）

```md
# Batch-X Release Note

## 1. 本轮变更
- 目标：
- 完成：
- 未完成：

## 2. 影响范围
- 模块：
- 启动链：是/否
- contract：是/否
- 路由：是/否

## 3. 风险
- P0：
- P1：
- P2：

## 4. 验证
- 命令：
- 结果：

## 5. 产物
- snapshot：
- logs：
- e2e：

## 6. 回滚
- commit：
- 方法：

## 7. 下一批次
- 目标：
- 前置条件：
```

## Governance Incident Example（治理层缺陷复盘示例）

```md
# Batch-Fx Release Note（治理层根因修复）

## 1. 本轮变更
- 目标：修复创建态语义判定错误，杜绝系统生成字段在创建页泄漏。
- 完成：
  - 修复 `render_profile` 判定：`new/0/null/none/false` 统一归入 create。
  - 补强 `project.project` 表单识别：含 `form` 视图（含 `tree,form`）均触发表单治理。
  - 固化系统生成字段策略：`project_code/code` 仅 `edit/readonly` 可见。
- 未完成：全量创建页策略巡检（留到下一批次）。

## 2. 影响范围
- 模块：`addons/smart_core`、`addons/smart_construction_core`、`.codex/skills/*`
- 启动链：否
- contract：是
- 路由：否

## 3. 风险
- P0：历史缓存契约可能短时显示旧字段（需强刷）。
- P1：其他模型可能存在同类 create/edit 语义判定缺陷。
- P2：文档未同步会导致团队回归到前端兜底思路。

## 4. 验证
- 命令：`make mod.upgrade ... smart_core,smart_construction_core`；`make contract.export ... ui.contract(op=model)`
- 结果：PASS（`render_profile=create`，`visible_fields` 不含 `project_code/code`）。

## 5. 产物
- snapshot：`artifacts/contract/rootfix/project_ui_contract_model_create_admin_postfix.json`
- logs：`artifacts/codex/...`（按批次目录）
- e2e：N/A（本批次以契约验收为主）

## 6. 回滚
- commit：回退本批次治理补丁 commit。
- 方法：`make mod.upgrade ... smart_core` 后重启服务并恢复前一版 snapshot。

## 7. 下一批次
- 目标：全量扫描“系统生成字段”在创建态的契约可见性。
- 前置条件：确认统一字段分类清单（system-generated / user-input）。
```

---

## Hard Constraints

- 不允许“只改代码不写文档”。
- 不允许“总结模糊”（必须可追溯到文件/命令）。
- 不允许遗漏验证结果。
- 不允许无回滚路径。
- 不允许下一批次无明确目标。

---

## Quality Gate（文档门禁）

文档必须满足：

- 可复现（别人可按文档复现验证）
- 可回滚（明确路径）
- 可追踪（关联 snapshot / logs / trace_id）

👉 不满足 = 批次未完成

---

## Anti-Patterns（禁止）

- “优化了一些东西”这种描述
- 不写失败项
- 不写风险
- snapshot 未更新但写“已完成”
- 文档与实际代码不一致

---

## Batch Reminder

```text
当前批次必须明确：
- 是否有 contract/snapshot 更新
- 是否有验证产物
- 是否可回滚

否则，不允许收口
```

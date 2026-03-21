---
name: openai-docs-first
description: 涉及 Codex/MCP/OpenAI 能力时先查官方文档，再做配置与实现决策。
metadata:
  short-description: 官方文档优先（执行强化版）
---

# OpenAI Docs First

## Use When
- 涉及 Codex CLI / Skills / MCP / OpenAI API / 模型能力
- 涉及配置（API Key / endpoint / model / tool / runtime）
- 涉及行为差异（工具调用 / reasoning / streaming / limits）

## Workflow（强制顺序）

1. 确认官方文档：
   - API 能力
   - 参数约束
   - 版本差异（模型/SDK/CLI）
2. 标记关键约束：
   - 必填参数
   - 不支持能力
   - 限制（rate/token/tool）
3. 对照当前仓库：
   - 是否已有实现路径
   - 是否冲突（Makefile / Codex policy / execution allowlist）
4. 收敛最小方案：
   - 只启用必要能力
   - 不引入额外抽象层
5. 定义验证路径：
   - CLI/接口验证命令
   - 预期输出
6. 再实施代码或配置

## Hard Constraints

- 不允许基于“经验”跳过文档确认。
- 不允许引入未验证能力（如 tool calling / reasoning 扩展）。
- 不允许同时修改：模型 + 调用方式 + 契约结构。
- 不允许绕过仓库执行策略（必须走 Makefile / allowlist）。
- 若文档与现有实现冲突，优先收敛方案，不直接重构系统。
- 未确认稳定版本，不进入生产路径。

## Adaptation Strategy

- 优先适配当前架构（intent / contract / scene），而非改架构适配模型。
- 模型能力作为“插件能力”，不得侵入主链。
- MCP / Codex 能力必须可关闭（feature flag）。
- 所有外部能力必须有 fallback（本地逻辑或降级路径）。

## Output（必须产出）

- 文档结论摘要：
  - 支持能力 / 限制 / 推荐用法
- 本仓库适配策略：
  - 接入点（CLI / service / intent）
  - 是否新增模块或仅配置
- 配置清单：
  - model / endpoint / key / flags
- 验证命令与结果：
  - CLI / API 调用示例
- 风险与兼容性说明：
  - 版本漂移风险
  - fallback 策略

## Verification

```bash
# 示例（根据实际能力替换）
make codex.cli CODEX_CLI_ARGS="--version"
make verify.codex.smoke
```

## Rollback Strategy

- 保留旧配置（model / endpoint）
- feature flag 关闭新能力
- 恢复旧调用路径（CLI/API）
- 清理缓存/凭证（避免脏状态）

## Anti-Patterns（禁止）

- 未查文档直接接入新模型
- 用“试出来”的参数进入正式配置
- 将模型能力写死在业务逻辑中
- CLI 调用绕过 Makefile 执行链
- 多能力同时引入（Codex + MCP + 新模型）
- 无 fallback 的强依赖接入

## Batch Reminder

```text
当前批次必须明确：
- 使用的 OpenAI 能力（Codex / MCP / API）
- 目标模型与版本
- 是否影响现有调用链

未明确，不允许进入实现
```

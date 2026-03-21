# Project Skills Router

This repository defines project-local Codex skills under `.codex/skills`.

## Governance Baseline (v2)

Mandatory baseline for every task:
- Single batch, single objective.
- Layer isolation and batch isolation.
- Contract first, semantic freeze before code.
- Code result != contract result != gate result.
- Fixed startup chain: `login -> system.init -> ui.contract`.
- Role source of truth: `role_surface.role_code`.

If any baseline rule is violated, the batch is invalid.

## Skill Routing Table (Mandatory)

Use this table to force the correct skill at task start:

| Scenario | Required Skill |
| -- | -- |
| Governance / batch authority / boundary control | `project-governance-codex` |
| Batch decomposition and execution pacing | `batch-execution` |
| Contract audit and closure decision | `contract-audit` |
| Odoo addon/model/service/controller change | `odoo-module-change` |
| Frontend schema/store/page contract consumption | `frontend-contract-consumer` |
| Verification and release gate decision | `verify-and-gate` |
| Release note / iteration / artifacts sync | `release-note-and-doc-update` |
| Plan before implementation | `create-plan` |
| OpenAI/Codex/MCP capability decisions | `openai-docs-first` |
| UI regression and contract-consumption checks | `playwright-ui-check` |

## Trigger Format (Required)

Always trigger skills explicitly in prompt:

```text
使用 skill: <skill-name>
任务：<具体动作>
批次：Batch-X
```

Example:

```text
使用 skill: contract-audit
任务：审计 login 返回结构
批次：Batch-B
```

## Batch Input Master Template

Use this as the default entry for all implementation batches:

```text
启动 Batch-X

Layer Target：
Module：
Reason：

目标：
范围：
不做：

指定 skills：
- 主 skill：
- 辅 skill：
```

Parallel rule: only one-main one-assist is allowed.

## Recommended Skill Sequence

1. `project-governance-codex`
2. `create-plan`
3. `batch-execution`
4. Domain skill (`contract-audit` / `odoo-module-change` / `frontend-contract-consumer`)
5. `verify-and-gate`
6. `release-note-and-doc-update`

## References (Hard Guard)

- `docs/ops/codex_execution_allowlist.md`
- `docs/ops/codex_workspace_execution_rules.md`
- `ARCHITECTURE_GUARD.md`
- `docs/architecture/ai_development_guard.md`

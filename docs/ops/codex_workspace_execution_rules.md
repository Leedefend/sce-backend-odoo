# Codex Workspace Execution Rules (Hard Guard)

## 目标
- 防止 Codex 在错误仓库、错误路径、错误分支下执行改动。
- 将“执行前校验”变成强制步骤，而不是可选习惯。

## 适用范围
- 本仓库内所有 Codex 代码改动、文档改动、开发验证执行。
- 不适用于人工监督下的服务器生产部署协助；该场景适用
  `docs/ops/codex_production_assist_policy.md`。
- 生产协助模式下，Codex 不得修改仓库文件、不得执行 Git 写操作，只能执行只读检查和
  `docs/ops/prod_command_policy.md` 允许的 Makefile target。

## 强制执行步骤（每次开始改动前）
1. **工作目录校验**
   - 必须执行：`pwd`
   - 必须执行：`git rev-parse --show-toplevel`
   - 结果必须指向当前仓库根目录。

2. **分支校验**
   - 必须执行：`git branch --show-current`
   - 分支必须匹配 allowlist：`feat/*`、`feature/*`、`codex/*`、`experiment/*`。
   - 若不匹配，立即停止执行。
   - 例外：人工监督的生产部署协助允许 `main`、tag 或冻结 commit，但仅限只读检查和
     生产策略允许的 Makefile target，禁止任何写文件或 Git 写操作。

3. **仓库标识校验**
   - 必须执行：`git status --short`
   - 必须执行：`git rev-parse --short HEAD`
   - 在执行日志中记录当前分支与短 SHA，作为本轮上下文锚点。

4. **目标模块存在性校验**
   - 变更前必须确认目标模块路径存在（例如 `addons/smart_core`、`frontend/apps/web`）。
   - 若路径不存在，立即停止执行并报告“疑似错误仓库/路径”。

## 执行中防漂移规则
- 每次大批量 `apply_patch` 前，必须再次执行：
  - `git branch --show-current`
  - `git rev-parse --show-toplevel`
- 若与本轮起始锚点不一致，立即停止并回报。

## 禁止行为
- 未完成上述校验即直接改文件。
- 在未确认仓库与分支的情况下执行连续迭代。

## 失败处理
- 一旦发现上下文错位：
  1. 立即停止改动。
  2. 输出当前 `pwd`、`git branch --show-current`、`git rev-parse --show-toplevel`。
  3. 等待人工确认后再继续。

## 审计要求
- 每个迭代批次在 `docs/ops/iterations/delivery_context_switch_log_v1.md` 记录：
  - 当前分支
  - 当前短 SHA
  - 本轮 Layer Target / Module / Reason

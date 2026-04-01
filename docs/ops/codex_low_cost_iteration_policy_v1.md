# Codex Low-Cost Iteration Policy v1

状态：Execution Policy  
适用对象：Codex 治理类任务、`agent_ops` 连续迭代、模板化批次拆分

---

## 1. 目标

本规范用于把当前迭代执行方式收敛为：

- 低消耗
- 短上下文
- 强约束
- 可连续执行

该模式默认适用于治理类与审计类任务，不扩展为业务实现自由模式。

---

## 2. 三段式任务模式

所有低消耗任务默认拆为以下三阶段：

### 2.1 `scan`

职责：

- 只找候选
- 只做路径级与模块级观察
- 只输出候选清单

禁止：

- 不得下结论
- 不得修改代码
- 不得生成验证结论
- 不得把候选直接升级为最终分类

### 2.2 `screen`

职责：

- 只读取 `scan` 结果
- 只做候选归类
- 只输出下一候选家族及理由

禁止：

- 不得再次扫描仓库
- 不得读取新的业务文件
- 不得补做 `scan` 阶段工作
- 不得执行验证命令

### 2.3 `verify`

职责：

- 只执行已声明验证命令
- 只读取 `screen` 结果
- 只输出结构化判定

禁止：

- 不得做新推理
- 不得引入新候选
- 不得再次扫描仓库
- 不得修改任务范围

---

## 3. 单任务单阶段规则

Rule 1：
所有治理类任务默认先拆为 `scan/screen/verify` 三阶段。

Rule 2：
每阶段只允许一个目标。

- `scan` = 找候选
- `screen` = 做归类
- `verify` = 做校验

Rule 3：
禁止单次任务同时做：

- 扫描
- 判断
- 验证
- 报告

---

## 4. 硬限制

低消耗模式必须声明并遵守以下限制：

- `max_files`
- `max_candidates`
- `max_output_lines`
- `forbid_repo_wide_scan`

默认值：

- `max_files: 12`
- `max_candidates: 15`
- `max_output_lines: 80`
- `forbid_repo_wide_scan: true`

阶段上限：

- `scan`：最多 15 个候选
- `screen`：最多 80 行输出
- `verify`：只输出结构化结果

若任务合同未显式覆盖，默认采用上述值。

---

## 5. Session 规则

低消耗模式必须遵守：

- 每个子任务必须新 session
- 禁止跨任务复用长上下文
- 禁止把 A 阶段原始仓库观察直接带入 C 阶段推理
- 每阶段只能消费上一阶段产物与本阶段允许输入

执行提示必须明确包含：

- `use_new_session: true`
- `carry_long_context: false`

---

## 6. 仓库扫描限制

低消耗模式禁止 repo-wide scan。

禁止行为：

- 全仓 `rg` / `find` / `git diff` 无路径边界扫描
- 在 `screen` / `verify` 阶段重新读取候选外文件
- 在阶段内扩展到任务合同未声明模块

允许行为：

- 只对任务 allowlist 范围做定向读取
- 只读取上一阶段结果文件
- 只在 `scan` 阶段做受限候选发现

---

## 7. 输出约束

所有低消耗阶段必须优先结构化输出。

### 7.1 `scan` 输出

必须输出 JSON 数组，每项只允许：

- `path`
- `module`
- `feature`
- `reason`

### 7.2 `screen` 输出

只允许输出：

- `next_candidate_family`
- `family_scope`
- `reason`

### 7.3 `verify` 输出

只允许输出：

- `status`
- `violations`
- `decision`

其中 `status` 只能为：

- `PASS`
- `FAIL`
- `STOP`

---

## 8. 继续执行规则

当且仅当以下条件同时成立时，低消耗链允许继续：

- 当前阶段输出结构合法
- 未触发限制超标
- 未触发 forbidden paths
- `verify.status = PASS`

若 `verify.status` 为 `FAIL` 或 `STOP`，则必须立即停止。

---

## 9. Stop 规则

出现以下任一情况必须立即停止：

- 超出 `max_files`
- 超出 `max_candidates`
- 超出 `max_output_lines`
- 触发 `forbid_repo_wide_scan`
- 触发 forbidden paths
- 阶段职责混淆
- 需要跨阶段补推理才能完成判定

---

## 10. 模板与入口规则

低消耗模式优先使用仓库模板：

- `agent_ops/templates/task_low_cost.yaml`
- `agent_ops/templates/prompts/lead_scan.txt`
- `agent_ops/templates/prompts/lead_screen.txt`
- `agent_ops/templates/prompts/lead_verify.txt`

复杂任务必须先 plan，再实现。

默认使用单代理、分阶段、短上下文模式。

只有在明确需要并行时才允许启用 subagents。

---

## 11. 与现有 agent_ops 兼容规则

本规范必须保持与现有 `agent_ops` 兼容：

- 不替换现有任务合同主结构
- 通过增量字段表达 `mode` 与 `limits`
- 保持 `validate_task.py` 可继续验证
- 保持 `run_iteration.sh` 可继续作为旧流程入口

低消耗模式是新增执行轨，不是对旧流程的破坏性替换。

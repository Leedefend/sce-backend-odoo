# 表单结构契约统一 Runbook v1

## 目标

所有正式业务表单在前端运行态接收一致的结构契约：

- 标准页签：主信息、业务明细、来源追溯、备注说明。
- 分组语义：每个业务分组必须有可渲染标题和 `semanticTitle`。
- 协作能力：附件、时间线/日志、关注/消息入口由统一契约承载。

该能力属于 Unified Page Contract v2 运行态投影，不属于前端业务逻辑。

## 架构边界

- 后端契约层负责将原生 Odoo form arch 标准化为前端可直接消费的结构。
- 前端只根据 `layoutContract`、`runtimeContract.collaboration` 和字段元数据渲染，不判断具体业务模型。
- 业务事实层只有在字段、关系、权限、工作流或事实承载缺失时才改模型/XML。
- 不能为了统一视觉结构而逐个业务视图补 notebook/group/chatter。

## 默认处理策略

1. 先跑原生视图审计，识别 XML/运行态 arch 的真实差异。
2. 再跑 v2 运行态契约审计，确认前端实际接收的结构。
3. 如果原生 XML 有缺口但 v2 契约已标准化，不改业务 XML。
4. 如果 v2 契约仍缺页签、分组语义、附件或日志，优先修复 `unified_page_contract_v2_assembler.py` 的标准化器。
5. 只有业务事实本身缺字段或缺关系时，才进入业务事实层修改。

## 验收命令

```bash
ENV=dev ENV_FILE=.env.dev COMPOSE_PROJECT_NAME=sc-backend-odoo-dev PROJECT=sc-backend-odoo-dev DB_NAME=sc_demo make verify.form_structure.contract
```

该命令会执行：

- `scripts/verify/form_structure_contract_standardizer_guard.py`
- `scripts/verify/form_structure_contract_runtime_audit.sh`

报告输出：

- `docs/audit/native/form_structure_contract_runtime/form_structure_contract_runtime_audit.md`
- `docs/audit/native/form_structure_contract_runtime/form_structure_contract_runtime_audit.csv`
- `docs/audit/native/form_structure_contract_runtime/form_structure_contract_runtime_audit.json`

## 当前验收基线

截至本 runbook 建立时，`sc_demo` 运行态 v2 契约审计结果：

- 运行态业务表单契约：115
- `contract_standardized`：115
- 仍需关注：0
- 附件契约覆盖：115
- 时间线/日志契约覆盖：115

## 后续专题执行口径

后续统一其他表单视图时，先看运行态 v2 契约报告。除非报告证明 v2 契约无法表达某个业务事实，否则不要把结构统一任务下沉到每个业务视图 XML。

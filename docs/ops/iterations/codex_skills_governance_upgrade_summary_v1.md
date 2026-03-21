# Codex Skills Governance Upgrade Summary v1

## Scope
- Branch: `codex/skills-governance-bootstrap`
- Layer Target: `Platform Layer`
- Module: `.codex/skills/*`
- Reason: 将《Codex 协作机制 v2》固化为可执行技能体系，支持批次化实现、独立审计和门禁收口。

## Upgraded Skills
- `project-governance-codex`: 升级为 v2 总控机制，固定角色、唯一执行管线、系统级红线、最终裁决规则。
- `batch-execution`: 强制单目标批次、语义前置、实现顺序、并行约束、停止条件。
- `contract-audit`: 增加启动链/版本/边界检查与 `S0/S1/S2` 严重级别，输出可执行审计结论。
- `verify-and-gate`: 三层结论拆分（Code/Contract/Gate），失败分类、判定矩阵、环境可信规则。
- `odoo-module-change`: 强化升级路径、兼容策略、反模式、回滚方案与主链保护。
- `frontend-contract-consumer`: 强化 `schema -> store -> 页面` 顺序，禁止前端语义推导。
- `release-note-and-doc-update`: 强化文档门禁与批次收口模板，要求可复现/可回滚/可追踪。
- `create-plan`: 强化计划生成结构，要求依赖关系、完成判据、验证与停机条件。
- `openai-docs-first`: 强化官方文档优先流程、最小接入策略、fallback 与回滚。
- `playwright-ui-check`: 强化分层用例、断言、失败分类与产物路径。

## Router Upgrade
- `.codex/skills/README.md` 升级为“技能路由表 + Batch 输入总入口”。
- 固化场景到技能映射、显式触发格式、主辅技能输入模板和推荐执行序列。

## Project Constraints Embedded
- 启动链固定：`login -> system.init -> ui.contract`
- role 真源唯一：`role_surface.role_code`
- `default_route` 以后端契约为准
- public intent 禁止随意 rename 或语义漂移
- compat 生命周期完整：`introduce -> observe -> default -> deprecate -> remove`

## Governance Patch v1.1（项目编号创建态泄漏根因修复）
- 业务事实：`project_code/code` 属于系统生成字段，不应出现在 `project.project` 创建态表单。
- 契约判定规则：`render_profile` 识别时必须排除伪记录标记（`new/0/null/none/false`），仅正整数 `id/res_id` 判定为编辑态。
- 表单识别规则：`project.project` 只要契约中包含 `form` 视图（含 `tree,form` 复合场景）即触发表单治理规则。
- 可见性规则：系统生成字段默认 `create` 不可见，仅 `edit/readonly` 可见。
- 验收证据：批次收口必须附 create 契约快照，明确 `render_profile=create` 且 `visible_fields` 不含 `project_code/code`。

## Trial Run Recommendation
- 试点批次：`Batch-B`
- 试点目标：`system.init 角色真源统一`
- 主 skill：`batch-execution`
- 辅 skill：`contract-audit`
- 门禁 skill：`verify-and-gate`

## Acceptance Checklist
- [ ] 批次输入遵循 Master Template（目标/范围/不做/主辅 skill）
- [ ] 实现线与审计线分离（A 线/ B 线）
- [ ] 输出包含 Code/Contract/Gate 三层结论
- [ ] 文档与 snapshot/日志路径同步

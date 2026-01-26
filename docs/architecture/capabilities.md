# Capability Codes (Phase N1)

Capabilities are user intents that map to system behaviors.
They are not menus or models; they are stable capability codes.

Project
- project.edit_basic: edit project basic info (name, dates, owner)
- project.lifecycle.transition: change lifecycle_state
- project.close: close project

Task
- task.create: create task/work item
- task.start: start task execution
- task.complete: mark task complete

Finance
- finance.settlement.create: create settlement order
- finance.payment.submit: submit payment request

Contract / BOQ / Cost
- contract.create: create contract
- boq.edit: edit BOQ structure/lines
- cost.entry: record cost/progress entry

Portal UI labels and hints (CN)
- project.edit_basic: label=编辑项目基础信息, hint=项目关闭后不可修改
- project.lifecycle.transition: label=变更生命周期状态, hint=受流程门禁约束
- project.close: label=项目关闭, hint=关闭后仅可查看
- task.create: label=创建任务, hint=暂停/关闭阶段不可创建
- task.start: label=启动任务, hint=需满足就绪条件
- task.complete: label=完成任务, hint=完成度达到要求
- finance.settlement.create: label=创建结算单, hint=执行阶段开放
- finance.payment.submit: label=提交付款申请, hint=需结算审批通过
- contract.create: label=创建合同, hint=按项目阶段开放
- boq.edit: label=编辑BOQ, hint=结构冻结后只读
- cost.entry: label=录入成本/进度, hint=仅执行阶段允许

# 能力清单（Phase N1）

能力是“用户意图 + 系统行为”的稳定编码，
不是菜单、不是模型。

项目类
- project.edit_basic：编辑项目基础信息（名称、日期、负责人）
- project.lifecycle.transition：变更生命周期状态
- project.close：项目关闭

任务类
- task.create：创建任务/工序
- task.start：启动任务执行
- task.complete：完成任务

财务类
- finance.settlement.create：创建结算单
- finance.payment.submit：提交付款申请

合同 / BOQ / 成本
- contract.create：创建合同
- boq.edit：编辑 BOQ/清单结构
- cost.entry：录入成本/进度

Portal 展示文案（label/hint）
- project.edit_basic：label=编辑项目基础信息，hint=项目关闭后不可修改
- project.lifecycle.transition：label=变更生命周期状态，hint=受流程门禁约束
- project.close：label=项目关闭，hint=关闭后仅可查看
- task.create：label=创建任务，hint=暂停/关闭阶段不可创建
- task.start：label=启动任务，hint=需满足就绪条件
- task.complete：label=完成任务，hint=完成度达到要求
- finance.settlement.create：label=创建结算单，hint=执行阶段开放
- finance.payment.submit：label=提交付款申请，hint=需结算审批通过
- contract.create：label=创建合同，hint=按项目阶段开放
- boq.edit：label=编辑BOQ，hint=结构冻结后只读
- cost.entry：label=录入成本/进度，hint=仅执行阶段允许

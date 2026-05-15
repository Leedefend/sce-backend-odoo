# Model View Standardization Plan

- source: `artifacts/backend/model_view_fact_layer_audit.json`
- model_count: 116
- P0: 0
- P1: 0
- OK: 116

## Frameworks

### 业务单据模型 (`business_document`)
- policy: 可创建/可编辑的承载业务事实模型，统一补齐附件、日志、状态和业务日期信号。
- list_frame: 状态, 单据号/名称, 项目/公司, 往来单位, 金额, 业务日期, 录入人, 录入时间, 附件
- form_frame: 头部状态与动作, 基本信息, 业务信息, 金额/明细, 附件, 日志/沟通, 历史溯源

### 业务明细行模型 (`business_detail_line`)
- policy: 明细行不强制独立状态/日志，附件按业务需要从父单据继承或关联。
- list_frame: 父单据, 项目/业务对象, 名称/编码, 数量, 单价, 金额, 备注
- form_frame: 父单据, 明细信息, 数量金额, 备注

### 报表汇总模型 (`report_summary`)
- policy: 报表以只读列表和钻取为主，不强制附件/日志/状态。
- list_frame: 期间/项目/公司, 分类维度, 指标金额, 累计值, 更新时间
- form_frame: 只读摘要, 维度信息, 指标明细, 来源说明

### 历史事实模型 (`legacy_fact`)
- policy: 历史事实模型优先只读、可追溯，不强制 Odoo chatter；附件以历史文件索引或附件引用表达。
- list_frame: 旧系统编号, 项目/公司, 业务日期, 金额/数量, 来源模型, 历史录入人, 历史录入时间
- form_frame: 历史来源, 原始字段, 映射字段, 附件索引/历史文件, 投影去向

### 配置/字典模型 (`configuration`)
- policy: 配置模型不按业务数据缺口处理，重点是可维护、可审计、权限边界明确。
- list_frame: 名称/编码, 分类, 启用状态, 排序, 更新时间
- form_frame: 配置基本信息, 适用范围, 规则/参数, 变更说明

### 主数据/组织权限模型 (`master_data`)
- policy: 主数据重点是身份一致性、去重、授权和历史来源。
- list_frame: 名称, 编码/账号, 类型, 所属公司/部门, 启用状态, 更新时间
- form_frame: 基础身份, 组织关系, 联系方式/权限, 历史来源

## P0 Queue

| lane | domain | model | records | missing | first action |
|---|---|---|---:|---|---|

## P1 Queue

| lane | domain | model | records | missing |
|---|---|---|---:|---|

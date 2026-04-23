# 旧库业务事实资产化重建方案 v1

状态：Frozen Migration Governance
适用范围：旧库业务事实抽取、标准化、目标模型映射、数据资产装载、新库重建验证
结论：迁移主路线从“一次性直接写新库”校准为“旧库业务事实 -> 新系统标准模型数据资产 -> 可重复重建”。

## 1. 总体目标

本项目后续迁移不再以“把旧库在线 update 到新库”为最高目标。

冻结目标是：

```text
旧库业务事实
  -> 标准化事实
  -> 新系统目标模型映射
  -> 可版本管理的数据资产包
  -> 新库分阶段重建与校验
```

这条路线的完成标准不是某一次数据库写入成功，而是形成可反复执行、可审计、可调整、可重新导入的重建能力。

## 2. 不再采用的默认策略

以下做法不作为后续主路线：

- 直接把旧库数据一次性 update 到新库。
- 把所有旧库数据无差别转换成 XML。
- 以每轮临时 JSON/CSV 作为长期迁移资产。
- 把运行时派生字段、日志、chatter、activity、自动统计字段硬编码成静态资产。
- 为了迁移补齐而修改新系统业务语义、ACL、财务语义或前端特判。

## 3. 五层数据资产化

### 第 1 层：旧库原始事实层

目标：留证据，不做语义改写。

内容包括：

- 原始表名、字段名、主键、外键或弱关联。
- 原始枚举值、状态值、日期、金额、文本。
- 原始来源系统或来源切片。
- 原始脏数据、缺失值、冲突值。

产物形态：

- 只读抽取 manifest。
- 原始事实字典。
- 抽样证据或外部运行证据。

入库原则：

- 原始大批量明细不入主仓库。
- 阶段冻结后的事实字典、字段字典、来源清单可以入库。

### 第 2 层：标准化事实层

目标：把旧库事实清洗成可理解、可引用、可复核的稳定事实。

标准化动作包括：

- 状态值统一。
- 日期、金额、精度、币种口径统一。
- 单位名称、项目名称、合同编号、客商名称归一。
- 重复记录、弱引用、组合来源、缺失引用分类。
- 垃圾数据按已冻结策略丢弃。

产物形态：

- 标准化事实表。
- 清洗规则表。
- 冲突分类表。
- 丢弃规则与丢弃计数摘要。

硬规则：

- 标准化不能伪造业务事实。
- 新系统非必填字段允许空缺，不为迁移补假值。
- 企业往来单位优先按企业主体处理，垃圾数据直接丢弃。

### 第 3 层：新模型映射层

目标：把标准化事实映射到新系统模型与字段。

当前已知主线映射：

| 旧库事实 | 新系统目标 | 资产优先级 |
| --- | --- | --- |
| 往来单位事实 | `res.partner` / legacy identity carrier | 核心主数据 |
| 项目主档 | `project.project` | 核心业务事实 |
| 项目成员中性事实 | project member neutral staging | 业务辅助信息 |
| 合同主档 | contract header target model | 核心业务事实 |
| 收款申请核心事实 | `payment.request(type=receive)` | 核心业务事实，但不触发结算/会计 |
| 付款、结算、会计事实 | 待单独边界恢复 | 高风险，默认排除 |

映射层必须维护：

- 旧字段 -> 新字段映射。
- 旧主键 -> stable external id 映射。
- 必填字段满足策略。
- 空缺字段允许策略。
- 不导入字段与原因。
- 派生字段重建方式。

### 第 4 层：装载资产层

目标：生成新库可重放的数据资产包。

允许载体：

- XML：配置、主数据、结构稳定且规模可控的业务主实体。
- CSV：中大批量、结构扁平、差异审查可接受的数据。
- JSON：中间 manifest、loader 输入、分批 payload。
- Python loader：需要 ORM 逻辑、分批事务、二次构建或复杂依赖的数据。

载体选择规则：

| 数据类型 | 首选载体 | 说明 |
| --- | --- | --- |
| 配置、字典、场景、默认参数 | XML | 需要版本管理和跨环境一致 |
| 公司、部门、岗位、项目类型、状态 | XML | 主数据稳定，适合外部标识 |
| 客商、项目、合同主档 | XML 或 CSV + loader | 取决于规模和模型稳定度 |
| 项目成员、合同关系、任务关系 | CSV + loader | 关系多、依赖强，便于批量校验 |
| 成本、付款、结算、会计流水 | CSV/JSON + loader | 不默认 XML，需高风险边界任务 |
| chatter、activity、日志、统计字段 | 导入后脚本或不迁移 | 运行时派生，不做静态事实资产 |

### 第 5 层：环境重建层

目标：在新库中按顺序导入并验证，形成一键或准一键重建能力。

重建步骤：

1. 安装新系统业务模块，不安装 demo 模块。
2. 装载基础配置与主数据资产。
3. 装载核心业务主实体资产。
4. 装载辅助关系与中性事实资产。
5. 执行二次构建脚本。
6. 执行重建校验。
7. 输出重建 manifest、计数、失败分类、回滚说明。

## 4. external id 规则

所有可重放核心记录必须有稳定 external id。

格式：

```text
legacy_<lane>_<source>_<legacy_pk>
```

示例：

- `legacy_partner_sc_3308`
- `legacy_project_sc_1001`
- `legacy_contract_sc_20045`
- `legacy_receipt_sc_90001`

规则：

- `lane` 使用业务车道名称：`partner`、`project`、`contract`、`receipt`、`project_member`。
- `source` 使用来源系统或来源切片，当前默认 `sc`。
- `legacy_pk` 必须来自旧库稳定主键或已冻结的复合来源键。
- 不允许使用新库自增 id 作为 external id 组成部分。
- 组合来源必须先在标准化事实层冻结 canonical key。
- 丢弃数据不分配 external id，但必须在阶段摘要里保留丢弃计数与规则。

引用规则：

- 跨资产包引用必须使用 external id。
- loader 写库前必须先解析 external id 依赖。
- 缺失依赖时默认阻断该记录，不自动创建假引用。
- 非核心辅助信息可以延迟绑定，但必须在 manifest 中标记 `deferred_reference`。

## 5. 分包规范

数据资产包采用固定层级：

```text
migration_assets/
  00_base/
  10_master/
  20_business/
  30_relation/
  40_post/
  manifest/
```

### 00_base

内容：

- 公司、部门、岗位。
- 字典、分类、状态。
- 基础配置与默认参数。

优先载体：XML。

### 10_master

内容：

- 客商主档。
- 项目主档。
- 合同主档。

优先载体：XML 或 CSV + loader。

### 20_business

内容：

- 收款申请核心事实。
- 任务、成本、付款等后续业务事实。

优先载体：CSV/JSON + loader；规模小且稳定时可 XML。

### 30_relation

内容：

- 项目成员。
- 项目-合同关系。
- 合同-客商关系。
- 业务辅助关系。

优先载体：CSV + loader。

### 40_post

内容：

- 二次构建。
- 状态校正。
- 可见性补齐。
- 派生字段重算。

优先载体：Python loader 或 Odoo shell runner。

### manifest

内容：

- 资产包版本。
- 生成时间。
- 来源库快照。
- 每包记录数。
- external id 覆盖率。
- 依赖顺序。
- 校验命令。
- 丢弃计数。
- 已知缺口。

## 6. 重建导入顺序

冻结顺序：

1. `00_base/company_department_post_dictionary`
2. `10_master/partner`
3. `10_master/project`
4. `10_master/contract_header`
5. `30_relation/project_member_neutral`
6. `20_business/receipt_core`
7. `40_post/reference_bind_and_state_recompute`
8. `manifest/rebuild_acceptance`

高风险车道暂不进入默认顺序：

- payment settlement。
- accounting。
- ACL/security。
- record rules。
- manifest/module install order changes。

这些车道必须由独立高风险任务契约授权。

## 7. 校验清单

每个资产包至少验证：

- 文件结构存在。
- manifest 可解析。
- external id 唯一。
- required reference 可解析。
- 必填字段满足新模型约束。
- 丢弃计数与规则一致。
- 导入后目标模型计数符合 manifest。
- 重跑导入不产生重复记录。
- 高风险车道未被隐式触发。

当前最小门禁：

```bash
python3 agent_ops/scripts/validate_task.py <task>
make verify.native.business_fact.static
git diff --check
```

进入真实资产生成后，应追加：

```bash
python3 scripts/migration/<asset_generator>.py --check
python3 scripts/migration/<asset_manifest_verify>.py
DB_NAME=<fresh_db> make odoo.shell.exec < scripts/migration/<loader>.py
```

## 8. 迁移迭代步骤

后续迁移按以下节奏推进：

### Step 1：事实字典冻结

输出：

- 旧库事实字典。
- 旧字段清单。
- 主键与弱关联清单。
- 不迁移字段清单。

验收：

- 每个业务车道都有来源表、来源键、业务含义、导入策略。

### Step 2：标准化规则冻结

输出：

- 清洗规则。
- 丢弃规则。
- 缺失字段策略。
- 组合来源 canonical key 规则。

验收：

- 不再为垃圾数据、缺失辅助字段、非必填字段阻断核心事实迁移。

### Step 3：目标模型映射冻结

输出：

- 旧 -> 新模型映射表。
- 字段映射表。
- 必填字段策略。
- 派生字段处理策略。

验收：

- 每个核心事实都能判定为 `load`、`defer`、`discard` 或 `high_risk_excluded`。

### Step 4：external id 与资产包规范落地

输出：

- external id 生成器。
- 资产包目录结构。
- manifest schema。

验收：

- partner/project/contract/receipt 至少一个车道可生成稳定 external id manifest。

### Step 5：资产生成器替代一次性写库脚本

输出：

- XML/CSV/JSON 资产生成器。
- loader 输入。
- asset manifest。

验收：

- 在不连接新库写入的情况下，可重复生成同样资产包。

### Step 6：新库重建 runner

输出：

- fresh DB 安装脚本。
- 分包导入 runner。
- 导入后校验 runner。

验收：

- 新库可从资产包重建到已冻结业务范围。

### Step 7：车道扩展

顺序：

1. 已完成重放车道资产化：partner、project、project_member、contract、receipt。
2. 辅助业务事实补齐。
3. payment/settlement/accounting 高风险边界恢复。

验收：

- 每扩展一个车道，都必须先通过 `fact -> normalized -> mapping -> asset -> rebuild` 完整链路。

## 9. 当前主线校准结论

当前已完成的新库重放数据具备转入资产化路线的基础，但还不等于最终完成。

已具备：

- partner、project、project_member neutral、contract header、receipt core 的新库重放经验。
- fresh DB 无 demo 安装路径。
- manifest 刷新与 lane 状态管理经验。

需要立即补齐：

- 旧库事实字典。
- 标准化清洗规则。
- 旧 -> 新模型映射总表。
- external id 生成规则实现。
- 数据资产分包 manifest schema。
- 分包导入与校验 runner。

## 10. 后续调度原则

- 后续所有迁移批次优先产出“可重放资产”，不是只产出“写库结果”。
- XML 是核心载体之一，但不是唯一载体。
- 大批量业务事实优先 CSV/JSON + loader。
- 运行时派生数据只允许通过导入后构建，或明确不迁移。
- 没有 external id 的核心事实不得进入长期资产包。
- 没有 manifest 的资产包不得进入重建 runner。
- 高风险财务、结算、ACL、record rule 不随普通业务事实资产化批次混入。

## 11. 下一批建议

下一批应执行：

```text
ITER-MIGRATION-ASSET-MANIFEST-SCHEMA
```

唯一目标：

- 定义 `migration_assets/manifest` schema。
- 定义 external id manifest 字段。
- 选 partner 车道作为第一条资产化样板。

不做：

- 不写新库。
- 不重构已有迁移脚本。
- 不引入 payment/settlement/accounting。

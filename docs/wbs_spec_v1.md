# 📘 专业版 WBS 体系设计文档（可实施版）

面向：造价/成本/合同/结算/执行一体化的工程管理系统  
版本：v1.0  
适用：房建、市政、机电、装饰、景观等工程；招标/合同/变更/结算全流程  

---

## 第 1 章 体系目标与定位

### 1.1 设计目标
提供一个统一、标准化、可计算、可追溯的工程结构框架：
- 完全兼容中国工程造价体系（清单计价规范）
- 支撑预算、合同、变更、成本、结算、支付、执行全流程
- 可供 AI 解析，自动生成结构化数据与分析结果

覆盖范围：
- 分部分项工程 / 单价措施项目 / 总价措施项目 / 规费 / 税金 / 各类补充费用
- 通过“清单 → 结构 → 合价 → 汇总”自然贯通工程成本

### 1.2 行业标准引用
- 《建设工程工程量清单计价规范》（GB 50500–2013）及表格 F1.1、F1.2、F1.3
- 《全国统一建设工程计量规范》系列专业规范
- 投标工程量清单通用格式
- PMBOK（分解式 WBS 结构）、BIM 构件编号原则、CBS、OBS

### 1.3 适用范围
- 房建、市政、机电、装饰、景观等工程；覆盖可研、概算、预算、招标、合同、结算
- 支持多专业、多单位工程、多标段；多版本清单（投标/合同/变更/结算）；AI 自动分析与任务分解
- 可扩展到 BIM 模型自动生成、供应链/物流对接、工程执行成本与进度联动

### 1.4 系统定位
- **工程成本中心的唯一结构主线**：预算、合同、支付、变更、结算、成本核算均以 WBS 为主线
- **AI 可解释的结构体系**：由规则驱动生成，可识别工程逻辑、费用分布、风险点与依赖关系

---

## 第 2 章 WBS 树总体结构

### 2.1 六大结构类别（Section Categories）
工程项目 WBS 由六类核心结构构成：
- 单项工程（Project Division）
- 单位工程（Unit Project）
- 专业工程（Major Category）
- 分部工程（Sub-division）
- 分项工程（Item Category）
- 费用类结构（Fee/Tax/Other：措施、规费、税金等）

标准树形示例：
```
单项工程
 └─ 单位工程
      └─ 专业工程
           └─ 分部工程
                └─ 分项工程（清单项目）
                     └─ 费用子项（措施、规费、税金）
```

### 2.2 七类结构节点
统一的节点类型示例：
- project：项目根节点（如“工程大学消防站工程”）
- unit：单位工程（如“地下室工程、主体结构工程”）
- major：专业工程（如“建筑工程、机电工程、装饰工程”）
- division：分部工程（如“土石方工程、模板与支撑工程”）
- item：清单项（如“010102001 综合脚手架”）
- measure：措施项目（如“脚手架措施、混凝土养护、垂直运输”）
- fee：规费（如“社保费、工程排污费”）
- tax：税金（如“增值税”）
- total：预算/合同合计（如“项目汇总、合同总额”）

### 2.3 WBS 标准层级定义（核心结构）
| 层级 | 名称       | 来源      | 说明                     |
| ---- | ---------- | --------- | ------------------------ |
| L1   | 单项工程     | 项目      | 工程总体                 |
| L2   | 单位工程     | 表头解析    | 一般按 F1.1 表格式拆分        |
| L3   | 专业工程     | 专业字段识别 | 建筑/机电/装饰等              |
| L4   | 分部工程     | 名称或编码解析 | 如“脚手架工程”“砌筑工程”       |
| L5   | 分项工程     | 清单行     | 工程量可计量的最小实体          |
| L6   | 措施/规费/税金 | 清单类别    | 对应造价体系的 F1.2、F1.3 表等 |

### 2.4 WBS 的业务语义模型
- WBS 既是工程逻辑结构（施工组织分解），也是成本结构（造价归类）。
- 分部分项工程属于“工程量可计量结构”，措施/规费/税金属于“费用结构”，二者统一呈现于同一 WBS 框架。

---

## 第 3 章 清单分类体系（boq_category）完整规范

### 3.1 清单分类总览
系统定义六大类：

| 分类编码 | 中文名称 | 说明 | 示例 |
| --- | --- | --- | --- |
| boq | 分部分项工程 | 工程实体，可计量、可计价 | 土石方、砌筑、脚手架、钢筋、混凝土 |
| unit_measure | 单价措施项目 | 按工程量计价，与主项有依赖 | 垂直运输、混凝土养护、脚手架搭拆 |
| total_measure | 总价措施项目 | 按项计价，不与工程量挂钩 | 安全文明施工费、夜间施工费 |
| fee | 规费 | 政府规定的法定费用 | 社保费、工程排污费 |
| tax | 税金 | 按规费+工程费计算的税金 | 增值税 |
| other | 其他费用 | 业主自定义的补充费用 | 专家评审费、保险费 |

### 3.2 分类识别规则
系统通过三类信息自动识别清单类别：
- **Sheet 名**（最强信号）：包含“分部分项工程清单计价表/F.1.1”→boq；“单价措施项目清单计价表/F.1.2”→unit_measure；“总价措施项目清单计价表/F.1.3”→total_measure。
- **清单名称关键字**：脚手架/模板/垂直运输→unit_measure；安全文明/环保/降尘→total_measure；社保/排污/规费→fee；出现“税”或税率→tax。
- **编码规则（可选）**：01 开头建筑分部分项、02 装饰、03 机电；100X 措施；900X 规费/税金。

### 3.3 分类与 WBS 对应关系
| 分类 | WBS 层级 | 描述 |
| --- | --- | --- |
| boq | L5 分项工程 | 工程实体，影响工程量/进度分析 |
| unit_measure | L6 措施工程（单价） | 依赖主项工程量（如垂直运输） |
| total_measure | L6 措施工程（总价） | 与工程量无关的项目性费用 |
| fee | L7 规费结构 | 法定费用，一般按费率自动计算 |
| tax | L8 税金结构 | 自动从规费+造价基数计算 |
| other | L6/L7（可配置） | 企业或项目自定义费用 |

### 3.4 分类对成本流程的影响
| 分类 | 预算 | 合同 | 变更 | 支付 | 结算 |
| --- | --- | --- | --- | --- | --- |
| boq | ✓ | ✓ | ✓ | ✓ | ✓ |
| unit_measure | ✓ | ✓ | ✓ | ✓ | ✓ |
| total_measure | ✓ | ✓ | ✓ | 部分（按比例） | ✓ |
| fee | 系统计算 | 系统计算 | 限制人工变更 | 自动带入 | 自动 |
| tax | 自动计算 | 自动计算 | 自动调整 | 系统计算 | 自动 |
| other | ✓ | ✓ | ✓ | ✓ | ✓ |

### 3.5 模型字段定义
```python
boq_category = fields.Selection(
    [
        ("boq", "分部分项"),
        ("unit_measure", "单价措施项目"),
        ("total_measure", "总价措施项目"),
        ("fee", "规费"),
        ("tax", "税金"),
        ("other", "其他费用"),
    ],
    required=True,
    default="boq",
)
```

### 3.6 分类示例（真实导入）
- 分部分项：010101 土方工程、010202 模板工程、010301 混凝土工程
- 单价措施：外脚手架、垂直运输费
- 总价措施：安全文明施工费、夜间施工费
- 规费：社保费、工程排污费
- 税金：增值税（税金 = 造价合计 × 税率）

---

## 第 4 章 WBS 树生成算法设计

### 4.1 目标与原则
目标：把 project.boq.line（分部分项 + 措施 + 规费 + 税金 + 其他）自动生成 sc.project.structure 树，满足：
- 一次导入，多场景复用（预算/合同/结算/成本）
- 分区清晰：分部分项/措施/规费/税金各自独立
- 幂等可重复生成，不产生重复节点
- 可扩展：后续行业/企业自定义不破坏现有

原则：
- 分层抽象：结构层级与业务属性分离，用 structure_type + boq_category 组合表达
- 按单位工程聚合：所有类别挂各自单位工程下
- 叶子永远是清单项：底层节点对应 12 位清单编码或等价标识

### 4.2 输入与输出模型
输入（project.boq.line）：
- 定位：project_id, single_name, unit_name, major_name, section_type
- 编码：code, code_division, code_item
- 业务：boq_category（六类）、division_name
- 金额：quantity, amount
- 其他：sheet_index, sheet_name, remark, cost_item_id …

输出（sc.project.structure）：
- 现有结构类型：single / unit / major / division / subdivision / item
- 预留扩展（设计层面）：measure_unit / measure_total / fee / tax / other（根或组节点），便于费用类分区

### 4.3 目标树层级（按单位工程聚合）
- L1：项目（project_id 关联）
- L2：single（单项工程）
- L3：unit（单位工程）
- L4：major（专业工程，或措施/规费/税金根节点）
- L5：业务区块（division 或措施/规费/税金分组）
- L6：叶子（item；措施/规费/税金/其他的具体项）

约束：每条 boq.line 有且仅有一个 structure_id；上层 qty_total/amount_total 由子节点递归计算。

### 4.4 总体流程（action_generate_structure_from_boq）
1) 循环项目  
2) 读取项目清单  
3) 预加载已存在节点，构建 struct_map（防重复）  
4) 按 boq_category 分发构建：boq / unit_measure / total_measure / fee / tax / other  
5) 把清单行回写到叶子节点 structure_id  

### 4.5 分部分项（boq）算法（v2）
层级：single → unit → major → division → item  
分部去重：同单位工程 + 相同 code_division 只保留一个；名称优先 division_name > 备注 `[分部]xxx` > 编码。
伪代码摘要：
```
lines = filtered(boq, code_item 长度=12)
division_name_map = 预处理
struct_map = preload_existing()
for line in lines:
    node_single = get_or_create(single)
    node_unit   = get_or_create(unit, parent=single)
    node_major  = get_or_create(major, parent=unit, code/name=major_name/section_type/code_prof)
    node_div    = get_or_create_division(parent=unit，key=code_division)
    node_item   = get_or_create(item, parent=node_div, code=code_item, name=line.name)
    line.structure_id = node_item.id
```

### 4.6 单价措施（unit_measure）算法
层级：single → unit → measure_unit 根 → 措施分组 → item  
分组策略（多层兜底）：division_name > cost_item 名称 > 关键字（脚手架/模板/垂直运输/安全文明…）> sheet_name > “未分类措施”。
伪代码：
```
root = get_or_create(measure_unit, parent=unit, name="单价措施项目工程")
group = get_or_create(measure_unit, parent=root, name=derive_group(line))
item  = get_or_create(item, parent=group, code=line.code_item or line.code or line.name, name=line.name)
line.structure_id = item.id
```

### 4.7 总价措施（total_measure）算法
层级：single → unit → measure_total 根 → 分组 → item  
分组依据：名称关键字/成本项/Sheet 名；无则“未分类总价措施”。  
伪代码同单价措施，根节点换为 measure_total。

### 4.8 规费（fee）算法
层级：single → unit → fee 根 → 费种  
规则：规费通常无工程量概念，主要汇总金额；费种名称用 fee_type 或行名称；叶子可用 code 或名称。

### 4.9 税金（tax）算法
层级：single → unit → tax 根 → 税种/税率子项  
规则：税额建议由系统公式计算（税率×计税基数），导入金额可作为对照或初始值。

### 4.10 其他费用（other）算法
模式同 total_measure，结构类型用 other：single → unit → other 根 → 分组 → item。

### 4.11 幂等性与再生成
- 节点 key： (project_id, structure_type, dedup_parent_key, code_or_name)
- dedup_parent_key：分部节点按单位工程去重，其余按直接父节点
- 预加载所有节点填充 struct_map
- 默认只增不删；如需重建可提供“清空后重建”开关

### 4.12 实施路线（建议）
1. 先保持分部分项逻辑，过滤非 boq  
2. 扩展 structure_type 枚举（可先隐藏 UI）  
3. 为 unit_measure / total_measure / fee / tax / other 各自实现子过程  
4. 在 action_generate_structure_from_boq 内按类别分发  
5. 视图层按需要增加过滤/分组，structure_type 可仅后台使用  

---

## 第 5 章 基于专业版 WBS 的成本与进度控制模型（核心章）

### 5.1 WBS 是成本与进度的唯一载体
- 未绑定 WBS（structure_id）的业务数据，不纳入工程成本体系。
- 必须绑定 WBS 的对象：预算清单、合同清单、进度计量、签证/变更、成本台账、物资/分包计价；发票/支付建议绑定。
- 成本发生点落在叶子节点（item），上层节点仅做汇总。

### 5.2 三套成本线（Budget / Contract / Actual）
- 预算成本线：来源 BOQ + 措施/规费/税金计价；字段 `boq_qty/boq_price/boq_amount`；作用目标成本。
- 合同成本线：来源中标/变更后的合同清单；字段 `contract_qty/price/amount`；作用合同收入与计量基准。
- 实际成本线：来源物资入库、劳务、分包、采购、发票/支付；字段 `actual_qty/price/amount`。
- 统一映射到 WBS：`structure.budget_amount / contract_amount / actual_amount`。

### 5.3 WBS 节点的动态汇总（反向聚合）
- 采用 compute + store + depends：叶子变化自动向上汇总。
- 示例：
```python
@api.depends('child_ids.budget_amount','child_ids.contract_amount','child_ids.actual_amount')
def _compute_totals(self):
    for rec in self:
        rec.budget_amount = sum(rec.child_ids.mapped('budget_amount'))
        rec.contract_amount = sum(rec.child_ids.mapped('contract_amount'))
        rec.actual_amount = sum(rec.child_ids.mapped('actual_amount'))
```

### 5.4 进度计量模型（工程量驱动成本）
- 每条进度计量必须绑定 WBS 叶子：
```python
structure_id = fields.Many2one('sc.project.structure', required=True)
qty = fields.Float('本期工程量')
qty_cumulative = fields.Float(compute='_compute_cum')
amount = fields.Float(compute='_compute_amount')  # amount = qty * contract_price
```
- 本期/累计产值可推送到进度报表、合同产值、现金流、成本应计。

### 5.5 成本台账模型（Actual Cost Ledger）
- 每笔成本必须可追溯到 WBS 叶子：
```python
structure_id = fields.Many2one('sc.project.structure', required=True)
qty = fields.Float()
price = fields.Float()
amount = fields.Float(compute='_compute_amount')  # amount = qty * price
```
- 自动滚入 `actual_amount`，递归向上汇总。

### 5.6 三条成本线的对比报表
1) 预算 vs 合同（招投标偏差）：预算、合同、差额、偏差率  
2) 合同 vs 结算（变更管理）：已批变更、未批变更、合同价 vs 结算价差额  
3) 预算 vs 实际（成本偏差）：预算、实际、完成率、偏差、完工预测 EAC = AC + (预算 / 完成比例)

### 5.7 成本预警与智能提示（AI 扩展）
- 偏高节点原因诊断、超支趋势提醒、进度驱动现金流预测、超支 TopN 节点。
- 关键数据：WBS 树 + 预算/合同/实际 + 进度计量。

### 5.8 统一模型驱动全生命周期
- 从预算 → 合同 → 进度 → 成本 → 结算 → 决算的统一数据结构。
- 同一棵 WBS 树：可汇总、可对比、可预测、可扩展智能分析。

---

## 第 6 章 项目动态成本控制体系（Dynamic Cost Control）

### 6.1 六条“控制线”
| 控制线 | 说明 |
| --- | --- |
| 预算成本线（Budget） | 初始目标成本 |
| 合同成本线（Contract） | 合同签订后的基线 |
| 结算成本线（Settlement Target） | 变更多次调整形成的动态成本线 |
| 计划成本线（Planned Cost） | 进度计划对应的预期成本消耗 |
| 实际成本线（Actual Cost） | 已真实发生的费用 |
| 完工预测成本线（EAC） | 系统智能预测的最终成本 |

### 6.2 动态成本核心公式
- 成本偏差 CV：`CV = 预算成本 - 实际成本`
- 进度偏差 SV：`SV = EV - PV` （EV 挣值 = 完成量 × 合同单价）
- 完工预测 EAC：`EAC = AC + (BAC - EV) / CPI`，其中 CPI = EV / AC
- 成本趋势 TCPI：`TCPI = (BAC - EV) / (预算剩余可用成本)`

### 6.3 成本数据流
清单导入 → 生成预算线 → 合同签订 → 变更签证（调整合同/结算线）→ 进度计量（产值/挣值）→ 物资/劳务/分包/支付（实际成本）→ 更新 EAC。  
所有变化回写 WBS，递归汇总，更新项目经济指标。

### 6.4 变更管理（Change Management）
- 变更类型：设计变更、现场签证、工程量偏差、单价调整、措施费调整、合同补充条款。
- 每个变更必须绑定 `structure_id`（清单节点）；变更金额/工程量自动影响合同线与结算线。
- 动态合同价 = 合同原价 + 已批准变更金额。

### 6.5 成本分析仪表盘（Dashboard）
- 全局指标：预算/合同/变更/实际/EAC/CV/CPI。
- 各专业趋势：预算、实际、进度完成量、完工预测。
- 风险预警：超预算节点、单价异常、工程量偏差>10%、CPI<0.8、进度延误。

### 6.6 AI 驱动洞察
- 自动识别成本失控原因：材料涨价、工程量异常、劳务超耗、改签延期、分包低效等。
- 自动预测盈亏：基于 AC/EV/CPI/SPI，输出预计最终成本与风险节点。

### 6.7 全生命周期成本视图
| 阶段 | 依据 | 输出 |
| --- | --- | --- |
| 预算 | BOQ | 预算线 |
| 合同 | 中标价+变更 | 合同线 |
| 施工 | 进度计量+成本台账 | 实际线、EAC |
| 结算 | 变更+核量 | 结算线 |
| 决算 | 全部数据 | 盈亏分析、复盘 |

企业可一眼看到：“预算多少 → 合同多少 → 做到哪了 → 花了多少钱 → 最后会花多少钱”。

### 6.8 章末总结
- 建立六条控制线 + 公式体系（CV/SV/EAC/TCPI）。
- 把变更管理、进度计量、成本台账全部绑定 WBS。
- EAC 完工预测、仪表盘、AI 成本洞察，为企业提供动态决策力。

---

## 第 7 章 进度计划体系（Gantt + 依赖关系 + 工程量驱动）

### 7.1 三大核心模型
- 进度任务 ScTask：`structure_id` 必填，duration、start_date、end_date、progress。
- 任务依赖 ScTaskLink：支持 FS/SS/FF/SF + lag。
- 工程量驱动进度 ScProgressLine：前文已有，用于计量与完成比例。

### 7.2 WBS → 自动生成任务
- 按“任务粒度”参数生成：可到分部/分项/清单项。
- 建议默认生成：单项工程、单位工程、分部工程、分项工程；清单项按需开启精细化控制。

### 7.3 时标与自动排程
- 手工计划：start + duration → end；或 end - duration → start。
- 自动排程：拓扑排序 + CPM 关键路径：
  - 正向：ES = max(predecessor.EF + lag)，EF = ES + duration
  - 反向：LS = min(successor.LS - lag)，LF = LS + duration
  - 输出关键路径与浮动工期。

### 7.4 工程量驱动的真实进度
- 公式：`progress% = 累计完成工程量 / 预算工程量`
- 自动更新：甘特进度条、EV（挣值）、产值、成本预测 EAC。
- 让进度基于工程量而非主观百分比。

### 7.5 资源负荷分析（Resource Load）
- 资源类型：labor / machine / material / 施工面。
- 字段示例：`task_id, resource_type, resource_id, qty_per_day`。
- 生成资源曲线与负荷直方图，识别资源冲突（塔吊、挖机、劳务等）。

### 7.6 任务-计量-产值-成本联动
- 任务绑定 WBS → 获得预算工程量/合同单价。
- 计量 → progress% → EV → EAC：`EAC = AC + (BAC - EV) / CPI`。
- 产值驱动回款预测：应收进度款 = 本期产值 × 回款比例。
- 形成进度、产值、成本、风险的五位一体联动。

### 7.7 甘特图前端（实现建议）
- Vue3 + Canvas/SVG，接口 `/api/project/{id}/gantt`。
- 数据结构示例：
```json
{
  "tasks": [
    {
      "id": 101,
      "name": "基础垫层",
      "structure_id": 501,
      "start": "2026-01-10",
      "end": "2026-01-15",
      "duration": 5,
      "progress": 40,
      "dependencies": ["100:fs", "99:ss"]
    }
  ]
}
```

### 7.8 章末总结
- 任务自动化生成、依赖排程（CPM）、工程量驱动进度、资源负荷分析、甘特渲染、进度→产值→成本联动，构成专业级进度管控体系。

---

## 第 8 章 合同管理体系（主合同 + 分包合同 + 变更 + 计量支付）

### 8.1 三类合同模型
| 类型 | 说明 | 特点 |
| --- | --- | --- |
| 主合同 main | 与业主签订，决定产值收入 | 收入侧基线 |
| 分包合同 sub | 与施工队签订，最大成本来源 | 成本侧核心 |
| 采购合同 purchase | 材料/设备采购 | 直接形成成本台账 |

示例模型：
```python
class ScContract(models.Model):
    _name = "sc.contract"
    name = fields.Char()
    type = fields.Selection([("main","主合同"),("sub","分包"),("purchase","采购")])
    project_id = fields.Many2one("project.project", required=True)
    vendor_id = fields.Many2one("res.partner")
    amount = fields.Float("合同总价")
    version = fields.Char("合同版本")
```

### 8.2 合同清单绑定 WBS（关键）
合同 = 清单 = WBS 结构：
```python
class ScContractItem(models.Model):
    _name = "sc.contract.item"
    contract_id = fields.Many2one("sc.contract", required=True)
    structure_id = fields.Many2one("sc.project.structure", required=True)
    qty = fields.Float()
    price = fields.Float()
    amount = fields.Float(compute="_compute_amount")
```
意义：产值统计、变更落点、计量自动算产值、主分包对比、结算核对、风险定位。

### 8.3 合同变更体系（Dynamic Contract Price）
- 变更登记：必须绑定 structure_id，记录 qty_change/price_change/amount_change，reason（design/site/quantity/price/other），状态 draft/submitted/approved/rejected。
- 变更审核：流程 draft → submitted → approved → contract_updated（可扩展工作流）。
- 回写合同：批准后更新 contract_item（qty/price/amount），并更新节点/项目 contract_amount，形成“动态合同价”。

### 8.4 计量与支付体系（产值管理）
- 业主计量（主合同）：
```python
contract_id, period, structure_id, qty, amount  # amount = qty * contract_price
```
- 分包计量（分包合同）：同样绑定 structure_id，用于主分包差额、成本偏差、分包成本占比（Contract Yield Ratio）。
- 支付/回款：合同金额 → 计量产值 → 应付/应收 → 已付/已收 → 剩余；财务可见现金流与拖欠。

### 8.5 合同风险分析
- 超预算：actual_cost > budget_cost
- 超合同：actual_cost > contract_amount
- 进度偏差影响产值：EV < PV
- 变更未签：未批变更金额/合同金额 > 10%
- 回款偏慢：累计回款/累计完成产值 < 80%
- 分包成本失控：分包合同 + 已付 > 主合同金额  
→ 生成风险热力图（按 WBS 节点）。

### 8.6 合同体系与 WBS 融合
统一链路：
```
WBS
 → 预算结构
 → 合同结构
 → 变更结构
 → 进度计量（产值）
 → 分包计量（成本）
 → 支付 & 回款
 → 动态成本预测（EAC）
```

### 8.7 章末总结
- 主合同/分包/采购合同全覆盖
- 合同清单强绑定 WBS
- 变更管理与动态合同价
- 计量（产值）与支付/回款
- 风险分析与热力图  
形成企业级、可控、可回溯的合同管理闭环。

---

## 第 9 章 成本台账体系（Cost Ledger Management）

### 9.1 核心原则：成本按 WBS 归集
- 每笔成本必须绑定：project_id、structure_id、cost_item_id（成本科目）、可选 contract_id、boq_line_id。
- 目的：看清每个节点的实际成本、预算差额、合同差额、风险点。

### 9.2 成本台账主模型
```python
class ScCostLedger(models.Model):
    _name = "sc.cost.ledger"
    project_id = fields.Many2one("project.project", required=True)
    structure_id = fields.Many2one("sc.project.structure")
    cost_item_id = fields.Many2one("sc.dictionary")   # 成本科目
    contract_id = fields.Many2one("sc.contract")      # 可选
    boq_line_id = fields.Many2one("project.boq.line") # 可选
    type = fields.Selection([
        ("material","材料"),("subcontract","分包"),
        ("labor","人工"),("equipment","机械"),("other","其他")
    ], required=True)
    name = fields.Char()
    amount = fields.Float(required=True)
    date = fields.Date(required=True)
    source_document = fields.Char()
    vendor_id = fields.Many2one("res.partner")
```

### 9.3 成本来源 1：材料成本自动归集
- 采购合同锁价 → 入库单按收料数量 × 采购单价入账；入库单选择 structure_id。
- 出库到结构节点：出库单含 structure_id / boq_line_id / 数量 / 成本价 → 自动写台账。
- 项目级加权平均价：`平均价 = (上期结存金额 + 本期入库金额) / (上期结存数量 + 本期入库数量)`，出库金额 = 出库量 × 平均价。

### 9.4 成本来源 2：分包成本
- 分包计量：金额 = 数量 × 分包单价；自动写台账 type=subcontract，绑定 structure_id、contract_id、boq_line_id。

### 9.5 成本来源 3：人工费台账
- 劳务分包按产值计费 → 计入分包成本。
- 自营劳务工资导入：工人/工种/工时(或量)/金额/structure_id；台账 type=labor。

### 9.6 成本来源 4：机械费台账
- 机械台班：机械类型、台班数量、单价、structure_id → 台账 type=equipment。

### 9.7 成本汇总（WBS 成本聚合）
- 节点直接成本：ledger where structure_id=node。
- 节点累计成本：自身直接成本 + 子节点成本（递归）。
- 字段可扩展：`cost_total = fields.Float(compute="_compute_cost_total")`。

### 9.8 成本偏差与绩效
- 成本偏差 CV：`CV = 预算成本 - 实际成本`
- 成本绩效 CPI：`CPI = 预算成本 / 实际成本`
- 完工预测 EAC：`EAC = 实际成本 + (剩余工程量 × 合理单价)`
- 支持挣值分析（EVA）：结合进度 EV/PV。

### 9.9 成本风险预警
- Actual > Budget（超预算）
- Actual > Contract Amount（亏损风险）
- 材料异常消耗：材料量 > 清单量 × 系数
- 分包单价异常：分包单价 > 主合同单价
- 人工/机械占比异常
- 风险分级：绿/黄/红/紫；展示成本风险地图、瀑布图、周度曲线。

### 9.10 成本驾驶舱（Dashboard）
- 指标：总预算、总成本、CV、EAC、分包/材料/人工/机械占比。
- 图表：WBS 成本树、构成饼图、成本趋势折线、预算 vs 实际柱状、节点热力图。
- 联动：点节点 → 过滤材料出库、分包计量、工资、机械台班等台账。

### 9.11 章末总结
- 统一成本台账模型，覆盖材料/分包/人工/机械/其他。
- 成本按 WBS 归集；预算/合同/实际三算对比；CV/CPI/EAC。
- 成本风险雷达与驾驶舱，形成项目成本精细化、动态化、可预警的管理体系。

---

## 第 10 章 项目进度管理体系（Progress & Earned Value）

### 10.1 进度数据三来源
- 计划进度 Baseline（甘特/节点计划）→ PV 计划值
- 实际进度 Actual（工程量计量）→ EV 挣值
- 成本实际 AC（成本台账）→ AC

### 10.2 进度核心模型（绑定 WBS）
```python
class ScProgressEntry(models.Model):
    _name = "sc.progress.entry"
    project_id = fields.Many2one("project.project", required=True)
    structure_id = fields.Many2one("sc.project.structure", required=True)
    boq_line_id = fields.Many2one("project.boq.line")  # 可选
    date = fields.Date(required=True)
    quantity_done = fields.Float("本期工程量")
    quantity_cum = fields.Float("累计工程量")
    percent = fields.Float("本期%")
    percent_cum = fields.Float("累计%")
    amount_done = fields.Float(compute="_compute_amount")
    amount_cum = fields.Float(compute="_compute_amount")
```
产值自动：`amount = quantity_done × 合同单价`

### 10.3 工程量驱动产值
- 计量工程量 → 本期/累计产值；合同单价来自绑定的合同清单/WBS。

### 10.4 计划进度（Baseline）
- 甘特计划：`structure_id, start_date, end_date, planned_qty/percent`。
- 产值计划（按期）：`structure_id, period(YYYY-MM), planned_qty, planned_amount` → PV。

### 10.5 挣值管理（EVMS）
- 核心值：EV = 累计产值；PV = 累计计划产值；AC = 成本累计。
- 指标：
  - SV = EV - PV
  - CV = EV - AC
  - SPI = EV / PV
  - CPI = EV / AC
- 完工预测 EAC：
  - A) EAC = 总预算 / CPI
  - B) EAC = AC + (BAC - EV) / (CPI × SPI)
  - C) 可扩展按人工/材料趋势。

### 10.6 进度预警
- SPI < 1 滞后；30 天无进度；EV 与计量差异 > 20%；AC 高但 EV 低；回款率 < 产值率 - 20%。
- 全部绑定结构节点，自动提示。

### 10.7 可视化
- 甘特图（计划/实际/进度%）。
- S 曲线：PV / EV / AC 三曲线。
- WBS 进度热力图：绿/黄/红。

### 10.8 进度驾驶舱
- 指标：完成率、本期/累计产值、SPI/CPI、进度偏差、EAC、剩余产值。
- 图表：PV/EV/AC 曲线、WBS 树、甘特、产值柱状、进度风险雷达。

### 10.9 章末总结
- 工程量进度记录 → 自动产值
- 甘特计划与节点计划 → PV
- EVMS 全指标（SV/CV/SPI/CPI）+ EAC
- 滞后预警 + 可视化（甘特/S 曲线/热力图）
- 全流程基于 WBS 联动预算、合同、成本，形成黄金级进度管控体系。

---

## 第 11 章 质量与安全管理体系（Quality & Safety）

### 11.1 质量管理架构
- 核心事件：质量检查（Inspection）、质量问题/NCR（Issue）、整改（Rectification）、验收（Acceptance）。
- 全部绑定：project_id、structure_id(WBS)、responsible_user、deadline、status。

### 11.2 质量检查（Inspection）
```python
class ScQualityInspection(models.Model):
    _name = "sc.quality.inspection"
    project_id = fields.Many2one("project.project", required=True)
    structure_id = fields.Many2one("sc.project.structure")
    inspector_id = fields.Many2one("res.users")
    inspection_type = fields.Selection([
        ("routine","日常"),("special","专项"),("third_party","第三方"),("material","材料进场")
    ])
    date = fields.Date()
    result = fields.Selection([("ok","合格"),("issue","存在问题")])
    notes = fields.Text()
```
结果为“issue”自动生成质量问题。

### 11.3 质量问题（Issue/NCR）
```python
class ScQualityIssue(models.Model):
    _name = "sc.quality.issue"
    project_id = fields.Many2one("project.project", required=True)
    structure_id = fields.Many2one("sc.project.structure")
    description = fields.Text()
    issue_type = fields.Selection([...])
    severity = fields.Selection([("low","一般"),("medium","较严重"),("high","严重"),("critical","重大事故")])
    responsible_user = fields.Many2one("res.users")
    deadline = fields.Date()
    status = fields.Selection([("open","未整改"),("in_progress","整改中"),("review","待复检"),("closed","已关闭")], default="open")
```
每个 issue 必须绑定 WBS，便于按工序/分部统计。

### 11.4 整改闭环
```python
class ScQualityRectification(models.Model):
    _name = "sc.quality.rectification"
    issue_id = fields.Many2one("sc.quality.issue", required=True)
    responsible_user = fields.Many2one("res.users")
    rectification_notes = fields.Text()
    rectification_date = fields.Date()
```
流程：发现 → 通知 → 整改 → 复检 → 关闭。

### 11.5 验收体系
五类验收：工序、分项、分部、单位工程、竣工；与 WBS 层级天然对应。
```python
acceptance_type = fields.Selection([
    ("process","工序"),("subdivision","分项"),("division","分部"),
    ("unit","单位工程"),("project","竣工")
])
result: pass/fail，绑定 structure_id。
```

### 11.6 安全管理
- 安全检查 ScSafetyInspection（日期、inspector、issue_count、notes、structure_id）。
- 隐患 ScSafetyIssue（description、severity、status、deadline、responsible_user），流程同整改闭环。
- 事故上报：描述、受伤情况、经济损失、原因、责任、纠正措施。
- 安全教育/培训、危险源辨识（JSA）可扩展，全部绑定 WBS。

### 11.7 质量与安全责任矩阵
```python
class ScQSMasterResponsibility(models.Model):
    _name = "sc.qs.responsibility"
    structure_id = fields.Many2one("sc.project.structure")
    quality_user_id = fields.Many2one("res.users")
    safety_user_id = fields.Many2one("res.users")
    inspector_id = fields.Many2one("res.users")
```
节点责任人清晰，问题自动通知到人。

### 11.8 质量与安全台账（QS Ledger）
- 统一记录：事件类型（检查/问题/验收/安全检查/隐患）、WBS 节点、日期、严重度、是否关闭。
- 支持按结构汇总：检查次数、问题数量、隐患闭环率、事故分布。

### 11.9 QS 驾驶舱
- 指标：本月质检次数、安全检查次数、闭环率、未整改数、严重问题数、隐患闭环率、验收合格率、最近事故。
- 图表：质量问题趋势/热力图、安全隐患趋势/热力图、验收通过率、返工成本趋势。
- 与 WBS/进度/成本/合同联动，形成完整运营视角。

### 11.10 章末总结
- 质量检查、NCR、整改闭环、各层级验收、安全检查/隐患/事故上报、责任矩阵、台账与驾驶舱，全部以 WBS 为主线，构建覆盖全生命周期的质安管理能力。

---

## 第 12 章 工程“五算对比体系”设计

### 12.1 五算全景
五算 = 概算 Estimate / 预算 Budget / 合同 Contract / 实际 Actual / 决算 Settlement。目标：随时回答“花了多少、该花多少、还要花多少、有没有亏、亏在哪”。

### 12.2 关键模型与绑定
- 预算：`budget_line` 按 WBS，`amount_cost_target/amount_revenue_target`。
- 合同：收入/分包/采购合同，合同清单绑定 WBS。
- 实际成本：`sc.cost.ledger`，必须有 `structure_id`。
- 决算：`settlement_items` 绑定 BOQ/WBS。
- 清单 BOQ：提供工程量与类别（分部分项/单价措施/总价措施）。
- **统一绑定 WBS（structure_id）** 以对齐维度。

### 12.3 五算对比模型（示例）
```python
class WBSFiveCalculation(models.Model):
    _name = "wbs.five.calc"
    structure_id = fields.Many2one("sc.project.structure")
    estimate_amount = fields.Float()
    budget_amount = fields.Float()
    contract_amount = fields.Float()
    settlement_amount = fields.Float()
    actual_amount = fields.Float()
    cost_variance = fields.Float()    # 预算 - 实际
    profit_variance = fields.Float()  # 合同 - 实际
```
- 概算：用户录入或按清单单价估算（可选）。  
- 预算：预算行按结构聚合。  
- 合同：合同清单按结构聚合（收入侧）。  
- 实际：成本台账按结构聚合。  
- 决算：结算清单按结构聚合。  
- 偏差：`cost_variance = budget - actual`；`profit_variance = contract - actual`。

### 12.4 五算对比界面
项目页新增“五算对比”标签，树形同 WBS：
| WBS | 预算 | 合同收入 | 决算 | 实际 | 成本偏差 | 利润偏差 |
支持层级汇总、展开/折叠、节点钻取。

### 12.5 预警规则
- 实际 > 预算：黄色；超 10%：红色。
- 合同 < 实际：亏损红色。
- 决算 < 合同：收入减少黄灯。
- 质量问题多 → 预估下调（可选 AI 调整）。

### 12.6 AI 分析（预留能力）
- 成本风险预测：趋势超支、Top 风险节点。
- 利润预测：最终盈利/风险成本估计。
- 质量与成本关联：质量问题↑ → 返工风险提示。

### 12.7 与 BOQ/措施清单的集成
- 分部分项 → 分项工程；单价措施/总价措施 → 措施工程节点；全部金额归集到对应 WBS，防止丢项。

### 12.8 章末总结
- 五算模型 + 全金额 WBS 绑定 + 对比算法 + 预警 + 质安/进度联动 + AI 预测预留，升级为企业级决策平台。

---

## 第 13 章 工程进度（计量）体系设计

### 13.1 两种主流进度模型
- 形象进度（节点法）：基础/主体/封顶/装修等阶段性达成，用于月报和宏观管理。
- 工程量进度（产值法）：按 BOQ 计量，直接对应主合同/分包合同产值，用于计量与经营核心。

### 13.2 核心模型
- 形象进度节点：ScProgressMilestone（节点名称、计划/实际日期、进度%）。
- 工程量计量：ScProgressQty（project/contract/structure_id/boq_line_id，qty_done、qty_cum、amount_done 自动 = qty × 合同单价）。
- WBS 进度汇总：ScProgressWbs（structure_id，progress_rate = 累计产值 / 该节点合同金额，递归汇总）。

### 13.3 进度记录来源
- A 分包进度填报 → 审核后自动生成计量记录、可选生成成本台账、更新 WBS 进度。
- B 监理/项目部直接录入工程量 → 自动回写 WBS。
- C 形象进度比例 → 可按比例生成对应工程量/产值（可选）。

### 13.4 进度与合同联动
核心：产值 = 完成工程量 × 合同单价。  
主合同产值（收入） vs 分包产值（成本）逐 WBS 对比，得出毛利曲线。示例：混凝土 C30 主价 450、分包 320、完成 120 m³ → 主合同产值 54,000，分包产值 38,400，毛利 15,600。

### 13.5 进度与成本联动（EVA）
- PV 计划产值，EV 已完产值，AC 实际成本。
- CV = EV - AC；SV = EV - PV；CPI = EV / AC；SPI = EV / PV。
- 支撑 AI 预测超支/滞后，定位异常 WBS 节点。

### 13.6 前端页面结构
1) 形象进度视图：甘特/节点条，状态色（正常/延期/严重延期）。  
2) 清单进度视图：清单编码、名称、合同量、累计完成、 本期产值、完成比例、WBS 路径。  
3) WBS 进度树：单位→专业→分部→分项→清单，展示各层完成率。

### 13.7 AI 智能诊断（预留）
- 进度滞后预测、产值不足预警、成本超支趋势、分包履约评估、赶工导致质量风险提示。

### 13.8 章末总结
- 形象进度 + 产值法并存，WBS 自动汇总；与合同/预算/成本联动，支持 EVA、预警、甘特/S 曲线/树形多视图，具备工业级进度管理基础。

---

## 第 14 章 工程质量管理体系设计（与进度/成本联动）

### 14.1 三个核心对象
- 检查（Inspection）：监理/项目部/第三方/公司巡检。
- 问题（Quality Issue/NCR）：蜂窝麻面、焊接不合格、砌体砂浆不足等。
- 整改（Rectification）：分包整改 → 质量员复验 → 关闭。
全部绑定 WBS。

### 14.2 质量问题模型
```python
class ScQualityIssue(models.Model):
    _name = "sc.quality.issue"
    project_id = fields.Many2one("project.project", required=True)
    structure_id = fields.Many2one("sc.project.structure", required=True)  # WBS
    boq_line_id = fields.Many2one("project.boq.line")  # 可选
    name = fields.Char()
    description = fields.Text()
    level = fields.Selection([("minor","一般"),("major","严重"),("critical","重大")])
    source = fields.Selection(["supervision","project","company","third"])
    state = fields.Selection([("open","待整改"),("repair","整改中"),("review","待复检"),("closed","已完成")])
```
关键：必须有 structure_id，必要时指向具体清单项。

### 14.3 整改闭环流程
open → repair → review → closed；复检不通过可 review→repair。按钮驱动状态流转。

### 14.4 质量与进度联动
- 规则1：存在 open/repair 问题的节点禁止计量（EV=0）。
- 规则2：返工成本预测：返工量×人工+材料+间接费 → 写入成本预测。
- 规则3：重大问题过多（critical>3 或高密度）→ SPI 下降，影响进度预测。

### 14.5 质量与合同联动
- 扣款：`quality_penalty = penalty_rate × issue_level_factor`，写入分包合同。
- 工期调整：返工影响关键路径时可调整工期（可选）。
- 争议/索赔：质量负担、工程量确认争议接入合同变更模块。

### 14.6 质量风险模型
风险分值 = 未关闭问题数×系数1 + 严重问题数×系数2 + 历史频次×系数3 + 分包履约能力×系数4。  
0–30 绿，30–70 黄，70–100 红。影响工期预测、返工成本、安全等级、考核。

### 14.7 AI 质量诊断
- 问题聚类：高发分项/分部、施工队、问题类型预测。
- 质量→成本：返工费用预测、分包扣减建议、质量改进 ROI。
- 自动质量周报/月报：新增/闭环效率、风险分布、返工风险节点、趋势预测。

### 14.8 前端 UI 建议
- 检查/问题列表：WBS、清单、严重度、状态、分包、整改时限；按专业/分部/施工队/严重度筛选。
- 问题详情：图片/语音/视频、位置、关联清单、整改按钮。
- 质量地图：WBS 树热力色（红 critical / 黄 major / 蓝 minor）。

### 14.9 章末总结
- 质量检查/问题/整改闭环，强绑定 WBS；质量对进度计量、成本预测、合同扣款联动；风险与 AI 诊断、质量地图和报告能力，形成企业级质量管理体系。

---

## 第 15 章 安全管理体系设计（隐患、闭环、风险、AI）

### 15.1 三要素
- 危险源（Hazard）：高处、吊装、用电、临边洞口、深基坑等，须绑定 WBS。
- 隐患（Issue）：检查发现的事件。
- 整改（Rectification）：open → repair → review → closed，强调时效。

### 15.2 安全隐患模型
```python
class ScSafetyIssue(models.Model):
    _name = "sc.safety.issue"
    project_id = fields.Many2one("project.project", required=True)
    structure_id = fields.Many2one("sc.project.structure", required=True)
    task_id = fields.Many2one("project.task")           # 可选
    subcontractor_id = fields.Many2one("sc.subcontractor")
    hazard_type = fields.Selection([
        ("height","高处作业"),("lifting","起重吊装"),("electricity","临时用电"),
        ("collapse","坍塌风险"),("fire","火灾风险"),("equipment","机械伤害"),("other","其他"),
    ])
    description = fields.Text()
    level = fields.Selection([("general","一般"),("major","重大"),("critical","特别重大")])
    state = fields.Selection([("open","未整改"),("repair","整改中"),("review","待复检"),("closed","已关闭")], default="open")
    deadline = fields.Datetime("整改时限")
```
要点：必须有 structure_id；可绑定分包/任务。

### 15.3 危险源模型
```python
class ScHazardSource(models.Model):
    _name = "sc.hazard.source"
    project_id = fields.Many2one("project.project")
    structure_id = fields.Many2one("sc.project.structure")
    risk_level = fields.Selection([("low","低"),("medium","中"),("high","高")])
    description = fields.Text()
    control_measures = fields.Text()
```

### 15.4 整改闭环与超期提醒
open → repair → review → closed；超期自动消息提醒，首页标红，分包考核扣分；可用 cron 检查 deadline。

### 15.5 风险矩阵 L×S
风险 R = L(可能性1–4) × S(严重度1–4)。  
R 1–4 绿，5–8 黄，9–12 橙，13–16 红。用于 WBS 风险热力图与态势看板。

### 15.6 安全与 WBS/进度/成本联动
- 重大隐患未闭合 → 节点禁止施工/计量。
- 隐患多 → SPI 下降，工期预测延迟。
- 停工整改 → 记录“安全停工成本”（人工/机械停机/管理/间接费）写入成本预测。

### 15.7 安全教育与三级交底（可选）
- 公司/项目/班组三级教育，记录人员、时间、内容、照片，支持考试与教育日志 PDF。
- 分包问题频发可自动触发再教育。

### 15.8 安全投入与成本
- PPE、防护、检测等安全费用；按隐患类型 × 参考系数预测安全投入，写入成本预测。

### 15.9 AI 安全能力
- 风险热力：高风险分项/分部排行。
- 下周事故类型预测：高处坠落、起重伤害、临电风险概率。
- 分包安全等级：按隐患数/闭环速度/重大占比/停工次数 → A/B/C/D。
- 自动安全周报/月报：隐患趋势、闭环率、分布、投入、下周预测、重大隐患处理。

### 15.10 前端页面
- 隐患列表：按分包/WBS/专业/类型/等级/状态过滤。
- 隐患详情：照片/视频、责任人、提醒、整改/复检记录、状态按钮。
- WBS 安全热力图：红(重大)/橙(高)/黄(中)/绿(低)。

### 15.11 章末总结
- 隐患管理与整改闭环、风险矩阵、教育交底、安全投入、与进度/成本/任务的联动、AI 分析与热力图，形成行业顶级的安全管理体系。


---

## 第 16 章 成本管理体系（预算/合同/结算/台账/预测/五算对比）

### 16.1 总体目标
- 造价全过程管理：预算（标前/控制价）→ 合同（标后）→ 过程台账 → 预测 → 结算。
- 成本实时透明：目标成本、承诺成本、实际成本、预计成本全量可视。
- 成本结构与 WBS 完全同步，收入与成本双向映射，实时计算盈利能力。
- 预留 AI：成本偏差、利润趋势、风险预警与 EAC 预测。

### 16.2 成本的“五算体系”
- 预算算量（标前预算/内部预算）→ 预算模块 Budget
- 合同算量（主合同）→ 主合同模块 Contract
- 计划算量（施工计划）→ WBS/任务模块
- 实际算量（产值计量）→ 进度模块 Progress
- 结算算量（最终结算）→ 结算模块 Settlement  
> 关键：全部绑定 WBS 维度，支持统一对比。

### 16.3 成本的四类状态
- 目标成本 Target Cost：项目启动控制线
- 承诺成本 Committed Cost：已签合同未完全执行
- 已发生成本 Actual Cost：台账/付款/入库
- 预计成本 Forecast Cost：后续预估（未发生）  
> 最终成本 = Actual + Forecast

### 16.4 成本中心模型（按 WBS 归集）
```python
class ScCostCenter(models.Model):
    _name = "sc.cost.center"
    project_id = fields.Many2one("project.project")
    structure_id = fields.Many2one("sc.project.structure", required=True)
    target_cost = fields.Float()
    committed_cost = fields.Float()
    actual_cost = fields.Float()
    forecast_cost = fields.Float()
    gross_margin = fields.Float(compute="_compute_margin")
```
示例公式：`gross_margin = (预算产值 - (actual_cost + forecast_cost)) / 预算产值`

### 16.5 预算成本（Budget）
```python
class ScBudgetLine(models.Model):
    _name = "sc.budget.line"
    project_id = fields.Many2one("project.project")
    structure_id = fields.Many2one("sc.project.structure")
    cost_item_id = fields.Many2one("sc.dictionary")
    quantity = fields.Float()
    price = fields.Float()
    amount = fields.Float()
```
预算按 WBS 层层汇总。

### 16.6 合同成本（分包合同）
```python
class ScSubcontractLine(models.Model):
    _name = "sc.subcontract.line"
    contract_id = fields.Many2one("sc.subcontract")
    structure_id = fields.Many2one("sc.project.structure")
    boq_line_id = fields.Many2one("project.boq.line")
    quantity = fields.Float()
    price = fields.Float()
    amount = fields.Float()
```
合同行写入承诺成本（committed_cost），并可按 WBS/清单/成本科目关联。

### 16.7 过程成本（台账）
```python
class ScCostLedger(models.Model):
    _name = "sc.cost.ledger"
    project_id = fields.Many2one("project.project")
    structure_id = fields.Many2one("sc.project.structure")
    cost_item_id = fields.Many2one("sc.dictionary")
    amount = fields.Float("本期金额")
    date = fields.Date()
```
来源：材料出库、人工工资、机械台班、分包计量、费用报销等，直接写入 actual_cost。

### 16.8 预计成本（Forecast）
- 剩余工程量 × 合同单价（未完成部分）
- 质量问题返工成本
- 进度滞后赶工成本
- 安全停工/整改成本  
> `forecast_cost = 系统自动计算 + 用户调整`

### 16.9 实际成本与 ERP 集成
- 预留接口：进项/销项发票、付款、采购、库存入库/出库、费用报销。
- 现阶段可人工录入台账，后续无缝对接财务与供应链。

### 16.10 成本分析指标
- 预算/承诺/已发生/预计/完工成本（actual+forecast）
- 收入、成本、毛利、毛利率、利润趋势
- 按 WBS、专业、分包、成本科目多维分析。

### 16.11 与进度/质量联动
- 进度滞后 → 预计成本增加（赶工费）
- 质量问题 → 返工成本计入 forecast
- 安全事故/停工 → 人工损失/机械停机计入 forecast

### 16.12 五算对比大屏
- 表格：WBS | 预算算量 | 合同算量 | 计划算量 | 实际算量 | 结算算量 | 偏差
- 图表：算量偏差折线、单价对比柱状、成本趋势/利润预测曲线
- 树形视图：按 WBS 展开，层级汇总。

### 16.13 AI 成本分析
- EAC 预测：结合 CPI/SPI、分包履约、材料行情、质量/安全影响。
- 自动成本周报/月报：新增成本、偏差、分包排名、材料涨价预测、利润预测。
- 成本风险雷达：料/工/机/分包/管理费/间接费多维评分。

### 16.14 章末总结
- 预算、合同、结算、台账、预测、五算对比体系落地。
- 成本四状态 + 五算并行，全面绑定 WBS。
- 实时毛利/利润预测，风险预警，AI 预测能力预留。
- 与进度、质量、安全闭环联动，形成企业级经营决策核心。

---

## 第 17 章 进度 × 质量 × 安全 × 成本的一体化 AI 决策系统

### 17.1 四个孤岛痛点
- 进度（计划/产值/计量）、质量（检查/不合格/整改）、安全（隐患/事故/停工）、成本（预算/合同/台账/预测）彼此割裂，无法联动推理。

### 17.2 必须一体化的原因
- 进度滞后 → 赶工费↑ → 成本↑
- 安全隐患 → 停工 → 进度滞后 → 成本↑
- 质量返工 → 工程量减产 → 进度滞后 + 成本↑
- 成本压力 → 分包资金紧张 → 人员减少 → 进度滞后

### 17.3 一体化 AI 的核心方程
```
项目状态 = f(进度, 质量, 安全, 成本, 风险, 外部因素)
```
AI 目标输出：项目健康度评分、完工日期预测、完工成本预测（置信区间）、主要风险来源、优先级策略建议。

### 17.4 统一快照模型（ScProjectStatusSnapshot）
```python
class ScProjectStatusSnapshot(models.Model):
    _name = "sc.project.status.snapshot"
    project_id = fields.Many2one("project.project")
    progress_rate = fields.Float()
    progress_deviation = fields.Float()
    quality_defects = fields.Integer()
    quality_risk_score = fields.Float()
    safety_incidents = fields.Integer()
    safety_risk_score = fields.Float()
    cost_actual = fields.Float()
    cost_committed = fields.Float()
    cost_forecast = fields.Float()
    cost_deviation = fields.Float()
    wbs_critical_path_delay = fields.Float()
    subcontract_risk_score = fields.Float()
    ai_health_score = fields.Float()
    ai_risk_summary = fields.Text()
    ai_recommendation = fields.Html()
```
触发时机：进度/质量/安全/台账/分包计量更新即生成新快照，AI 读取标准化输入。

### 17.5 项目健康度的 8 个核心指标
- 进度健康：实际/计划、关键线路延误、S 曲线偏差。
- 产值健康（EVM）：CPI = EV/AC，SPI = EV/PV。
- 质量健康：不合格项数、重复整改率、关键工序评分、减产影响。
- 安全健康：隐患数、关闭率、违规次数、停工时长。
- 成本健康：目标/承诺/实际/预测偏差，分包成本、材料/人工波动。
- 资源健康：出勤、机械利用率、材料供应紧张度。
- 合同履约健康：分包完成率/计划、成本超支/付款风险、履约评分。
- 总风险健康：综合权重形成项目健康度 0–100。

### 17.6 完工日期预测（AI）
```
完工日期 = 今天 + (剩余产值 ÷ 日均产值预测)
```
日均产值由近 30 天学习，质量返工/安全停工/分包能力/机械利用率修正。

### 17.7 完工成本预测（AI EAC）
```
EAC = AC
    + 预计工程量 × 单价预测
    + 风险成本预测
    + 工期延误赶工费预测
```
权重示例：进度偏差40% + 分包能力20% + 材料行情20% + 安全质量10% + 历史资源10%；输出置信区间。

### 17.8 AI 决策建议（行动清单）
- 本周三大风险（例：模板滞后、重复整改率高、分包资金压力）。
- 下周三大行动（增人/改排布/优先整改关键轴线/锁价采购）。
- 成本预警（超支幅度与来源：赶工、返工、材料）。
- 完工日期情景（保持现状 vs 两班倒）。
- 项目健康评分（例：72 分，黄色，风险点列表）。

### 17.9 智能驾驶舱呈现
- WBS 健康度热力树、项目状态雷达、五算对比、成本偏差趋势、完工预测曲线。
- AI 文本分析与建议（可折叠），适配晨会/大屏。

### 17.10 未来扩展接口
- BIM/IFC 绑定 WBS，构件产量与工序联动。
- IoT 接入（吊次、混凝土到场、环境、考勤）推理实际施工速度。
- 成本节奏控制（成本曲线偏离自动预警现金流缺口）。

### 17.11 小结
- 构建“进度-质量-安全-成本”四维一体的推理/预测/决策体系。
- 统一快照输入，AI 输出健康度、完工时间/成本预测、风险与行动建议。
- 可联动 BIM/IoT 与成本曲线，实现施工智能化的“驾驶舱”级能力。

---

## 第 18 章 专业版合同管理体系（收入 + 成本 + 风险闭环）

### 18.1 合同体系的四个层次
- 收入合同（主合同/补充协议）
- 成本合同（分包/采购/专业分包）
- 内部约定（内部责任书/内部承包）
- 结算协议（中间计量/竣工结算/终结协议）  
> 合同 2.0 = 合同元数据 + 价格结构 + 计量规则 + 支付条款 + 约束逻辑 + 风险标签

### 18.2 收入合同模型 ProjectRevenueContract
```python
class ProjectRevenueContract(models.Model):
    _name = "project.revenue.contract"
    name = fields.Char(required=True)
    contract_no = fields.Char(required=True, index=True)
    project_id = fields.Many2one("project.project", required=True)
    partner_id = fields.Many2one("res.partner", required=True)  # 业主
    sign_date = fields.Date()
    start_date = fields.Date()
    end_date = fields.Date()
    amount_untaxed = fields.Monetary()
    amount_tax = fields.Monetary()
    amount_total = fields.Monetary()
    currency_id = fields.Many2one("res.currency", related="project_id.company_currency_id", store=True)
    tax_rate = fields.Float()
    settle_type = fields.Selection([
        ("lump_sum","总价合同"),("unit_price","单价合同"),("cost_plus","成本加酬金"),("pc_sum","暂定价")
    ], default="unit_price")
    boq_version_id = fields.Many2one("project.boq.version")
    boq_lock = fields.Boolean()
    state = fields.Selection([
        ("draft","草稿"),("running","执行中"),("changed","变更中"),
        ("closed","已完结"),("cancelled","已作废")
    ], default="draft")
    change_count = fields.Integer(compute="_compute_change_stats", store=True)
    amount_changed = fields.Monetary(currency_field="currency_id", store=True)
    payment_term_id = fields.Many2one("account.payment.term")
    retention_rate = fields.Float()
    advance_rate = fields.Float()
    risk_level = fields.Selection([("low","低"),("medium","中"),("high","高")], default="medium")
    note = fields.Text()
    ai_risk_summary = fields.Text()
    ai_clause_hint = fields.Html()
```
- 关键：`boq_version_id` 绑定合同清单版本，`settle_type` 结构化计价方式，`risk_level/ai_*` 供 AI 条款分析。

#### 收入合同行 ProjectRevenueContractLine
```python
class ProjectRevenueContractLine(models.Model):
    _name = "project.revenue.contract.line"
    contract_id = fields.Many2one("project.revenue.contract", required=True, ondelete="cascade")
    project_id = fields.Many2one("project.project", related="contract_id.project_id", store=True)
    boq_line_id = fields.Many2one("project.boq.line")
    structure_id = fields.Many2one("sc.project.structure")
    code = fields.Char()
    name = fields.Char(required=True)
    spec = fields.Char()
    uom_id = fields.Many2one("uom.uom")
    quantity_contract = fields.Float()
    price_contract = fields.Float()
    amount_contract = fields.Monetary(currency_field="currency_id")
    quantity_settled = fields.Float(compute="_compute_settle_stats", store=True)
    amount_settled = fields.Monetary(currency_field="currency_id", compute="_compute_settle_stats", store=True)
    currency_id = fields.Many2one("res.currency", related="contract_id.currency_id", store=True)
    is_measure_item = fields.Boolean()
    cost_item_id = fields.Many2one("sc.dictionary", domain="[('type','=','cost_item')]")
    sequence = fields.Integer(default=10)
```
- 关键：`boq_line_id` 对齐清单，`structure_id` 挂接 WBS，结算累计字段供结算聚合。

### 18.3 成本合同体系（分包/采购/劳务/机械/服务）
```python
class ProjectCostContract(models.Model):
    _name = "project.cost.contract"
    name = fields.Char(required=True)
    contract_no = fields.Char(required=True, index=True)
    project_id = fields.Many2one("project.project", required=True)
    partner_id = fields.Many2one("res.partner", required=True)
    contract_type = fields.Selection([
        ("subcontract","专业分包"),("labour","劳务分包"),("material","材料采购"),
        ("machinery","机械租赁"),("service","专业服务")
    ], required=True, default="subcontract")
    sign_date = fields.Date()
    planned_start = fields.Date()
    planned_end = fields.Date()
    amount_untaxed = fields.Monetary()
    amount_tax = fields.Monetary()
    amount_total = fields.Monetary()
    currency_id = fields.Many2one("res.currency", related="project_id.company_currency_id", store=True)
    tax_rate = fields.Float()
    settle_logic = fields.Selection([
        ("by_boq","按 BOQ"),("by_wbs","按 WBS"),("by_lump_sum","总价包干"),
        ("by_schedule","按节点付款"),("by_time","按工日/工时")
    ], default="by_boq")
    retention_rate = fields.Float()
    advance_rate = fields.Float()
    payment_term_id = fields.Many2one("account.payment.term")
    state = fields.Selection([
        ("draft","草稿"),("running","执行中"),("suspended","已暂停"),
        ("closed","已完结"),("cancelled","已作废")
    ], default="draft")
    risk_level = fields.Selection([("low","低"),("medium","中"),("high","高")], default="medium")
    ai_risk_summary = fields.Text()
    ai_recommendation = fields.Html()
    wbs_scope_ids = fields.Many2many("sc.project.structure", string="承包范围(WBS)")
```
- 关键：`settle_logic` 结构化结算方式；`wbs_scope_ids` 定义分包承包范围，限制计量与问题归属。

#### 成本合同行 ProjectCostContractLine
```python
class ProjectCostContractLine(models.Model):
    _name = "project.cost.contract.line"
    contract_id = fields.Many2one("project.cost.contract", required=True, ondelete="cascade")
    project_id = fields.Many2one("project.project", related="contract_id.project_id", store=True)
    boq_line_id = fields.Many2one("project.boq.line")
    structure_id = fields.Many2one("sc.project.structure")
    code = fields.Char()
    name = fields.Char(required=True)
    spec = fields.Char()
    uom_id = fields.Many2one("uom.uom")
    quantity_contract = fields.Float()
    price_contract = fields.Float()
    amount_contract = fields.Monetary(currency_field="currency_id")
    quantity_exec = fields.Float(compute="_compute_exec_stats", store=True)
    amount_exec = fields.Monetary(currency_field="currency_id", compute="_compute_exec_stats", store=True)
    currency_id = fields.Many2one("res.currency", related="contract_id.currency_id", store=True)
    cost_item_id = fields.Many2one("sc.dictionary", domain="[('type','=','cost_item')]")
    is_temporary = fields.Boolean()
    is_measure_item = fields.Boolean()
    sequence = fields.Integer(default=10)
```
- 关键：`boq_line_id` 建立业主清单 ↔ 分包清单映射；`structure_id` 绑定 WBS；`cost_item_id` 打通台账维度。

### 18.4 结算体系（中间计量 / 竣工结算）
```python
class ProjectSettleOrder(models.Model):
    _name = "project.settle.order"
    name = fields.Char(required=True, copy=False)
    project_id = fields.Many2one("project.project", required=True)
    settle_type = fields.Selection([
        ("income_interim","收入中间结算"),("income_final","收入竣工结算"),
        ("cost_subcontract","分包结算"),("cost_material","材料结算")
    ], required=True)
    contract_id = fields.Many2one("project.revenue.contract")
    cost_contract_id = fields.Many2one("project.cost.contract")
    period_start = fields.Date()
    period_end = fields.Date()
    settle_date = fields.Date()
    amount_contract = fields.Monetary()
    amount_change = fields.Monetary()
    amount_other = fields.Monetary()
    amount_total = fields.Monetary()
    amount_tax = fields.Monetary()
    amount_total_tax = fields.Monetary()
    currency_id = fields.Many2one("res.currency", related="project_id.company_currency_id", store=True)
    state = fields.Selection([
        ("draft","草稿"),("submitted","已提交"),("confirmed","已确认"),
        ("done","已完结"),("cancel","已作废")
    ], default="draft")
    line_ids = fields.One2many("project.settle.order.line","order_id")
    ai_summary = fields.Html()
    ai_risk_hint = fields.Text()
```
结算行：
```python
class ProjectSettleOrderLine(models.Model):
    _name = "project.settle.order.line"
    order_id = fields.Many2one("project.settle.order", required=True, ondelete="cascade")
    project_id = fields.Many2one("project.project", related="order_id.project_id", store=True)
    contract_line_id = fields.Many2one("project.revenue.contract.line")
    cost_contract_line_id = fields.Many2one("project.cost.contract.line")
    boq_line_id = fields.Many2one("project.boq.line")
    structure_id = fields.Many2one("sc.project.structure")
    code = fields.Char()
    name = fields.Char()
    uom_id = fields.Many2one("uom.uom")
    qty_contract = fields.Float()
    qty_before = fields.Float()
    qty_current = fields.Float()
    qty_total = fields.Float()
    price = fields.Float()
    amount_current = fields.Monetary(currency_field="currency_id")
    amount_total = fields.Monetary(currency_field="currency_id")
    currency_id = fields.Many2one("res.currency", related="order_id.currency_id", store=True)
    is_change = fields.Boolean()
    remark = fields.Char()
```
- 价值：结算始终立足合同行，且对齐 BOQ/WBS，可直接做收入 vs 成本 vs 毛利/偏差分析。

### 18.5 合同变更体系（变更/签证/索赔）
```python
class ProjectContractChange(models.Model):
    _name = "project.contract.change"
    name = fields.Char(required=True)
    project_id = fields.Many2one("project.project", required=True)
    change_type = fields.Selection([("income","收入合同变更"),("cost","成本合同变更")], required=True)
    revenue_contract_id = fields.Many2one("project.revenue.contract")
    cost_contract_id = fields.Many2one("project.cost.contract")
    reason = fields.Selection([("design","设计变更"),("site","现场签证"),("material","材料变更"),("claim","索赔"),("other","其他")])
    description = fields.Text()
    amount_delta = fields.Monetary(currency_field="currency_id")
    currency_id = fields.Many2one("res.currency", related="project_id.company_currency_id", store=True)
    state = fields.Selection([("draft","草稿"),("submitted","已提交"),("approved","已批准"),("applied","已执行"),("cancel","已作废")], default="draft")
    line_ids = fields.One2many("project.contract.change.line","change_id")
    ai_risk_summary = fields.Text()
    ai_suggestion = fields.Html()
```
变更行：
```python
class ProjectContractChangeLine(models.Model):
    _name = "project.contract.change.line"
    change_id = fields.Many2one("project.contract.change", required=True, ondelete="cascade")
    project_id = fields.Many2one("project.project", related="change_id.project_id", store=True)
    revenue_line_id = fields.Many2one("project.revenue.contract.line")
    cost_line_id = fields.Many2one("project.cost.contract.line")
    boq_line_id = fields.Many2one("project.boq.line")
    structure_id = fields.Many2one("sc.project.structure")
    change_mode = fields.Selection([
        ("add","新增"),("delete","删除"),
        ("modify_qty","调工程量"),("modify_price","调单价")
    ], required=True)
    qty_before = fields.Float()
    qty_after = fields.Float()
    price_before = fields.Float()
    price_after = fields.Float()
    amount_before = fields.Monetary(currency_field="currency_id")
    amount_after = fields.Monetary(currency_field="currency_id")
    amount_delta = fields.Monetary(currency_field="currency_id")
    currency_id = fields.Many2one("res.currency", related="change_id.currency_id", store=True)
```
- “应用变更”可自动写回合同行、生成差额台账、更新预算/五算。

### 18.6 AI 在合同体系的玩法
- 条款风险扫描：NLP 识别付款条件/索赔窗口/验收标准等风险，写入 `ai_risk_summary / ai_clause_hint`。
- 合同 vs 实际执行偏差：合同价+变更价 vs 结算/台账/回款，AI 输出差异与风控建议。
- 项目群视角组合分析：分包风险、结算方式对现金流影响、利润最优合同形态。

### 18.7 本章小结
- 收入合同 / 成本合同 / 变更 / 结算“四位一体”，全部挂接 WBS、BOQ、成本科目。
- 数据模型已为 AI 条款审查、变更谈判、结算草稿生成预留入口。
- “工程怎么干，钱就怎么走；钱怎么走，合同就怎么约；风险怎么控，台账就怎么记”真正落地。

---

# 第 19 章｜成本台账 & 利润分析中心

> 任何一分钱的成本，都要回答三个问题：为什么花？花在谁？花到哪一块工程上？

本章把 `project.cost.ledger` 设计成“工程成本总账”，强挂接 WBS / BOQ / 合同 / 科目 / 标签，成为所有成本事实的唯一落点和分析源。

---

## 19.1 体系定位

已有骨架：
- WBS / BOQ / 五算：结构与量价
- 合同（收入/成本）：法律与价格边界
- 进度 / 资料 / 驾驶舱：状态与过程

成本台账的角色：
- 所有成本事实的最终落点
- 多维度统计的唯一源

设计原则：
1) 单表原子化：不拆表头/行，方便 `read_group`
2) 强结构挂接：`project_id / structure_id / boq_line_id / cost_item_id / contract`
3) 可追溯源头：记录来源单据
4) 维度丰富，录入入口简洁（自动或手工）

---

## 19.2 `project.cost.ledger` 数据模型

```python
class ProjectCostLedger(models.Model):
    _name = "project.cost.ledger"
    _description = "项目成本台账"
    _order = "project_id, date, id"

    # 归属
    project_id = fields.Many2one("project.project", required=True, index=True, ondelete="cascade")
    company_id = fields.Many2one("res.company", related="project_id.company_id", store=True, readonly=True)

    # 结构 / 清单
    structure_id = fields.Many2one("sc.project.structure", index=True)
    boq_line_id = fields.Many2one("project.boq.line", index=True)
    cost_item_id = fields.Many2one("sc.dictionary", domain="[('type','=','cost_item')]")

    # 合同 / 来源
    revenue_contract_id = fields.Many2one("project.revenue.contract", index=True)
    cost_contract_id = fields.Many2one("project.cost.contract", index=True)
    source_model = fields.Char("来源模型")
    source_id = fields.Integer("来源 ID")
    source_display = fields.Char("来源单号")

    # 金额
    date = fields.Date(default=fields.Date.context_today, required=True)
    description = fields.Char(required=True)
    quantity = fields.Float()
    uom_id = fields.Many2one("uom.uom")
    price_unit = fields.Monetary(currency_field="currency_id")
    amount = fields.Monetary("金额(不含税)", currency_field="currency_id")
    tax_amount = fields.Monetary("税额", currency_field="currency_id")
    amount_total = fields.Monetary("金额(含税)", currency_field="currency_id", compute="_compute_amount_total", store=True)
    currency_id = fields.Many2one("res.currency", related="project_id.company_currency_id", store=True, readonly=True)

    # 方向 & 状态
    direction = fields.Selection([("debit","成本发生"),("credit","成本冲减")], default="debit", required=True)
    state = fields.Selection([("draft","草稿"),("confirmed","已确认"),("locked","已锁定")], default="confirmed")

    # 标签 / 扩展
    section_type = fields.Selection([
        ("building","建筑"),("installation","安装/机电"),
        ("decoration","装饰"),("landscape","景观"),("other","其他")
    ])
    partner_id = fields.Many2one("res.partner")
    employee_id = fields.Many2one("hr.employee")
    tag_ids = fields.Many2many("project.cost.tag")
    ai_category_hint = fields.Char()
    ai_comment = fields.Text()

    @api.depends("amount","tax_amount")
    def _compute_amount_total(self):
        for rec in self:
            rec.amount_total = (rec.amount or 0.0) + (rec.tax_amount or 0.0)
```

与现有统计对齐：`project.project._compute_cost_control_stats` 依赖 `amount` 按 `project_id` 汇总，字段保持不变即可。

---

## 19.3 成本科目与成本标签

**成本科目**（结构化维度，用 `sc.dictionary(type='cost_item')`）：
```
直接成本：人工/材料/机械/专业分包
间接成本：管理/办公/差旅/折旧
财务成本：利息/手续费
```

**成本标签**（轻量事件标记）：
```python
class ProjectCostTag(models.Model):
    _name = "project.cost.tag"
    name = fields.Char(required=True)
    color = fields.Integer()
    description = fields.Char()
```
科目是刚性报表维度，标签是灵活分析维度（如签证/赶工/停工损失等）。

---

## 19.4 台账与业务单据的打通策略

目标：大多数台账行由业务单据自动生成，少数手工补录。

来源映射示例：
- 采购/收货/发票 → 材料类成本（带 partner、amount、税额，结构按需求单/领料单反推）
- 分包结算单 → 分包成本（继承 `cost_contract_id / structure_id / boq_line_id`）
- 机械租赁 → 按时间或工程量归集到 WBS
- 工资/劳务 → 按项目+WBS 分摊或按班组考勤拆解

统一生成接口示例（按钮“生成成本台账”）：
```python
vals = {
    "project_id": doc.project_id.id,
    "description": doc.name,
    "date": doc.date,
    "amount": doc.amount_untaxed,
    "tax_amount": doc.amount_tax,
    "partner_id": doc.partner_id.id,
    "source_model": doc._name,
    "source_id": doc.id,
    "source_display": doc.name,
    # 维度：cost_item_id / structure_id / boq_line_id 按业务场景传入
}
Ledger.create([vals])
```

---

## 19.5 利润分析的度量公式

1) 静态合同毛利：`合同总额 - 目标成本(预算)`
2) 执行毛利：`实际收入(开票/结算) - 台账实际成本`
3) 成本偏差：`目标成本 - 台账成本`
4) 收入偏差：`合同金额 - 结算/实际收入`

驾驶舱依赖：
- 收入：合同/发票/回款
- 成本：`project.cost.ledger.amount`

---

## 19.6 WBS / BOQ 维度的成本穿透报表

1) WBS 成本树：`structure_id child_of` 汇总台账金额
2) 清单盈亏：BOQ 行的收入合同金额 vs 分包/采购成本（合同行 + 台账）
3) 科目×WBS 交叉：行=科目，列=单位/分部，值=台账金额

全部可用 `read_group` + `child_of` 实现。

---

## 19.7 AI 成本与利润的扩展玩法

- AI 自动分类台账行：生成 `ai_category_hint`、自动打标签、建议 `structure_id/cost_item_id`
- AI 成本异常检测：对比历史项目与计划，找出单价/分包/材料异常
- AI 利润诊断：定位亏损专业/分包；项目群层面分析合同模式与供应商风险

---

## 19.8 落地路线建议

1) 先落地 `project.cost.ledger` 模型+菜单（手工录入），驾驶舱已有字段立即可用  
2) 在 WBS/BOQ 表单加 smart button：“查看本节点成本台账”（domain 带 `structure_id child_of 当前节点`）  
3) 先接一条自动生成链路（如分包结算单 → 成本台账）  
4) 再完善科目字典、标签模型、WBS/清单维度分析报表  

闭环复述：
> WBS 决定结构 → BOQ 决定价格 → 合同锁定边界 → 台账记录事实 → 驾驶舱呈现结果。

---

# 第 20 章｜项目经营驾驶舱设计（多维指标 & 看板）

> 驾驶舱 = 用尽可能少的指标，解释清楚这一个项目“赚不赚钱、稳不稳、风险在哪”。

现有字段（`project.project`）：
- 合同收入：`contract_amount`, `subcontract_amount`
- 成本：`budget_total`, `cost_ledger_amount_actual`, `cost_committed`
- 进度：`progress_rate_latest`
- 清单：`boq_amount_total`, `boq_amount_building`, `boq_amount_installation`
- 资料：`document_*`
- 驾驶舱字段：`dashboard_revenue_actual`, `dashboard_cost_actual`, `dashboard_profit_actual`, `dashboard_invoice_amount`, `dashboard_payment_in`, `dashboard_payment_out`, `dashboard_document_completion`, `dashboard_progress_rate`

目标：把这些指标结构化成“经营驾驶舱体系”，而非零散字段。

---

## 20.1 驾驶舱的层级结构

分两个层级：

1. **项目级驾驶舱（单项目视图）**
   - 面向项目经理/成本经理
   - 关注“这一盘工程现在怎么样”

2. **项目群驾驶舱（多项目总览）**
   - 面向管理层/经营管理部
   - 关注“哪些项目好、哪些危险、整体盘子怎么样”

同一指标口径一致，仅聚合维度不同。

---

## 20.2 指标体系总览

先列指标，再谈页面排布。

### 20.2.1 收入 & 成本指标

- **收入类**
  - `contract_amount`：项目合同总额（含税/不含税需统一口径）
  - `dashboard_revenue_actual`：实际收入（已实现收入：开票/结算）
  - `dashboard_invoice_amount`：已开票金额（若区分收入确认与开票，可分开展示）

- **成本类**
  - `budget_total`：目标成本（预算）
  - `cost_committed`：已承诺成本（合同/订单）
  - `cost_ledger_amount_actual`：台账实际成本（已发生）

- **毛利类**
  - 合同毛利 = `contract_amount - budget_total`
  - 执行毛利 = `dashboard_revenue_actual - cost_ledger_amount_actual`
  - 毛利率
    - 预算毛利率 = 合同毛利 / 合同总额
    - 执行毛利率 = 执行毛利 / 实际收入

### 20.2.2 进度 & 产值指标

- `plan_percent`：计划完成率（来自进度计划或预算）
- `actual_percent` / `progress_rate_latest`：实际完成率
- 产值计量（预留）
  - `output_amount_plan`：计划产值
  - `output_amount_actual`：实际产值
- 衍生
  - 进度偏差 = 实际完成率 - 计划完成率
  - 产值偏差 = 实际产值 - 计划产值

### 20.2.3 资料 & 合规指标

- `document_completion_rate`：资料完备率
- `document_missing_count`：缺失必备资料数量
- 结合项目状态 `lifecycle_state`

### 20.2.4 资金 & 现金流指标

- `dashboard_payment_in`：收款申请金额（当前取 `payment.request` 的 done 金额）
- `dashboard_payment_out`：付款申请金额
- 财务对接后可扩展：已收款金额、已付款金额
- 衍生：资金缺口 = 已付款 - 已收款（或收/付计划 vs 实际）

### 20.2.5 风险与健康度评分（预留）

- 红黄灯 + 标签即可，规则示例：
  - 红灯：执行毛利率 < 预算毛利率 - 5 个百分点；实际成本 > 预算成本 × 105%；进度落后 > 10%
  - 黄灯：偏差在 5%~10%
- 预留健康度公式：

```text
健康度 = 100 - (成本超支分 + 进度滞后分 + 资料不全分 + 资金压力分)
```

---

## 20.3 项目级驾驶舱页面布局设计

可适配 Odoo 原生或自定义前端。

### 20.3.1 顶部概览卡片区（KPI Cards）

4~6 个卡片，每卡包含：

1. **项目合同额 & 预算成本**
   - 主值：合同总额
   - 副值：目标成本
   - 标签：预算毛利率

2. **实际收入 & 成本**
   - 主值：实际收入
   - 副值：台账成本
   - 标签：执行毛利 / 执行毛利率

3. **进度状态**
   - 主值：实际完成率
   - 副值：计划完成率
   - 标签：进度偏差（+/-）

4. **资料完备度**
   - 主值：资料完备率
   - 副值：缺失资料数量

5. **收支压力**
   - 主值：收款申请金额
   - 副值：付款申请金额
   - 标签：净现金流（收 - 付）

6. **项目健康度（预留）**
   - 主值：健康分（0~100）
   - 标签：综合评价（正常/关注/告警）

技术封装：后端返回 JSON，前端渲染卡片：

```json
[
  {
    "key": "contract_vs_budget",
    "title": "合同 vs 预算",
    "main_value": 250000000,
    "sub_value": 190000000,
    "unit": "元",
    "tag": "预算毛利率 24%",
    "trend": "up"
  }
]
```

短期用 Odoo kanban header stat button + 字段组合；长期在 Vue 前端做专用组件。

### 20.3.2 中部多维分析区

2×2 或分栏：

1. **成本结构饼图**
   - 维度：成本科目（人工/材料/分包/管理费/财务费...）
   - 数据：`project.cost.ledger` 按 `cost_item_id` + `project_id` 汇总

2. **WBS 维度成本条形图**
   - 维度：单位工程/分部工程
   - 数据：WBS 节点（X 轴） vs 台账成本（Y 轴，Top N）

3. **毛利走势折线图（时间维度）**
   - 按月：收入、成本、毛利

4. **进度 vs 成本曲线**
   - 横轴：时间
   - 纵轴：计划完成率 / 实际完成率 / 成本累计支出比例

Odoo 原生用 pivot/graph，自定义前端用 `read_group` 喂图。

### 20.3.3 底部细节列表区

1. **重大成本台账 TOP N**
   - 按金额降序
   - 字段：记账日期、来源单据、成本科目、WBS 节点、金额、供应商/分包单位

2. **资料缺失清单**
   - 字段：资料类别、是否必备、当前状态、责任人
   - 目标：项目经理可直接从驾驶舱补资料

---

## 20.4 项目群驾驶舱设计（多项目总览）

“列表 + 图表”的总览页。

### 20.4.1 项目列表指标

在 `project.project` 的 tree/kanban 中展示：

- 基础：项目名称、项目编号、项目状态（`lifecycle_state`）、项目经理
- 经营核心：`contract_amount`、`budget_active_cost_target`、`cost_ledger_amount_actual`、`dashboard_revenue_actual`、`dashboard_profit_actual`、`dashboard_progress_rate`、`dashboard_document_completion`、健康度（若有）

智能排序示例：

- 按执行毛利率 → 找赚钱项目
- 按成本超支比例 → 找爆雷风险
- 按进度滞后比例 → 找拖期项目
- 按资料完备率 → 找结算风险

### 20.4.2 上层图表

典型视图：

1. **项目毛利 vs 规模散点图**
   - X 轴：合同总额
   - Y 轴：执行毛利率
   - 气泡：项目规模/成本

2. **项目健康度排名条形图**
   - Y 轴：项目名称
   - X 轴：健康分

3. **资金压力雷达图**
   - 维度：收款完成率、付款完成率、资金缺口比例

4. **状态分布饼图**
   - 按项目状态：立项 / 在建 / 结算中 / 保修 / 关闭

---

## 20.5 指标计算口径统一（后端实现要点）

在 `project.project` 的 compute 层统一口径，只暴露算好的字段，前端/报表直接展示。

1. **收入口径**
   - `contract_amount`：主合同金额之和（可筛选主合同类型）
   - `dashboard_revenue_actual`：优先用发票行收入（income 科目 `read_group`），若项目未分类则用发票总额兜底

2. **成本口径**
   - 预算：`budget_active_cost_target`
   - 实际：`cost_ledger_amount_actual`（只认成本台账）

3. **进度口径**
   - 使用 `progress_rate_latest`，从 `project.progress.entry` 取最新记录

4. **资料完备度**
   - `_compute_document_stats` 逻辑保持

5. **健康度（预留字段）**

```python
health_score = fields.Float("项目健康度(0-100)", compute="_compute_health_score", store=False)
health_level = fields.Selection(
    [("good","正常"),("warn","关注"),("risk","告警")],
    string="健康等级", compute="_compute_health_score", store=False
)
```

规则示例：
- 成本超支 >10% → -40 分；5%~10% → -20 分
- 进度滞后 >10% → -20 分
- 资料完备率 <80% → -10 分
- 资金缺口显著 → -20 分

健康度 = `max(0, 100 - 扣分)`；健康等级：≥80 正常，50~80 关注，<50 告警。

---

## 20.6 权限 & 视图策略

驾驶舱数据敏感，需要权限控制。

1. **视图层级**
   - 普通项目成员：只能看自己参与项目（record rule）
   - 项目经理：可看本项目全部指标
   - 成本/财务人员：可看多个项目但不改主数据
   - 管理层：可看项目群驾驶舱

2. **数据粒度**
   - 预留“金额模糊”权限：部分角色仅看成本等级（高/中/低），不看具体金额（有需求再实现）

---

## 20.7 实施路线建议

结合当前进度，三步落地：

1. **Step 1：表单页驾驶舱页签**
   - `project.project` 表单新增 `<page string="经营驾驶舱">`
   - 用 group + stat info 展示关键字段，不画复杂图表

2. **Step 2：项目列表/kanban 的经营视图**
   - 项目 tree/kanban 增加经营视角 action/view，挂核心字段
   - 支持按状态/健康/毛利率筛选排序

3. **Step 3：核心图表**
   - 基于 `read_group` 做成本结构饼图 + 项目毛利柱状图
   - 为未来 Vue 前端提供接口规范

总结：第 19 章解决成本事实落地，第 20 章让人一眼看懂项目经营状况，指标口径统一，视图分层清晰。

---

# 第 21 章｜五算对比体系（概算 / 预算 / 标后 / 合同 / 决算）

五算不是五张表，而是同一个 WBS/清单的五套“版本属性”。现有能力：WBS 树、BOQ 基础、成本台账、进度、节点金额自动汇总，为五算对比提供了基础。

---

## 21.1 为什么工程行业必须“五算对比”？

- 设计 → 概算；施工图 → 预算；招标 → 标后；签约 → 合同；完工 → 决算
- 同一清单项目在五个阶段可能有五个数量、五个单价、五个合价
- 未结构化的痛点：预算员/技术员/分包量不一致；项目经理不知盈亏；成本经理不知偏差来源；决算缺证据
- 目标：让五算数据编码化、结构化、自动化

---

## 21.2 五算体系总设计思想

1. 同一 WBS/清单项目数据库中只存在“一条主记录”
2. 主记录拥有五算的版本字段
3. 导入新版本（预算/合同/决算等）时写入对应字段
4. WBS 自动按五算递归汇总，并做差异分析

五算数据不是五张表，是清单对象上的五个版本层。

---

## 21.3 `project.boq.line` 模型扩展（核心）

增加五算字段组：

```python
# 概算
estimate_qty = fields.Float("概算工程量")
estimate_price = fields.Float("概算单价")
estimate_amount = fields.Float("概算合价")

# 预算（施工图预算）
budget_qty = fields.Float("预算工程量")
budget_price = fields.Float("预算单价")
budget_amount = fields.Float("预算合价")

# 标后（投标报价）
postbid_qty = fields.Float("标后工程量")
postbid_price = fields.Float("标后单价")
postbid_amount = fields.Float("标后合价")

# 合同（签约）
contract_qty = fields.Float("合同工程量")
contract_price = fields.Float("合同单价")
contract_amount = fields.Float("合同合价")

# 决算（实际发生）
final_qty = fields.Float("决算工程量")
final_price = fields.Float("决算单价")
final_amount = fields.Float("决算合价")
```

五个版本构成同一清单的五条平行价格线。

---

## 21.4 数据来源与填充机制

导入来源与字段映射：

| 导入来源 | 写入字段 | 来源文件类型 |
| --- | --- | --- |
| 概算 | `estimate_*` | 概算清单 |
| 预算 | `budget_*` | 施工图预算 |
| 招标/标底 | `postbid_*` | 分部分项 F.1.1 标底 |
| 合同价 | `contract_*` | 合同清单 |
| 结算 | `final_*` | 决算书、计量签证产值 |

现有 wizard 能解析 F.1.1/F.1.2，只需按来源类型写入对应版本字段。

---

## 21.5 五算维度的自动汇总（WBS）

在 `sc.project.structure` 增加五算汇总字段：

```python
estimate_amount_total
budget_amount_total
postbid_amount_total
contract_amount_total
final_amount_total
```

每个汇总：`self.version_amount_total = sum(child_ids.version_amount_total) + sum(boq_lines.version_amount)` 递归累加。

---

## 21.6 五算差异公式（自动偏差分析）

对每个 WBS/清单计算偏差：

### 数量偏差
```
预算数量偏差 = 预算工程量 - 概算工程量
合同数量偏差 = 合同工程量 - 预算工程量
决算数量偏差 = 决算工程量 - 合同工程量
```

### 单价偏差
```
预算单价偏差 = 预算单价 - 概算单价
合同单价偏差 = 合同单价 - 预算单价
决算单价偏差 = 决算单价 - 合同单价
```

### 合价偏差
- 预算 vs 概算金额差
- 合同 vs 标后金额差
- 决算 vs 合同金额差（最关注）

决算超支分析：是量？是价？签证？漏项？措施费？材料涨价？系统可直接输出。

---

## 21.7 五算对比可视化（前端呈现）

### 21.7.1 清单行对比表

| 清单编码 | 名称 | 概算 | 预算 | 标后 | 合同 | 决算 | 差异分析 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 010101 | 土方开挖 | 1,230,000 | 1,180,000 | 1,240,000 | 1,300,000 | 1,450,000 | 决算增加：工程量变更 + 材料涨价 |

### 21.7.2 五线图

同一清单/WBS 节点的五条金额线：概算 → 预算 → 标后 → 合同 → 决算，直观展示演变。

### 21.7.3 偏差热力图

基于“决算比合同高多少”着色：深红（超支严重）/黄（轻微偏差）/绿（节约），配合 WBS 树定位爆雷项。

---

## 21.8 五算体系即成本控制逻辑

- 预算价 → 目标成本
- 标后价 → 招标合理性
- 合同价 → 承包责任
- 决算价 → 最终盈亏
- 差异 → 风险来源

系统能回答：
- 项目为什么亏：决算比合同超出 X，分解量/价/变更/返工/管理费
- 超支从哪开始：预算偏差 5% → 合同 8% → 决算 12%
- 下个项目怎么避免：预算漏项、工期风险识别、材料锁价策略

---

## 21.9 五算体系数据库结构总结

```
WBS 节点（sc.project.structure）
    estimate_amount_total
    budget_amount_total
    postbid_amount_total
    contract_amount_total
    final_amount_total
    （可选：五算差异字段）

清单（project.boq.line）
    estimate_qty/price/amount
    budget_qty/price/amount
    postbid_qty/price/amount
    contract_qty/price/amount
    final_qty/price/amount
    WBS 归属信息
```

数据流：文件导入 → 写入对应版本字段 → WBS 自动汇总 → 五算对比报表自动生成。

---

## 21.10 五算体系实施路线

### Phase 1：清单五算字段体系（1~2 天）
- 清单模型加字段；WBS 加汇总字段
- 导入 wizard 写入对应版本字段
- 表单页添加五算字段 group

### Phase 2：五算汇总与差异统计（2~3 天）
- WBS 递归自动计算五算金额
- 清单差异字段（量/价/合价差）
- WBS 节点差异字段自动计算

### Phase 3：前端驾驶舱报表（5~7 天）
- 五算对比表、五线图、偏差热力图、WBS 差异树

最终：提升系统的企业级价值，彻底对齐“同一工程量，不同阶段价量对不上”的行业痛点。

---

# 第 22 章｜工程变更与签证管理系统（五算体系的关键输入层）

五算告诉你“为什么偏差”，变更/签证告诉你“偏差怎么来的、是否合法、是否可控”。加入变更管理，系统升维到全过程合约管理。

---

## 22.1 为什么变更签证是成本控制的核心？

- 常见亏损源：无签字变更、设计变更导致量变、材料涨价、口头确认、赶工/夜间/安全文明费用、分包追加量、决算才发现漏算
- 结论：工程变更一定会发生；无系统管理成本必爆炸
- 目标：可申报 → 可审批 → 可追溯 → 可结算 → 可分析 的标准化变更管理体系

---

## 22.2 系统模型体系（核心架构）

三张核心模型：

### 1) 工程变更单 `sc.change.order`

记录设计/现场工程量变更。

```python
class ScChangeOrder(models.Model):
    _name = "sc.change.order"

    project_id = fields.Many2one("project.project")
    change_no = fields.Char()
    reason = fields.Text()
    change_type = fields.Selection([
        ("design", "设计变更"),
        ("site", "现场签证"),
        ("material", "材料调整"),
        ("scope", "工程范围变化"),
    ])

    requested_by = fields.Many2one("res.users")
    approved_by = fields.Many2one("res.users")

    state = fields.Selection([
        ("draft", "草稿"),
        ("submitted", "已提交"),
        ("approved", "已审批"),
        ("rejected", "已驳回"),
    ], default="draft")

    change_line_ids = fields.One2many("sc.change.line", "change_id")
```

### 2) 工程变更明细 `sc.change.line`

对应每条量/价变化。

```python
class ScChangeLine(models.Model):
    _name = "sc.change.line"

    change_id = fields.Many2one("sc.change.order")
    boq_line_id = fields.Many2one("project.boq.line")
    wbs_id = fields.Many2one("sc.project.structure")

    delta_qty = fields.Float("变更工程量")  # 正负皆可
    delta_price = fields.Float("单价调整")
    delta_amount = fields.Float("金额变化", compute="_compute_amount")
```

`delta_amount = delta_qty × (原单价 + delta_price)`。

### 3) 签证单 `sc.work.visa`

处理现场签证。

```python
class ScWorkVisa(models.Model):
    _name = "sc.work.visa"

    project_id = fields.Many2one("project.project")
    visa_no = fields.Char()
    description = fields.Text()

    qty = fields.Float("签证量")
    price = fields.Float("签证单价")
    amount = fields.Float("签证金额")

    related_boq_line_ids = fields.Many2many("project.boq.line")
    state = fields.Selection([...])
```

签证可与变更合并或独立，取决于企业习惯。

---

## 22.3 变更如何影响五算与决算（核心逻辑）

变更是合同偏差的证据层，不直接改原合同字段。

1) 合同量 = 原合同量 + 审批通过的 `delta_qty`  
2) 合同价 = 原合同价 + 审批通过的 `delta_amount`  
3) 决算价 = 合同价 + 决算阶段实际变动量

操作方式：
- 录入变更 `delta_qty/price`
- 系统自动调整合同价、最终决算价
- 保持“原始合同”+“变更证据”+“最终结果”三层清晰，便于审计/结算/复盘

---

## 22.4 变更审批流程设计

状态机：`draft → submitted → approved → confirmed/rejected`（可选 confirmed）。权限示例：草稿任意创建；提交=项目经理；审批=成本/技术负责人；确认=项目总/管理层。

审批通过自动执行：
- `contract_delta_qty += delta_qty`
- `contract_delta_amount += delta_amount`
- 重算五算字段
- 重算 WBS 金额
- 刷新驾驶舱指标

全程自动，无需手改合同量/价。

---

## 22.5 与台账、合同、成本联动

1) 进入成本预测 EAC：`EAC = actual_cost + committed_cost + expected_changes`，变更金额计入 expected_changes。  
2) 与台账匹配：实际成本产生时提示关联变更；无变更则标记为“可疑成本”需解释。  
3) 自动生成“变更说明书”：原因、前后对比、计算公式、清单对照、附件、合同价调整，导出 PDF。

---

## 22.6 前端（Vue）展示设计

1) **变更清单页**：编号、类型、金额、状态、申请人、审批人、原因、影响的 WBS；支持状态过滤、分类统计、月/周分析。  
2) **变更对比视图（黄金表）**：展示清单项的原合同/变更累计/最新合同/决算的量、价、合价对比。  
3) **WBS 变更热力图**：按变更金额着色（红/黄/绿）在 WBS 树中直观定位。

---

## 22.7 五算 + 变更 = 成本闭环

五算 = 静态对比；变更 = 动态演变；组合形成全过程成本管控。

流程：概算 → 预算 → 标后 → 合同价（基准线） → 变更修正基准 → 决算价（最终） → 复盘。

---

## 22.8 下一步路线建议

1) 创建两张表：变更单 + 变更行（轻量先行）  
2) 清单模型加合同偏差字段：`contract_delta_qty/contract_delta_amount`，并用 `contract_qty = original_contract_qty + contract_delta_qty` 等公式自动反映  
3) 变更审批工作流（state 驱动）  
4) WBS 汇总与五算联动逻辑  
5) 前端 Vue 变更对比页  
6) 将变更全量纳入 AI 成本预测（EAC）模型

---

# 第 23 章｜现场签证系统（Work Visa）完整设计

现场签证覆盖零星/临时/附加工作，易引发财务损失与篡改，必须可追溯、不可篡改、可审批、可核量、可计价、可与合同联动、可进入结算。

---

## 23.1 签证 VS 变更：区别与关系

| 类型 | 定义 | 来源 | 体量 |
| --- | --- | --- | --- |
| 设计变更 | 图纸/工程量规定变更 | 设计院/甲方 | 大规模工程量 |
| 现场签证 | 施工现场零星、临时、附加工作 | 工程师/监理 | 小量但多 |

共同点：都会改变成本、需结算、有审批、要证据链、要进入最终合同价。区别：变更影响合同清单编码；签证多为清单外新工作。签证需支持关联清单/WBS，或作为临时签证项。

---

## 23.2 核心数据模型设计

新增两模型：

### 签证主表 `sc.work.visa`

```python
class ScWorkVisa(models.Model):
    _name = "sc.work.visa"
    _description = "现场签证单"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    project_id = fields.Many2one("project.project", required=True)
    visa_no = fields.Char("签证编号", required=True, copy=False)
    title = fields.Char("签证标题", required=True)
    description = fields.Text("签证说明")

    applicant_id = fields.Many2one("res.users", string="申请人", default=lambda self: self.env.user)
    approver_id = fields.Many2one("res.users", string="审核人")
    approved_date = fields.Datetime()

    state = fields.Selection([
        ("draft", "草稿"),
        ("submitted", "已提交"),
        ("approved", "已审批"),
        ("confirmed", "已确认"),
        ("rejected", "驳回"),
    ], default="draft", tracking=True)

    visa_line_ids = fields.One2many("sc.work.visa.line", "visa_id")

    total_amount = fields.Monetary("签证金额合计", compute="_compute_amount_total", store=True)
    currency_id = fields.Many2one("res.currency", related="project_id.company_id.currency_id", readonly=True)

    attachment_ids = fields.Many2many("ir.attachment", string="附件（照片/视频/记录）")
```

特性：消息跟踪、审批、附件、金额汇总。

### 签证明细 `sc.work.visa.line`

```python
class ScWorkVisaLine(models.Model):
    _name = "sc.work.visa.line"
    _description = "签证明细"

    visa_id = fields.Many2one("sc.work.visa")

    boq_line_id = fields.Many2one("project.boq.line", string="关联清单项")
    wbs_id = fields.Many2one("sc.project.structure", string="关联 WBS 节点")

    description = fields.Char("工作内容", required=True)

    qty = fields.Float("数量")
    uom_id = fields.Many2one("uom.uom", "单位")
    price = fields.Float("单价")
    amount = fields.Float("金额", compute="_compute_amount", store=True)
```

支持清单内签证（关联 BOQ/WBS）和清单外新工作（描述+量价）。

---

## 23.3 签证审批流程设计

流程：`draft → submitted → approved → confirmed`。  
含义：草稿=现场填报；提交=项目经理审核量/必要性；审批=成本经理确认计价；确认=锁定金额纳入结算。  
动作：提交校验内容/数量；审批校验价格/计价依据；确认后金额锁定。

---

## 23.4 签证金额如何影响 WBS 与合价（核心）

签证不改原工程量，作为附加成本进入五算：
- 预测价变化（EAC）
- 合同外新增款项（Contract Extra Work）
- 决算增加项（Settlement Add-on）

建议 WBS 增加：`visa_amount`, `visa_amount_total`，递归汇总：节点签证金额 = 子节点签证金额之和。展示：

```
原合同价
+ 设计变更
+ 现场签证
= 调整后合同价
```

---

## 23.5 签证与成本台账联动

- 台账录入来源为签证时自动关联并归集
- 台账金额异常提示“应有签证”提醒
- 签证审批通过自动计入预计成本（EAC）

---

## 23.6 签证证据链管理

证据：现场照片（前后）、视频、监理指令、洽商、施工日志、旁站、材料出入场、机械台班、施工方案。Odoo 附件+chatter 支持。UI：左侧签证数据，右侧附件浏览，可 PDF 合并导出。

---

## 23.7 前端（Vue）签证 UI 设计

1) 签证总览页：统计卡片（数量/金额/类型分布）、按 WBS 汇总、类型分类、月/周趋势图  
2) 签证明细页：基本信息、签证明细表、附件区（图片墙/视频列表）、审批流  
3) 签证-清单对照视图：原合同工程量 vs 签证工程量 vs 决算量 + 金额累计

---

## 23.8 系统能力与行业对接

- PDF 导出（签证单+明细+附件）
- 对接政府监管平台（如广东/四川）
- 对接造价软件（广联达/新点）导入导出
- 纳入决算书生成

加入签证后，系统从“成本核算”升级为“合同与变更全过程管理”。

---

# 第 24 章｜项目结算体系（全过程结算 + 证据链 + 自动决算书生成）

结算整合 BOQ/WBS、变更（22）、签证（23）、台账、五算、进度计量，构建可审计、可结算、可自动生成决算书的体系。

---

## 24.1 工程结算体系的本质

结算 = 合同价 + 合法有效的工程量变化（变更） + 合法有效的现场新增工作（签证） + 可证明的最终发生量（决算量），并满足：可追溯、流程可验证、不可篡改、附件完整、审批链清晰、金额有依据。

---

## 24.2 结算体系 5 大核心组成

1) **合同基准线**：`original_contract_qty/price/amount`（合同清单导入生成基准线）  
2) **变更**：`delta_qty/price/amount` → 调整后合同价：`contract_qty = original_qty + sum(delta_qty)` 等  
3) **现场签证**：`qty/price/amount` + 证据链；不改工程量，只改价款，`visa_amount_total = sum(visa.amount)`  
4) **决算工程量**：`settlement_qty/price/amount`（最终确认量，必要时有结算单价）  
5) **审计调整**：`audit_qty_adjust/audit_amount_adjust/audit_comment`（审计扣减量价）

---

## 24.3 项目最终价款计算模型

```
Final Settlement =
    Contract Amount
  + Change Amount
  + Visa Amount
  + Settlement Adjustment (决算差异)
  + Other Fees (规费、税金、措施等)
  - Audit Reductions
```

展开：合同基准价 + 变更累计 + 签证累计 + 决算工程量差额 + 规费/税金 − 审计扣减 = 最终结算价。

---

## 24.4 系统模型设计（Odoo）

### 结算总表 `sc.settlement`

```python
class ScSettlement(models.Model):
    _name = "sc.settlement"
    _description = "项目结算单"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    project_id = fields.Many2one("project.project", required=True)

    state = fields.Selection([
        ("draft", "草稿"),
        ("calculating", "计算中"),
        ("submitted", "已提交审计"),
        ("audited", "审计完成"),
        ("confirmed", "已确认"),
    ], default="draft", tracking=True)

    settlement_line_ids = fields.One2many("sc.settlement.line", "settlement_id")

    contract_amount = fields.Monetary()
    change_amount = fields.Monetary()
    visa_amount = fields.Monetary()
    settlement_adjust_amount = fields.Monetary()
    fee_amount = fields.Monetary()
    tax_amount = fields.Monetary()
    audit_deduction_amount = fields.Monetary()
    final_amount = fields.Monetary()
```

### 结算明细 `sc.settlement.line`

每条 BOQ 一条结算行。

```python
class ScSettlementLine(models.Model):
    _name = "sc.settlement.line"

    settlement_id = fields.Many2one("sc.settlement")
    boq_line_id = fields.Many2one("project.boq.line")

    original_qty = fields.Float()
    change_qty = fields.Float()
    contract_qty = fields.Float()

    settlement_qty = fields.Float()
    settlement_price = fields.Float()
    settlement_amount = fields.Float()

    visa_amount = fields.Float()

    audit_qty_adjust = fields.Float()
    audit_amount_adjust = fields.Float()

    final_amount = fields.Float()  # 最终审定金额
```

### 规费/税金计算引擎

按费率自动计算，可配置、可人工调整。

---

## 24.5 结算计算流程（自动化）

用户点击“生成结算”：

1) 读取合同值：`original_contract_qty/amount`  
2) 读取变更：`change_amount = sum(delta_amount)`，`change_qty = sum(delta_qty)`，`contract_qty = original_qty + change_qty`  
3) 读取签证金额：`visa_amount = sum(visa.amount)`  
4) 读取决算工程量：`settlement_qty`（录入或计量生成），`settlement_amount = settlement_qty × settlement_price`  
5) 自动生成差异表（合同 vs 决算，量/金额/原因）  
6) 计算规费与税金（用户配置费率，自动算安全文明费/管理费/利润/税金等）  
7) 审计扣减（录入扣减量/金额/说明）立即影响结果  
8) 生成最终结算价：

```
final_amount = contract_amount + change_amount + visa_amount
                + settlement_adjust_amount + fee_amount + tax_amount
                - audit_deduction_amount
```

---

## 24.6 结算报告（自动生成 PDF）

报告包含：封面、项目概况、结算汇总、分部分项/措施结算书、变更签证汇总、决算工程量对比表、审计调整说明、附件目录（证据链）、影像资料。可扩展：审计用 Excel、政府审计可用的竣工结算书。

---

## 24.7 结算与 AI 结合

具备清单/WBS/量/变更/签证/台账/决算/审计后，AI 可：生成结算草稿、检测异常工程量/重复签证、预测结算金额、辅助审计说明、分类照片匹配清单、审查结算风险。

---

## 24.8 本章总结

你已有 BOQ、WBS、变更、签证、台账、五算、合价汇总基础，只需少量新增字段/模型/审批流，即可构建行业领先的全过程结算系统。

---

# 第 25 章｜产值计量系统（Monthly Work Progress Measurement）

解决“做了多少钱的活、本期计多少产值、与合同/结算/收款如何对齐”。依托 BOQ、WBS、`project.progress.entry`，形成专业产值计量体系。

---

## 25.1 行业视角下的产值计量本质

产值计量 = 按合同清单/工程结构分期统计“已完成量×单价”的金额，形成可审批、可结算依据。特征：有计量期（按月/里程碑），以合同 BOQ 为基准，可按工程量或百分比计量，累计计量≠合同总价（保留金、暂列等），结果喂给收入确认、收款申请、结算。

---

## 25.2 核心概念

- **计量批次**（Measurement Batch）：一次计量申请/报量单，如“2025-01 月度计量”；建议用 `project.progress.entry` 作为计量单头。  
- **计量明细**（Measurement Line）：每条 BOQ/WBS 的本期量/金额；新模型 `project.progress.line`。  
- **三值关系**：合同值 / 累计完成值 / 本期完成值，保持 `累计 = 上期累计 + 本期`，`剩余 = 合同 - 累计`，金额=量×价。  
- **项目产值率**：合同金额口径 `progress_rate = 累计计量金额 / 合同总额`；可扩展工程量权重口径。建议把 `project.project.progress_rate_latest` 定义为“产值进度（基于计量）”。

---

## 25.3 数据模型设计：计量单头 + 计量行

### 25.3.1 计量单头（重构 `project.progress.entry` 为计量批次）

```python
class ProjectProgressEntry(models.Model):
    _name = "project.progress.entry"
    _description = "产值计量单"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    project_id = fields.Many2one("project.project", required=True)
    name = fields.Char("计量名称", required=True)  # 如 “2025年1月产值计量”
    period_start = fields.Date("计量开始日期")
    period_end = fields.Date("计量结束日期")

    state = fields.Selection([
        ("draft", "草稿"),
        ("submitted", "已提交"),
        ("approved", "已审批"),
        ("accounted", "已入账"),
    ], default="draft", tracking=True)

    line_ids = fields.One2many("project.progress.line", "entry_id", string="计量明细")

    amount_period = fields.Monetary("本期计量金额")
    amount_cumulative = fields.Monetary("累计计量金额")
    progress_rate = fields.Float("本期进度(%)")
    progress_rate_cumulative = fields.Float("累计进度(%)")

    invoice_id = fields.Many2one("account.move", string="关联结算/发票", readonly=True)
    payment_request_id = fields.Many2one("payment.request", string="关联收款申请", readonly=True)
```

一个 entry = 一份产值计量申请单。

### 25.3.2 计量明细 `project.progress.line`

```python
class ProjectProgressLine(models.Model):
    _name = "project.progress.line"
    _description = "产值计量明细"

    entry_id = fields.Many2one("project.progress.entry", required=True, ondelete="cascade")
    project_id = fields.Many2one(related="entry_id.project_id", store=True)

    boq_line_id = fields.Many2one("project.boq.line", string="清单项目", required=True)
    structure_id = fields.Many2one("sc.project.structure", string="工程结构节点")

    contract_qty = fields.Float("合同工程量", related="boq_line_id.contract_qty", store=True)
    contract_price = fields.Float("合同单价", related="boq_line_id.price", store=True)
    contract_amount = fields.Monetary("合同合价", currency_field="currency_id")

    qty_period = fields.Float("本期工程量")
    amount_period = fields.Monetary("本期金额", compute="_compute_amounts", store=True)

    qty_cumulative = fields.Float("累计工程量", compute="_compute_amounts", store=True)
    amount_cumulative = fields.Monetary("累计金额", compute="_compute_amounts", store=True)

    qty_remain = fields.Float("剩余工程量", compute="_compute_amounts", store=True)
    amount_remain = fields.Monetary("剩余金额", compute="_compute_amounts", store=True)

    remark = fields.Char("计量说明")
    currency_id = fields.Many2one("res.currency", related="project_id.company_id.currency_id", store=True)
```

`_compute_amounts`：汇总同一 BOQ 已审批的 progress.line，计算累计/剩余；本期量只影响本 entry。

---

## 25.4 与 BOQ / WBS 的联动

- 支持节点计量：在 WBS 增加形象进度字段 `progress_rate_manual` 与 `progress_amount_cumulative`。按钮“按节点进度生成计量”：选分部/单位工程 → 取 `boq_line_all_ids` → 按节点进度折算本期量生成 progress.line。  
- 支持自下而上（按清单逐条）和自上而下（按节点形象进度折算）。

---

## 25.5 页面与操作流程

- 项目表单入口：按钮“产值计量”打开 `project.progress.entry` 列表（当前项目过滤）；统计字段：`progress_entry_count`、新增 `progress_value_total`（累计产值）。  
- 计量单列表视图：项目、计量名称、期间、本期/累计金额、本期/累计进度、状态；支持按项目/期间/状态分组筛选。  
- 计量单表单：上部单头，下部明细（tree inline）：清单编码/名称、合同量/价、本期量/金额、累计量/金额、剩余量。操作：  
  - 从 BOQ 生成全部计量行（首次）  
  - 从 WBS 节点生成计量（形象进度）  
  - 从上期计量复制结构、重置本期量为 0（提效）

---

## 25.6 与结算、收款、财务打通

- 与结算（章 24）：结算单可引用计量单作为依据；审计可对比累计产值 vs 最终审定，防止超前计量。  
- 与收款申请 `payment.request`：按钮“生成收款申请”，amount = `amount_period * 收款比例`（可配置质保金/暂扣比例）。  
- 与收入确认：已审批计量单可生成会计凭证（借应收、贷工程施工收入），实现按产值法确认收入。

---

## 25.7 项目级 S 曲线（Progress S-Curve）

- 计划曲线：来自计划/预算产值，预设每月计划完成率。  
- 实际曲线：来自计量累计产值，`amount_cumulative / 合同总额`。  
- 图：X=时间，Y=累计进度%，同图对比计划/实际，识别滞后、抢工、偏差月份。

---

## 25.8 权责与审批链

角色：填报人（现场）、审核人（项目经理/技术）、复核人（成本/造价）、批准人（项目总/公司）。  
流程：`draft → submitted → approved → accounted`，每步记录人/时间/日志/附件签字。

---

## 25.9 小结

打通：合同→BOQ→WBS；变更+签证→结算调整；产值计量→收入确认→收款申请；最终结算→审计调整→最终价款，形成完整“工程收入与价款形成链条”。

---

# 第 26 章｜成本控制闭环（Budget–Contract–Change–Ledger–Settlement）

控账的本质：让预算、合同、变更、签证、台账、产值、结算在一条逻辑链上收敛，数字统一、可追溯、可审计。

---

## 26.1 成本控制闭环的行业标准逻辑

```
预算（目标成本）
   → 合同（承诺成本）
      → 签证/变更（动态成本）
         → 台账（实际成本）
            → 结算（最终成本）
```

越往下越真实、不可逆、影响利润。最终利润 = 结算收入 - 最终成本。系统目标：避免成本失控、结算不符、利润预估偏差。

---

## 26.2 闭环体系总览：模块协同

| 模块 | 角色 | 现状 | 扩展 |
| --- | --- | --- | --- |
| `project.budget` | 预算（目标成本） | 有 | 增强版本/基准对比 |
| `project.boq.line` | 合同清单（收入/成本侧） | 有 | 增强成本属性 |
| `project.contract`（自定义） | 内外部合同（承诺成本） |有| 增强成本结构 |
| `project.cost.ledger` | 成本台账（实际成本） | 有 | 增加科目、WBS、BOQ 联动 |
| `project.progress.entry` | 产值（收入实际发生） | 有 | 已在 25 章增强 |
| `sc.settlement` | 结算（最终成本/收入） | 部分 | 本章扩展 |

闭环：预算(target) → 合同(committed) → 变更(adjusted) → 签证(extra) → 台账(actual) → 产值(actual revenue) → 结算(final)。

---

## 26.3 预算（Budget）体系

预算是“天花板”，为合同/采购/台账提供对比基准，支撑利润预测。

### 26.3.1 预算模型字段（建议）

```python
class ProjectBudget(models.Model):
    _name = "project.budget"

    version = fields.Char("预算版本")
    version_date = fields.Date("版本日期")

    project_id = fields.Many2one("project.project")
    boq_line_ids = fields.One2many("project.budget.line", "budget_id")

    amount_cost_target = fields.Monetary("总目标成本")
    amount_revenue_target = fields.Monetary("总目标收入")

    is_active = fields.Boolean("是否当前预算版本")
```

### 26.3.2 预算行与 BOQ 对应

`project.boq.line ↔ project.budget.line`，字段：`budget_qty/budget_price/budget_amount`，实现预算 vs 合同 vs 产值 vs 实际三线对比。

---

## 26.4 合同（Contract）= 承诺成本层

预算=预计成本，合同=承诺成本。合同行建议字段：`boq_line_id`、`wbs_id`、`contract_qty/contract_price/contract_amount`。合同类型：主合同（收入）、分包合同（成本）、采购合同。关键：成本合同必须与 WBS/BOQ 对齐，否则无法控成本。

---

## 26.5 变更（Change）与签证（Claim）统一建模

变更/签证都属合同增补，统一模型：

```python
class ProjectChangeOrder(models.Model):
    _name = "project.change.order"

    category = fields.Selection([("change","变更"),("claim","签证")])
    boq_line_id = fields.Many2one("project.boq.line")
    wbs_id = fields.Many2one("sc.project.structure")

    qty_change = fields.Float()
    price_change = fields.Float()
    amount_change = fields.Float()

    state = fields.Selection([...])
```

让变更直接修改清单量/价、合同金额、结算金额，联动全链路。

---

## 26.6 成本台账（Actual Cost Ledger）

台账是真实支出，需关联合同行、BOQ、WBS、科目。

```python
class ProjectCostLedger(models.Model):
    _name = "project.cost.ledger"

    project_id = fields.Many2one(...)
    wbs_id = fields.Many2one("sc.project.structure")
    boq_line_id = fields.Many2one("project.boq.line")
    contract_id = fields.Many2one("project.contract")
    vendor_id = fields.Many2one("res.partner")

    amount = fields.Monetary()
    amount_tax = fields.Monetary()
    payment_state = fields.Selection([("unpaid","未付"),("partial","部分付"),("paid","已付")])

    ledger_type = fields.Selection([
        ("labor","人工成本"),
        ("material","材料成本"),
        ("machinery","机械成本"),
        ("subcontract","分包成本"),
        ("other","其他成本"),
    ])
```

WBS 增加：`actual_cost_total`、`commit_cost_total`、`budget_cost_total`、`change_cost_total`，形成预算→承诺→动态→实际四条线。

---

## 26.7 结算（Final Settlement）终局层

`sc.settlement` 统一收入/成本结算。

```python
class Settlement(models.Model):
    project_id = fields.Many2one(...)
    type = fields.Selection([("income","收入结算"),("cost","成本结算")])

    boq_line_id = fields.Many2one("project.boq.line")
    wbs_id = fields.Many2one("sc.project.structure")

    amount_contract = fields.Monetary()
    amount_change = fields.Monetary()
    amount_progress = fields.Monetary()
    amount_final = fields.Monetary()

    state = fields.Selection([...])
```

作用：审定最终合同/成本价，覆盖变更/签证，是最终利润依据。

---

## 26.8 项目利润四线图（驾驶舱核心）

可绘制：预算成本线（蓝）、承诺成本线（绿）、实际成本线（橙）、最终成本线（红）；收入线（紫）、产值线（青）、结算线（黑）。基于 BOQ/WBS + 预算 + 合同 + 变更 + 台账 + 产值 + 结算，输出多维利润分析。

---

## 26.9 小结

已具备：合同价体系、清单+工程结构、预算控制、合同承诺成本、变更签证、实际成本（台账）、产值计量、结算、利润预测、驾驶舱（进度/收入/成本/利润四线图）。这是面向大型企业的专业工程管理系统框架。

---

# 第 27 章｜全系统数据联动与项目经营驾驶舱（四线图 + 三率一指数）

目标：用全链路数据提前预警、动态呈现趋势，帮助管理层决策，回答“赚了/亏了/要亏了”。

---

## 27.1 驾驶舱核心目标

1) 现状：当前产值/成本/利润/进度/资金压力  
2) 预测：成本是否超、工期是否可控、收款是否及时、最终利润多少  
3) 风险：预算外超成本、产值偏低、结算慢、收款滞后、现金流为负

---

## 27.2 核心指标体系（KPI 框架）

### 27.2.1 收入侧
合同总额；变更后合同价；本期产值；累计产值；结算价。

### 27.2.2 成本侧
目标成本；承诺成本；动态成本（承诺+变更）；实际成本；结算成本。关键偏差：承诺 vs 预算（项目起点超标？）；实际 vs 承诺（采购失控？）。

### 27.2.3 进度侧
计划进度；实际进度（产值计量）；进度偏差（SV = 实际 - 计划）。

### 27.2.4 资金侧
应收(AR)=产值-已收；应付(AP)=实际成本-已付；现金流净值=AR-AP；资金压力指数 CFI=现金流净值/合同额。

### 27.2.5 风险侧
进度落后、成本超支、收款滞后 → 组合为项目风险指数 PRI。

---

## 27.3 四线图（核心可视化）

收入线、成本线、产值线、进度线（可扩充为五线：含结算成本）。  
- 合同收入线：`contract_total(含变更)`  
- 预算成本线：`budget_cost_total`  
- 承诺成本线：`sum(contract.cost_amount)`  
- 实际成本线：`sum(cost_ledger.amount)`  
- 结算成本线（可选）：最终成本。

展示项目何时开始亏、成本是否穿透预算、利润率趋势。

---

## 27.4 三率一指数

1) 成本偏差率 CVR = (目标成本 - 实际成本) / 目标成本  
2) 合同执行率 CER = 累计产值 / 合同总额  
3) 收款完成率 CR = 已收款 / 累计产值  
4) 资金压力指数 CFI = (累计收款 - 实际成本) / 合同额  
阈值：CR<50% 重度拖欠；CFI<-10% 需资金注入，<-20% 危险。

---

## 27.5 驾驶舱页面设计

- 顶部 KPI（8 指标）：合同总额、变更后合同额、累计/本期产值、累计/本期成本、累计收款、CFI、项目经营等级（A/B/C/D）。  
- 中部五线图：收入/产值/预算成本/承诺成本/实际成本，按月/周。  
- 底部结构化分析：按 WBS/专业/分部/清单段/成本科目展示 预算 vs 承诺 vs 实际成本，合同产值 vs 已计量 vs 已收款，偏差率、预警等级。

---

## 27.6 项目健康指数 PHI

```
PHI = (CVR ×30%) + (CER ×20%) + (CR ×20%) + (CFI ×30%)
```

分级：90–100 A 优秀；70–89 B 正常；50–69 C 预警；<50 D 危机。

---

## 27.7 实施策略（Odoo 架构）

- 无需新模块：指标计算写在 `project.project` compute；图表用 web controller 或供前端 API；前端 ECharts/AntV。  
- 渲染流程：登录→加载收入/成本/产值/资金/指数→渲染 KPI 卡、折线图、成本构成、偏差表。

---

## 27.8 小结

从清单导入工具升级为企业级经营“大脑”：经营决策、成本控制、收入确认、产值计量、结算管理、健康指数+可视化，可面向国企/央企/大型施工/地产/轨道项目公司。

---

# 第 28 章｜PMO 多项目经营总控平台（集团经营中枢）

目标：把单项目的全链路能力汇聚为企业级经营中心，集团视角提前识别风险、优化资源、数据驱动决策。

---

## 28.1 PMO 平台核心价值

聚焦：资金风险（现金流）、成本偏差（利润稳定）、产值产能（推进能力）、收款进度（回款合理性）、合规（合同/采购/签证/台账规范）。本质：提前发现问题并快速处置。

---

## 28.2 企业级经营总控首页（Dashboard）

- 卡片 1：企业资金压力指数 CFI-G = 全公司 CFI 加权平均（累计收款、实际成本、合同额；绿/黄/红）。  
- 卡片 2：成本偏差总览 CVR-G = Σ（项目预算-项目实际）/Σ项目预算，可按事业部/地区/专业/项目类型分维度。  
- 卡片 3：产值执行度 CER-G = Σ累计产值/Σ合同额，用于业务推进/年度考核。  
- 卡片 4：结算滞后指数 = 应结算 - 已结算，按逾期 30/90/180 天分色预警。  
- 卡片 5：企业项目健康指数 PHI-G：A/B/C/D 项目占比。

---

## 28.3 多项目数据结构设计（标准化聚合）

依托标准 BOQ/WBS、成本/收入分类、清单编码规则，实现跨项目可聚合、可钻取的数据底座。

---

## 28.4 多维度钻取分析（联动 OLAP）

支持按区域、事业部、专业、项目经理、项目类型等维度查看：预算/合同/动态/实际成本；合同/变更/计量/结算/收款收入；利润率、偏差率、资金指数、健康指数。维度切换/钻取保持指标口径一致。

---

## 28.5 项目族群管理（Portfolio）

按地域/专业/规模/风险等级/合同模式/客户等规则自动分组，一键查看组内：总合同额、总产值、总成本、总收款、现金流、风险指数；用于董事会/事业部例会快速对比。

---

## 28.6 PMO 风险监测雷达

五维雷达：进度风险(SV)、成本风险(CV)、合同风险(变更滞后)、收款风险(CR)、结算风险(Settlement Index)。项目按风险排序，前端高亮红灯项目、风险高的事业部或地区。

---

## 28.7 多项目资源预测

输出 6–12 个月预测：产值（施工计划）、成本（工程量/合约）、现金流（合同收款节点），回答是否需追加投资/资金缺口/业务量增长区域。

---

## 28.8 PMO 前端页面结构（Vue3，三屏）

- 屏幕 1：企业总览 Dashboard（现金流、利润、健康指数、风险热力图）。  
- 屏幕 2：项目群分析：左侧项目组列表（事业部/区域/专业），右侧项目列表，按健康指数/利润率/产值执行度/收款进度/CFI 排序。  
- 屏幕 3：单项目深度分析：四线图、三率指标、风险雷达、结构化 BOQ/WBS、成本台账、合同/变更/结算。

---

## 28.9 小结

已具备三层能力：单项目工程结构化（BOQ+WBS）、项目经营链路（预算—合同—变更—产值—成本—结算）、项目驾驶舱（四线图+三率+健康指数），再叠加 PMO 企业总控、多维分析、收入/成本/资金/风险闭环，形成面向集团级客户的完整产品。

---

# 第 29 章｜全链路智慧工程数据模型（Data Model Deep Dive）

构建可持续迭代、可扩展、可视化、可分析的企业级数据蓝图：模型总图、命名规范、关联关系、数据血缘、DW 准备、星型模型、性能优化。

---

## 29.1 数据模型体系结构（总览图）

```
Project
│
├── WBS (sc.project.structure)
│     └── BOQ tree mapping
│
├── BOQ (project.boq.line)
│     ├── Budget (project.budget.line)
│     ├── Contract (project.contract.line)
│     ├── Change / Claim (project.change.order)
│     ├── Progress (project.progress.line)
│     ├── Settlement (project.settlement.line)
│     └── Cost Ledger (project.cost.ledger)
│
└── Finance (收款/付款)
```

BOQ 作为工程量实体，是所有经营数据的核心索引节点。

---

## 29.2 Project（项目主数据）

`project.project` 核心字段：`project_code`（集团唯一编码）、`name`、`project_type`、`owner_id`、`contractor_id`、`start_date/end_date`、`estimated_final_cost`、`health_index`。建议项目类型/专业/地区标准化字典。

---

## 29.3 WBS（工程结构）— 树形索引

`sc.project.structure` 关键字段：`parent_id`、`structure_type`（单项/单位/专业/分部/分项/清单）、`code`、`name`、`level`、`boq_line_all_ids`、`qty_total`、`amount_total`。WBS 已完整，可作为树形索引。

---

## 29.4 BOQ（业务主键）

`project.boq.line` 核心字段：`code`、`name`、`quantity`、`price`、`amount`、`boq_category`（分部分项/单价措施/总价措施）、`section_type`（建筑/机电/装饰等）、`wbs_id`。BOQ 绑定 WBS，金额/数量自动汇总到结构。

---

## 29.5 预算（Budget）模型

主表 `project.budget`：`version`、`version_date`、`project_id`、`is_active`、`amount_cost_total`、`amount_revenue_total`。  
明细 `project.budget.line`：`boq_line_id`、`budget_qty`、`budget_price`、`budget_amount`。预算必须与 BOQ 一一对应。

---

## 29.6 合同（Contract）模型

主表 `project.contract`：`type`（income/subcontract/purchase）、`partner_id`、`amount_total`、`signed_date`。  
明细 `project.contract.line`：`boq_line_id`、`qty`、`price`、`amount`、`wbs_id`。承诺成本 = 成本类合同金额之和。

---

## 29.7 变更（Change）/ 签证（Claim）

`project.change.order` 字段：`category`（change/claim）、`boq_line_id`、`qty_change`、`amount_change`、`reason`，挂 WBS/BOQ 保持结构化。

---

## 29.8 产值（Progress）模型

主表 `project.progress.entry`：`period`、`project_id`、`progress_amount_period`、`progress_amount_cum`。  
明细 `project.progress.line`：`boq_line_id`、`qty_period/qty_cum`、`amount_period/amount_cum`。

---

## 29.9 成本台账（Cost Ledger）

`project.cost.ledger` 字段：`boq_line_id`、`wbs_id`、`contract_id`、`amount`、`amount_tax`、`vendor_id`、`cost_type`（人工/材料/机械/分包/其他）、`date`。汇总到 `project.project.actual_cost_total`。

---

## 29.10 结算（Settlement）

`project.settlement` / `project.settlement.line`：`settlement_type`（income/cost）、`boq_line_id`、`amount_contract`、`amount_change`、`amount_progress`、`amount_final`。用于最终利润：`final_profit = final_income - final_cost`。

---

## 29.11 数据血缘（Data Lineage）

收入线：`Contract → Change → Progress → Settlement → Revenue Recognition`  
成本线：`Budget → Contract(成本) → Ledger → Settlement`  
工程结构线：`WBS → BOQ → Progress / Change / Ledger / Settlement`

---

## 29.12 数据仓库准备（DW）

预留 3 张宽表：  
- BOQ_Fact：BOQ 基础 + 预算/合同/变更/产值/成本/结算  
- Project_KPI_Fact：预算/承诺/实际/变更金额、进度偏差、资金压力、健康指数  
- Ledger_Fact：台账金额、科目、合同来源、清单映射

---

## 29.13 性能优化（大项目）

大项目规模：2 万 BOQ / 1 万 WBS / 10 万台账。优化建议：  
- 为 `boq_line_id`、`wbs_id`、`project_id`、`contract_id`、`date`、`cost_type` 建索引  
- 累计类 compute 做定时缓存  
- 批量导入用 batch_create  
- 表单视图精简 One2many 字段加载

---

## 29.14 小结

已具备：工程结构化索引（WBS+BOQ）、完整经营链路模型（Budget→Contract→Change→Ledger→Progress→Settlement）、数据血缘、星型建模准备、性能优化、可支撑 PMO 的集团级数据体系。

---

# 第 30 章｜智慧工地 + BIM + IoT + AI 融合架构设计

目标：让智慧工地技术能力（BIM/IoT/AI）挂接到既有数字底座（BOQ/WBS/预算/合同/产值/成本/结算），作为经营系统的能力插件，而不是第二套孤岛系统。

---

## 30.1 能力总览：行业 TOP 级智慧工地架构

包含 AI 自动识别（图纸/模型/图像）、BIM 5D（模型+工程量+成本+进度）、现场 IoT（塔吊/升降机/扬尘/监控）、现场管理（人员/机械/安全/质量），关键是全部挂到 BOQ/WBS 的经营体系。

---

## 30.2 智慧工地统一结构化模型（统一到 WBS）

智慧工地事件可映射：空间（区域/楼层/构件）、业务（BOQ/WBS）、行为（施工/安全/质量/进度/材料/机械）。统一事件模型：

```
sc.event
├── type (progress / safety / quality / material / equipment / ai)
├── wbs_id
├── boq_line_id
├── bim_element_id
├── location / floor
├── timestamp
├── payload(json)
```

形成链路：AI/IoT/BIM → Event → WBS → BOQ → 成本/合同/产值/变更 → 驾驶舱。

---

## 30.3 BIM 深度融合（5D）

### 30.3.1 BIM 模型结构

`bim.element`: `ifc_guid`、`name`、`category`（墙/梁/柱/板等）、`wbs_id`、`boq_line_id`、`geometry`。每个构件映射 WBS/BOQ。

### 30.3.2 BIM + BOQ 算量自动化

构件体积/面积/长度 → 自动写回 BOQ `quantity`；校验 BOQ 与模型算量差异。

### 30.3.3 BIM + Progress（模型驱动进度）

现场完成事件→标记 `bim.element.state`，自动生成 `project.progress.line`，模型驱动进度与产值入经营体系。

---

## 30.4 IoT 融合设计

常见 IoT：人员实名制、塔吊吊重、升降机、扬尘噪声、环境、摄像头/AI。全部落到 `sc.event`：事件类型+时间+项目+WBS/BOQ+payload。触发警告、记录、进度更新、成本预测调整、驾驶舱提示。示例：塔吊吊次→实际工作量→挂 BOQ→形成产值；升降机记录→工日推算→成本预测。

---

## 30.5 AI 能力融合

### 30.5.1 AI 图纸识别（自动算量）

识别墙体/柱/体积/钢筋/开洞等 → 写回 `boq_line.quantity`。

### 30.5.2 AI 施工影像识别

识别砌墙/钢筋绑扎/浇筑/安全帽/材料到场 → 生成 `sc.event`(progress/safety/material)，自动更新经营数据。

### 30.5.3 AI 自动生成签证、变更

事件触发变更草稿（附证据：摄像/IoT 气象），设计变更→AI 分析清单调整→更新 BOQ→生成变更单。

### 30.5.4 AI 驱动精益预测（Lean Prediction）

基于工程量、进度、合同、实际成本、IoT 数据 → 输出成本预测(EAC)、现金流预测、延期/超预算风险、人员/机械不足趋势。

---

## 30.6 产品竞争力总结

- 唯一实现“经营 + 智慧工地 + BIM + AI 全链路”的轻量级 ERP  
- WBS/BOQ 统一结构化底座  
- 智慧工地事件自动映射经营数据  
- 自动算量（图纸/BIM）、模型驱动进度、IoT 驱动产值  
- AI 自动生成变更/签证，AI 风险预测

可向房建、市政、轨道、基建推广，达到行业天花板级设计高度。

---

# 附录 A｜系统级术语表（Glossary）

- WBS：Work Breakdown Structure，工程结构树，所有业务数据的主索引。  
- BOQ：Bill of Quantities，工程量清单，量价与经营的业务主键。  
- 预算：目标成本基线，施工图预算/控制价。  
- 标后：投标报价（post-bid），中标前后形成的报价版本。  
- 合同价：签约价/动态合同价（含变更/签证）。  
- 变更：设计/现场引起的合同增减。  
- 签证：现场零星/临时新增工作，合同外附加款项。  
- 结算：合同收尾的审定价（收入/成本）。  
- 台账：实际成本事实记录（project.cost.ledger）。  
- EAC：Estimate at Completion，完工预测成本/收入。  
- CPI/SPI：成本绩效指数/进度绩效指数（EV/AC, EV/PV）。  
- EV/PV/AC：挣值/计划值/实际成本。

---

# 附录 B｜跨模块数据一致性原则（DRM 数据责任模型）

| 数据对象     | 主存放位置              | 其他模块以它为准？ |
| ---------- | -------------------- | ------------- |
| 清单工程量    | BOQ（project.boq.line） | 是            |
| 清单单价     | 合同（contract line）   | 是            |
| 变更/签证    | 变更/签证模块（change/visa） | 是（最终调整合同/预算） |
| 工程量实绩    | 计量/进度（progress）     | 是            |
| 成本实绩     | 台账（cost.ledger）      | 是            |
| 结算金额     | 结算模块（settlement）     | 是（终局价款）    |
| 收款/付款记录  | 财务/付款/收款模块          | 是（现金流口径）   |

原则：单一事实来源（SSOT），各模块读取时遵循主存放位置；变更/签证对合同与预算的调整通过审批落账；计量更新产值口径，台账更新成本口径，结算锁定终局价款。

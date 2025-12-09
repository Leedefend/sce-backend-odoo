# BOQ 模型与视图现状梳理（ProjectBoqLine）

## 模型基础信息
- 模型：`project.boq.line`
- `_order`: `project_id, section_type, parent_path, sequence, id`
- 树结构：`_parent_store = True`，`_parent_name = "parent_id"`，层级字段 `parent_path` / `level`

## 字段清单（含类型/索引/说明）
- `project_id` (Many2one, required, index): 所属项目，ondelete=cascade
- `parent_id` (Many2one, index): 上级清单，ondelete=cascade
- `child_ids` (One2many): 下级清单
- `parent_path` (Char, index): 树路径，由 `_parent_store` 维护
- `level` (Integer, compute/store): 层级深度；1 为顶级
- `sequence` (Integer, default=10): 序号/拖拽排序
- `section_type` (Selection): 工程类别（建筑/安装/装饰/景观/其他），用于统计
- `code` (Char, required, index): 清单编码
- `name` (Char, required): 清单名称
- `spec` (Char): 规格/项目特征
- `division_name` (Char, index): 分部工程名称
- `single_name` (Char, index): 单项工程名称（表头/模板解析）
- `unit_name` (Char, index): 单位工程/单体/标段名称
- `major_name` (Char, index): 专业名称（表头【】内）
- `uom_id` (Many2one, required): 计量单位
- `quantity` (Float, default=0.0): 工程量
- `price` (Monetary): 单价（currency_field=`currency_id`）
- `amount` (Monetary, compute/store/recursive=True): 合价；`item` 行=quantity*price，其他行=子行合计或自身数量*单价
- `has_warning` (Boolean, readonly): 是否有警告
- `warning_message` (Char, readonly): 警告信息
- `currency_id` (Many2one, related/company currency, store/readonly): 币种
- `cost_item_id` (Many2one): 成本项（字典 type=cost_item）
- `task_id` (Many2one, index): 关联任务，ondelete=set null
- `structure_id` (Many2one, index, recursive=True): 工程结构节点，ondelete=set null
- `unit_structure_id` (Many2one, index, compute/store): 所属单位工程节点
- `single_structure_id` (Many2one, index, compute/store): 所属单项工程节点
- `work_id` (Many2one, index): 施工工序结构，ondelete=set null
- `remark` (Char): 备注
- `is_provisional` (Boolean): 暂列/暂估标记
- `category` (Selection, index): 项目类别（分部分项/措施/其他）
- `boq_category` (Selection, index, default=`boq`): 清单类别（boq/unit_measure/total_measure/fee/tax/other），用于区分类目
- `fee_type_id` (Many2one): 规费类别（字典 type=fee_type）
- `tax_type_id` (Many2one): 税种（字典 type=tax_type）
- `code_cat` / `code_prof` / `code_division` / `code_subdivision` / `code_item` (Char, compute/store/index): 12 位编码分段
- `source_type` (Selection, index, default=`contract`): 清单来源（招标/合同/结算）
- `version` (Char, index): 版本号/批次
- `sheet_index` (Integer): 来源 Sheet 序号
- `sheet_name` (Char): 来源 Sheet 名称
- `line_type` (Selection, index, default=`item`, help=章/分部/汇总/清单项): 行类型；导入和层级推断核心

## 视图展示字段（当前 XML）
- **Tree** (`default_order="section_type, parent_path, sequence, id"`, `decoration-bf="line_type != 'item'"`)
  - 隐藏：parent_id, line_type
  - 序号：sequence(handle)
  - 名称：name（显示缩进）
  - 层级：level (readonly, optional hide)
  - 工程维度：project_id, section_type, single_name, unit_name, major_name, category, is_provisional, source_type, version, code_division, code_subdivision
  - 编码特征：code, spec
  - 计量计价：uom_id, quantity, price, amount(sum="工程合价")
  - 预警：has_warning(boolean_toggle), warning_message
  - 关联：cost_item_id, structure_id, task_id, remark

- **Form**
  - 基本信息：project_id, section_type, category, is_provisional, sequence, code, name, spec
  - 层级：parent_id, level(readonly)
  - 工程属性：single_name, unit_name, major_name(readonly); source_type, version, sheet_index(readonly), sheet_name(readonly), structure_id(readonly), task_id(readonly)
  - 计量计价：uom_id, quantity, price, amount(readonly)
  - 关联/备注：cost_item_id, remark
  - 子表页签 child_ids（可编辑）：sequence(handle), code, name, category, uom_id, quantity, price, amount(readonly)

- **Pivot**
  - 度量：amount(合价), quantity(隐)
  - 维度：project_id, section_type, major_name, division_name, category(optional), line_type(optional)

- **Search**
  - 条件：project_id, name, code, section_type, major_name, division_name, category, single_name, unit_name, source_type, version
  - 过滤：仅清单项(line_type=item), 仅有警告(has_warning)
  - 分组：项目/工程类别/专业/分部/类别/单项工程/单位工程/来源/版本/行类型
  - 其他：仅暂列/暂估(is_provisional)

- **Actions**
  - 主列表 `action_project_boq_line`: view_mode tree,form,pivot；默认按项目分组；权限 group_sc_user/manager
  - 分析 `action_project_boq_line_analysis`: view_mode tree,pivot,graph；默认 context search_default_project_id=active_id

## 已知问题清单（现状）
- 层级展示依赖导入阶段的 `line_type` + `_create_with_hierarchy` 推断，未做统一重算/校验。
- `parent_path` 仅依赖 `_parent_store`，缺乏统一重建工具，历史数据可能有偏差。
- `group` vs `item` 业务语义不够清晰（章节/汇总行无显式标记），视图仅用装饰区分。
- 展示顺序依赖导入顺序 + sequence，和 Excel 原顺序可能不完全一致。
- 视图缺少对章节/分部的显式区分样式，阅读大表时需依赖装饰和缩进。
- 汇总节点金额依赖子节点合计，若层级或导入错位会导致金额显示异常。

# BOQ-01 · 模型定义：project.boq.line

## 1. 模型概览

- 模型：`project.boq.line`
- 含义：工程量清单条目（支持平铺 + 树状层级）
- 特点：
  - 同一项目下允许重复清单编码（通过特征/备注区分部位）
  - 支持分部/单项/单位工程等维度
  - 支持树状层级（章/节/子目/清单项）
  - 预留费用类型、来源版本、导入来源等字段

---

## 2. 字段分组

### 2.1 基础字段

| 字段名        | 类型        | 说明                         |
|---------------|-------------|------------------------------|
| `project_id`  | Many2one    | 所属项目，必填              |
| `code`        | Char        | 清单编码，必填              |
| `name`        | Char        | 清单名称，必填              |
| `spec`        | Char        | 规格/项目特征               |
| `remark`      | Char        | 备注                         |
| `sequence`    | Integer     | 序号，用于排序              |
| `section_type`| Selection   | 工程类别（建筑/安装/装饰等）|
| `is_provisional` | Boolean  | 是否暂列/暂估               |

---

### 2.2 工程结构维度（平铺型）

这些字段主要反映“清单在工程结构中的定位”，来自表头或结构定义。

| 字段名         | 类型    | 说明                                   |
|----------------|---------|----------------------------------------|
| `division_name`| Char    | 分部工程名称                           |
| `single_name`  | Char    | 单项工程名称                           |
| `unit_name`    | Char    | 单位工程/单体/标段名称                 |
| `major_name`   | Char    | 专业名称（如“建筑与装饰工程”等）      |

> 说明：这些字段大多来自招标清单表头或导入模板，用于后续统计与过滤。

---

### 2.3 工程量与价格字段

| 字段名     | 类型        | 说明                        |
|------------|-------------|-----------------------------|
| `uom_id`   | Many2one    | 单位（计量单位）            |
| `quantity` | Float       | 工程量                      |
| `price`    | Monetary    | 单价（综合单价）            |
| `amount`   | Monetary    | 合价 = quantity × price（计算字段） |
| `currency_id` | Many2one | 币种（通常来自项目公司币别） |

---

### 2.4 清单类别与费用类型

| 字段名       | 类型      | 说明                                      |
|--------------|-----------|-------------------------------------------|
| `category`   | Selection | 项目类别：分部分项/措施/其他             |
| `boq_category` | Selection | 清单类别：分部分项/单价措施/总价措施/规费/税金/其他 |
| `fee_type_id` | Many2one | 规费类别（数据字典：`fee_type`）         |
| `tax_type_id` | Many2one | 税种（数据字典：`tax_type`）             |
| `cost_item_id` | Many2one| 成本项（字典：`cost_item`）              |

---

### 2.5 树状层级字段（本次新增）

为支持“章 → 节 → 子目 → 清单项”的层级展示，本次新增：

| 字段名       | 类型        | 说明                                  |
|--------------|-------------|---------------------------------------|
| `parent_id`  | Many2one    | 上级清单条目                          |
| `child_ids`  | One2many    | 下级清单条目                          |
| `parent_path`| Char        | Odoo 内部用的路径字段（_parent_store）|
| `level`      | Integer     | 层级（0=顶级，1=下一级，以此类推）    |

> 说明：  
> - 启用 `_parent_store = True` + `_parent_name = "parent_id"`，支持高效树查询。  
> - `level` 基于 `parent_path` 自动计算，用于视图展示与筛选。

---

### 2.6 工程/施工结构关联

| 字段名              | 类型        | 说明                                  |
|---------------------|-------------|---------------------------------------|
| `structure_id`      | Many2one    | 工程结构节点（`sc.project.structure`）|
| `unit_structure_id` | Many2one    | 计算所得：所属单位工程节点           |
| `single_structure_id` | Many2one  | 计算所得：所属单项工程节点           |
| `work_id`           | Many2one    | 施工工序结构（`construction.work.breakdown`）|
| `task_id`           | Many2one    | 关联任务（`project.task`）            |

---

### 2.7 编码分段字段（12 位清单编码）

| 字段名           | 类型  | 说明                   |
|------------------|-------|------------------------|
| `code_cat`       | Char  | 工程分类码（前 2 位）  |
| `code_prof`      | Char  | 专业工程码（前 4 位）  |
| `code_division`  | Char  | 分部工程码（前 6 位）  |
| `code_subdivision` | Char| 分项工程码（前 9 位）  |
| `code_item`      | Char  | 清单项目码（完整 12 位）|

> 说明：仅当 `code` 为 12 位纯数字时拆分生效，否则全部置空。

---

### 2.8 来源与导入信息

| 字段名      | 类型      | 说明                                   |
|-------------|-----------|----------------------------------------|
| `source_type` | Selection | 清单来源：招标/合同/结算               |
| `version`   | Char      | 版本号/批次，用于多次导入管理          |
| `sheet_index` | Integer | 导入来源 Sheet 序号                    |
| `sheet_name`  | Char    | 导入来源 Sheet 名称                    |

---

## 3. 与其他模块的关系

- 与 `project.project`：一对多，一个项目下多条清单
- 与 `sc.project.structure`：桥接模型，实现 BOQ ↔ 工程结构的绑定
- 与 `project.task`：支持任务维度与清单对应
- 与成本域模型（未来）：预算行、合同行、结算行可复用本模型核心字段

---

## 4. 后续扩展方向

- `quantity` / `price` 精细化拆分（人工、材料、机械）
- `spec` 升级为结构化 JSON 字段
- 引入 `waste_rate`、`tax_rate` 等价格附加参数
- 增加「清单版本快照」模型，支持历史版本追踪

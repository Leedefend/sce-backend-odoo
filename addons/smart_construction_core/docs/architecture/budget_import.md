# 项目预算导入指南

项目预算支持通过 Odoo 原生 CSV/Excel 导入能力批量创建预算版本和预算清单行。请在“项目预算”列表或表单中使用“导入”功能。

| 列名 | 示例值 | 说明 |
| --- | --- | --- |
| `project_id/id` | `your_module.project_external_id` | 必填。项目 External ID；也可以在导入向导中按数据库 ID 映射。 |
| `contract_id/id` | `your_module.contract_external_id` | 可选。关联合同或成本中心。 |
| `name` | `控制版 V1` | 预算名称。 |
| `version` | `CTRL-V1` | 版本号。缺省时系统可按项目生成版本序列。 |
| `line_ids/0/boq_code` | `BOQ-100` | 第一行清单编码。 |
| `line_ids/0/name` | `桥梁桩基` | 第一行清单名称。 |
| `line_ids/0/wbs_id/id` | `your_module.wbs_external_id` | 可选。关联 WBS 分部分项。 |
| `line_ids/0/qty_bidded` | `120` | 预算工程量。 |
| `line_ids/0/uom_id/id` | `uom.product_uom_meter` | 计量单位 External ID。 |
| `line_ids/0/price_bidded` | `850` | 综合单价。 |
| `line_ids/0/amount_bidded` | `102000` | 合价；可提供，也可由系统按数量和单价计算。 |

`line_ids/0/...` 表示第一行预算清单，`line_ids/1/...` 表示第二行，以此类推。导入完成后，可以在预算表单的预算清单页签继续编辑，并按成本科目拆分预算金额。

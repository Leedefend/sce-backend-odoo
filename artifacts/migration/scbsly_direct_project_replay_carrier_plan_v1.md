# SCBSLY Direct Project Replay Carrier Plan v1

Status: `READY_FOR_REPLAY_IMPLEMENTATION_WITH_BLOCKERS`
Generated At: `2026-05-30T07:18:50.884976+00:00`

| Bucket | Count | Old Rows |
| --- | ---: | ---: |
| legacy_fuel_carrier_added_requires_replay | 3 | 540 |
| existing_carrier_requires_identity_replay_or_scoped_surface | 21 | 48250 |
| menu_alias_added_requires_replay | 7 | 27621 |
| menu_alias_added_empty_old_list | 1 | 0 |
| report_route_no_row_replay | 2 | 0 |

## Rows

| P | 分类 | 菜单 | Bucket | Target Model | Old | New | Identity | Menu Patch |
| ---: | --- | --- | --- | --- | ---: | ---: | --- | --- |
| 20 | 费用与资金管理类单据 | 充值登记 | legacy_fuel_carrier_added_requires_replay | `sc.legacy.fuel.card.recharge.fact` | 32 |  | `DJBH` |  |
| 20 | 费用与资金管理类单据 | 加油登记 | legacy_fuel_carrier_added_requires_replay | `sc.legacy.fuel.card.refuel.fact` | 500 |  | `DJBH` |  |
| 20 | 费用与资金管理类单据 | 油卡登记 | legacy_fuel_carrier_added_requires_replay | `sc.legacy.fuel.card.fact` | 8 |  | `DJBH` |  |
| 30 | 材料管理类单据 | 入库 | existing_carrier_requires_identity_replay_or_scoped_surface | `sc.material.inbound` | 13171 | 400 | `RowIndex` |  |
| 30 | 费用与资金管理类单据 | 往来单位付款 | existing_carrier_requires_identity_replay_or_scoped_surface | `sc.payment.execution` | 10342 | 13690 | `DJBH` |  |
| 30 | 费用与资金管理类单据 | 进项上报 | existing_carrier_requires_identity_replay_or_scoped_surface | `sc.legacy.invoice.tax.fact` | 6389 | 25087 | `RowIndex` |  |
| 30 | 费用与资金管理类单据 | 项目费用报销单 | existing_carrier_requires_identity_replay_or_scoped_surface | `sc.expense.claim` | 5802 | 0 | `DJBH` |  |
| 35 | 劳务管理类单据 | 零星用工 | menu_alias_added_requires_replay | `sc.labor.usage` | 8769 |  | `RowIndex` | menu_sc_labor_casual_acceptance |
| 35 | 机械与租赁管理类单据 | 机械台班记录 | menu_alias_added_requires_replay | `sc.equipment.usage` | 17495 |  | `RowIndex` | menu_sc_equipment_shift_acceptance |
| 40 | 分包管理类单据 | 分包方单 | menu_alias_added_requires_replay | `sc.subcontract.request` | 721 |  | `RowIndex` | menu_sc_subcontract_request_acceptance |
| 40 | 分包管理类单据 | 分包结算单 | existing_carrier_requires_identity_replay_or_scoped_surface | `sc.subcontract.settlement` | 88 | 0 | `DJBH` |  |
| 40 | 劳务管理类单据 | 劳务结算 | existing_carrier_requires_identity_replay_or_scoped_surface | `sc.labor.settlement` | 576 | 0 | `DJBH` |  |
| 40 | 劳务管理类单据 | 方单 | menu_alias_added_requires_replay | `sc.labor.usage` | 252 |  | `DJBH` | menu_sc_labor_usage_acceptance |
| 40 | 合同类单据 | 供货合同 | existing_carrier_requires_identity_replay_or_scoped_surface | `sc.legacy.supplier.contract.pricing.fact` | 848 | 5565 | `Id` |  |
| 40 | 合同类单据 | 分包合同 | existing_carrier_requires_identity_replay_or_scoped_surface | `construction.contract.expense` | 86 | 215 | `DJBH` |  |
| 40 | 合同类单据 | 劳务合同 | existing_carrier_requires_identity_replay_or_scoped_surface | `construction.contract.expense` | 187 | 439 | `DJBH` |  |
| 40 | 合同类单据 | 施工合同 | existing_carrier_requires_identity_replay_or_scoped_surface | `construction.contract` | 182 | 1561 | `DJBH` |  |
| 40 | 合同类单据 | 机械合同（合同） | menu_alias_added_requires_replay | `sc.equipment.request` | 221 |  | `DJBH` | menu_sc_equipment_contract_acceptance |
| 40 | 合同类单据 | 租赁合同 | existing_carrier_requires_identity_replay_or_scoped_surface | `construction.contract.expense` | 221 | 423 | `DJBH` |  |
| 40 | 机械与租赁管理类单据 | 机械结算单 | existing_carrier_requires_identity_replay_or_scoped_surface | `sc.equipment.settlement` | 669 | 0 | `DJBH` |  |
| 40 | 机械与租赁管理类单据 | 租赁结算单 | existing_carrier_requires_identity_replay_or_scoped_surface | `sc.material.rental.settlement` | 669 | 1 | `DJBH` |  |
| 40 | 机械与租赁管理类单据 | 还租 | menu_alias_added_requires_replay | `sc.material.rental.order` | 37 |  | `DJBH` | menu_sc_material_rental_return_acceptance |
| 40 | 材料管理类单据 | 报价单 | menu_alias_added_requires_replay | `sc.material.rfq` | 126 |  | `RowIndex` | menu_sc_material_quote_acceptance |
| 40 | 材料管理类单据 | 材料结算单 | existing_carrier_requires_identity_replay_or_scoped_surface | `sc.material.settlement` | 1214 | 0 | `DJBH` |  |
| 40 | 材料管理类单据 | 材料计划 | existing_carrier_requires_identity_replay_or_scoped_surface | `project.material.plan` | 686 | 1 | `RowIndex` |  |
| 40 | 费用与资金管理类单据 | 工程结算单 | existing_carrier_requires_identity_replay_or_scoped_surface | `sc.settlement.order` | 37 | 2 | `DJBH` |  |
| 40 | 费用与资金管理类单据 | 工程进度收款 | existing_carrier_requires_identity_replay_or_scoped_surface | `sc.legacy.engineering.progress.receipt` | 639 | 3259 | `Id` |  |
| 40 | 费用与资金管理类单据 | 总包进项上报 | existing_carrier_requires_identity_replay_or_scoped_surface | `sc.invoice.registration` | 383 | 1919 | `DJBH` |  |
| 40 | 费用与资金管理类单据 | 支付申请 | existing_carrier_requires_identity_replay_or_scoped_surface | `payment.request` | 2595 | 13595 | `DJBH` |  |
| 40 | 费用与资金管理类单据 | 管理人员工资表 | existing_carrier_requires_identity_replay_or_scoped_surface | `sc.hr.payroll.document` | 233 | 3398 | `DJBH` |  |
| 40 | 项目管理类单据 | 施工日志（新） | existing_carrier_requires_identity_replay_or_scoped_surface | `sc.construction.diary` | 3233 | 5665 | `DJBH` |  |
| 70 | 机械与租赁管理类单据 | 租入 | menu_alias_added_empty_old_list | `sc.material.rental.order` | 0 |  | `` | menu_sc_material_rental_in_acceptance |
| 90 | 材料管理类单据 | 库存统计表（新） | report_route_no_row_replay | `sc.material.stock.summary` | 0 | 14 | `` |  |
| 90 | 费用与资金管理类单据 | 成本统计表（数据） | report_route_no_row_replay | `sc.comprehensive.cost.summary` | 0 | 840 | `` |  |

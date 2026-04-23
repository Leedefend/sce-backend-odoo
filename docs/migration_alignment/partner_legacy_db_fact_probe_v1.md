# 旧库 Partner 业务事实只读探针 v1

任务：`ITER-2026-04-13-1844`

## 连接范围

- 容器：`legacy-sqlserver`
- 数据库：`LegacyDb`
- 模式：只读 `SELECT`
- 输出：`artifacts/migration/partner_import_decision_support_v1.json`

本轮未写旧库，未写 Odoo，未创建 partner，未导入合同。

## 查询对象

- `dbo.T_Base_CooperatCompany`
- `dbo.T_Base_SupplierInfo`
- `dbo.T_ProjectContract_Out`
- `dbo.C_ZFSQGL`
- `dbo.C_JFHKLR`

## 已确认事实

探针状态：`PASS`

关键事实：

- `T_Base_CooperatCompany` 行数 7864，具备统一社会信用代码与税号字段，适合作为 partner 主源。
- `T_Base_SupplierInfo` 行数 3041，但统一社会信用代码和税号统计均为 0，更适合作为补充信息源。
- company/supplier 跨源同名很高，不能按名称自动合并。
- `C_JFHKLR.WLDWID` 强烈指向 company，支持回款/收款侧往来单位从 company 承接。
- `C_JFHKLR.SGHTID` 可以反推出 628 个单一回款相对方合同。

## 与 CSV 盘点差异说明

旧库聚合与 CSV 文件盘点存在少量差异，例如 company 重名名称数与 `FBF` 单一命中数不同。后续以旧库业务 ID 引用关系作为更高优先级事实，CSV 继续作为导出对照与模板准备输入。

## 风险

- 单一回款相对方不等于合同法务相对方，仍需人工确认；
- 多个回款相对方的 48 个合同不能进入首批强证据切片；
- `CBF` 歧义过高，应从首批合同相对方创建依据中排除；
- supplier 补充信息需要有明确合并键，不能按同名自动覆盖 company。


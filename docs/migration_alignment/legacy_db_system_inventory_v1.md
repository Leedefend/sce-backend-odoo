# 旧库系统盘点 v1

任务：`ITER-2026-04-13-1850`

## 范围

- 数据库：`LegacyDb`
- 模式：只读 `SELECT`
- 输出：`artifacts/migration/legacy_db_full_rebuild_blueprint_v1.json`

本轮不写旧库，不写 Odoo，不导入数据。

## 核心业务表规模

| 表 | 行数 |
|---|---:|
| `BASE_SYSTEM_PROJECT` | 755 |
| `T_System_XMGL` | 721 |
| `BASE_SYSTEM_PROJECT_USER` | 21390 |
| `T_ProjectContract_Out` | 1694 |
| `C_ZFSQGL` | 本轮仅做引用画像 |
| `C_JFHKLR` | 7412 |
| `T_Base_CooperatCompany` | 7864 |
| `T_Base_SupplierInfo` | 3041 |
| `BASE_SYSTEM_FILE` | 126967 |
| `T_BILL_FILE` | 51964 |
| `BASE_SYSTEM_MENU` | 1827 |
| `ts_function` | 3079 |

## Top 大表信号

旧库最大表不是项目/合同，而是物料、流程、日志、附件类数据：

| 表 | 行数 |
|---|---:|
| `T_Base_MaterialDetail` | 2279734 |
| `ts_function_RecordUserClick` | 510288 |
| `S_Execute_Detail_Step` | 165532 |
| `S_Execute_Approval` | 163245 |
| `ts_rolefunction_History` | 143089 |
| `C_Base_CBFL` | 130605 |
| `BASE_SYSTEM_FILE` | 126967 |
| `ts_system_loginData` | 122046 |
| `CheckInData` | 106208 |
| `BASE_LOWCODE_HISTORYDATA` | 97037 |
| `S_Execute_OtherReader` | 87759 |
| `S_Execute_DetailStatus` | 81622 |
| `T_BASE_TASKDONE` | 78822 |
| `BASE_SYSTEM_LOG` | 78350 |
| `T_BILL_FILE` | 51964 |

## 关键事实

| 指标 | 数量 |
|---|---:|
| 项目行 | 755 |
| 项目删除态 | 61 |
| 项目 `OTHER_SYSTEM_ID` 非空 | 696 |
| 项目成员行 | 21390 |
| 合同行 | 1694 |
| 合同删除态 | 65 |
| 合同项目命中 `BASE_SYSTEM_PROJECT` | 1606 |
| 合同去重项目 ID | 762 |
| 合作单位行 | 7864 |
| 合作单位删除态 | 676 |
| 合作单位有统一社会信用代码 | 3964 |
| 供应商行 | 3041 |
| 供应商银行账号非空 | 2521 |
| 回款行 | 7412 |
| 回款关联合同行 | 1857 |
| 单一回款相对方合同 | 628 |

## 初步判断

完整新库重建不能只按 CSV 顺序导入。应先完成 partner 和 project 主数据，再导入 contract 骨架，之后才进入回款、付款、附件和流程类数据。


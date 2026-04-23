# Partner 字段实施清单 v1

任务：`ITER-2026-04-13-1849`

## 新增字段

| 字段 | 类型 | 索引 | 用途 |
|---|---|---|---|
| `legacy_partner_id` | Char | Yes | 旧系统 partner ID |
| `legacy_partner_source` | Selection | Yes | 旧系统来源表 |
| `legacy_partner_name` | Char | No | 旧名称快照 |
| `legacy_credit_code` | Char | No | 统一社会信用代码辅助校验 |
| `legacy_tax_no` | Char | No | 税号辅助校验 |
| `legacy_deleted_flag` | Char | No | 旧系统删除标志 |
| `legacy_source_evidence` | Char | No | 旧系统证据路径 |

## 未实施项

- 未新增 SQL 唯一约束；
- 未新增菜单；
- 未新增 ACL；
- 未修改 manifest；
- 未修改前端；
- 未创建 partner 数据；
- 未导入合同数据。

## 验证要求

- Python 语法检查；
- 静态门禁；
- `smart_construction_core` 模块升级；
- `sc_demo` 中 `res.partner` 字段物化检查。


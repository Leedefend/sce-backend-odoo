# SCBSLY 历史付款申请依据口径收口说明

日期：2026-06-14

## 业务结论

新系统标准口径是：

`合同/结算单 -> 支付申请 -> 付款执行/付款台账`

SCBSLY 旧系统实际口径是：

`支付申请 -> 支付申请明细关系 -> 合同/结算/发票/入库/零星用工等来源单据`

因此迁移后分两层处理：

1. 新办业务继续按新系统标准口径办理，不放宽为任意来源单据。
2. 历史续办保留旧系统关系事实，作为历史关联依据展示和放行，避免历史单据因旧系统口径宽松而无法继续办理。

## 当前 sc_demo 数据结果

范围：`payment_request.legacy_source_table = SCBSLY_DIRECT_PAYMENT_APPLY_ACCEPTED`

总数：`2598`

按 `payment_basis_type` 归类：

| 依据口径 | 数量 | 含义 |
| --- | ---: | --- |
| 标准结算单 | 1398 | 付款申请主表直接关联 `sc.settlement.order` |
| 明细结算单 | 369 | 付款申请明细关联一张或多张 `sc.settlement.order` |
| 合同依据 | 49 | 无结算但已安全匹配 `construction.contract` |
| 历史关联依据 | 256 | 无新系统合同/结算锚点，但旧系统关系明细有可解释来源 |
| 无可解释依据 | 526 | 旧系统没有可用来源关系，或关系为空 |

## 已补齐内容

### 结算关系

脚本：

`scripts/migration/scbsly_payment_settlement_relation_backfill_write.py`

结果：

- 旧系统关系明细：`6434` 行
- 有结算单匹配的明细：`2540` 行
- 单结算主表回填：`1398` 张付款申请
- 多结算保留在明细层：`335` 张付款申请

### 缺失结算实体占位

脚本：

`scripts/migration/scbsly_missing_payment_settlement_placeholder_backfill.py`

用途：旧系统关系明确指向结算类型，但当前库没有对应结算实体时，生成历史占位 `sc.settlement.order`，只挂到付款申请明细，不强行写主表结算。

结果：

- 创建历史占位结算单：`34` 张
- 回写付款申请明细：`38` 行
- 未匹配结算类型关系行：`38 -> 0`

### 合同依据

脚本：

`scripts/migration/scbsly_payment_contract_basis_backfill.py`

安全规则：

- 只处理无结算/无材料结算/无合同/无明细结算的历史付款申请。
- 旧系统合同关系必须匹配唯一新系统合同。
- 项目、往来单位、申请方向必须一致。

结果：

- 安全写入合同依据：`49` 张付款申请

### 历史关联依据

新增字段：

- `payment.request.payment_basis_type`
- `payment.request.legacy_relation_count`
- `payment.request.legacy_relation_summary`

用途：

- 把旧系统关系明细整理成用户可见的业务依据摘要。
- 明确区分标准结算、明细结算、合同依据、历史关联依据、无可解释依据。
- 对有可解释旧关系明细的历史付款申请放行付款执行锚点校验。

## 剩余边界

`无可解释依据 = 526`

拆分：

- `361` 张：旧系统关系表中没有关系行。
- `165` 张：旧系统关系表有一行，但来源类型和来源单号均为空。

这部分不能自动推断为合同或结算。后续若业务要求继续办理，应进入人工核验或以补充附件/说明方式形成新依据。

## 验证样例

`ZFSQ-20220809-003`

- 依据口径：历史关联依据
- 历史关联依据数：45
- 摘要：零星用工单明细
- 付款执行锚点校验：通过

`ZFSQGL-20231024-001`

- 依据口径：合同依据
- 合同：`FBHT-20231023-001`
- 付款执行锚点校验：通过

`ZFSQGL-20240808-003`

- 依据口径：明细结算单
- 明细结算依据：`CLJSD-20240812-001`
- 付款执行锚点校验：通过

## 验收查询

```sql
SELECT payment_basis_type, COUNT(*)
  FROM payment_request
 WHERE legacy_source_table = 'SCBSLY_DIRECT_PAYMENT_APPLY_ACCEPTED'
 GROUP BY payment_basis_type
 ORDER BY COUNT(*) DESC;
```

```sql
WITH no_basis AS (
    SELECT id
      FROM payment_request
     WHERE legacy_source_table = 'SCBSLY_DIRECT_PAYMENT_APPLY_ACCEPTED'
       AND payment_basis_type = 'none'
),
rel AS (
    SELECT request_id,
           COUNT(*) AS line_count,
           COUNT(*) FILTER (
               WHERE COALESCE(source_line_type, '') <> ''
                  OR COALESCE(source_document_no, '') <> ''
           ) AS informative_lines
      FROM payment_request_line
     WHERE import_batch = 'scbsly_payment_settlement_relation_backfill_v1'
     GROUP BY request_id
)
SELECT COUNT(*) AS no_basis_total,
       COUNT(*) FILTER (WHERE rel.line_count IS NULL) AS no_relation_lines,
       COUNT(*) FILTER (WHERE rel.line_count > 0 AND rel.informative_lines = 0) AS only_blank_relation_lines
  FROM no_basis n
  LEFT JOIN rel ON rel.request_id = n.id;
```

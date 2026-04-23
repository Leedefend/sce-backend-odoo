# Partner 候选归一化规则 v1

任务：`ITER-2026-04-13-1843`

## 归一化规则

名称匹配时执行以下轻量清洗：

1. 去除首尾空格；
2. 合并连续空白；
3. 去除常见中文/英文括号、顿号、逗号、句点、斜杠、连字符；
4. 去除一个末尾组织后缀：
   - `有限责任公司`
   - `股份有限公司`
   - `集团有限公司`
   - `有限公司`
   - `公司`

## 不做的归一化

本轮不做以下推断：

- 不合并分公司与总公司；
- 不合并学校/大学/学院名称变体；
- 不按联系人、地址、电话推断同一主体；
- 不把 company 与 supplier 同名记录自动视为同一 partner；
- 不把多个旧源 ID 自动合并为一个新 partner；
- 不把未覆盖相对方自动创建为 partner。

## 匹配类型

| 类型 | 含义 | 下一步 |
|---|---|---|
| `company_single` | company 源唯一命中 | 人工确认后可进入写入 dry-run 候选 |
| `company_multiple` | company 源多行命中 | 人工选主或确认合并策略 |
| `cross_source_conflict` | company/supplier 均命中 | 人工确认来源优先级与是否合并 |
| `defer` | 两个源均未覆盖 | 补源或人工新建候选 |

## 人工确认输出要求

人工确认表至少应补齐：

- `confirm_result`
- `confirmed_partner_action`
- `confirmed_source`
- `confirmed_source_id`
- `review_note`

建议的 `confirmed_partner_action` 值：

- `reuse_existing`
- `create_from_company`
- `create_from_supplier`
- `merge_sources`
- `defer`
- `reject`


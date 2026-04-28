# 应收应付报表旧过程预检 Batch-AK

## 批次定位

- Layer Target：Migration Evidence / Legacy Procedure Precheck
- Module：`scripts/migration`, `docs/migration_alignment`
- 旧过程：`UP_USP_SELECT_YSYFHZB_XM_ZJ`
- 目标：进入新旧对账前，确认旧过程参数、结果集元数据和直接执行限制。

## 参数

| 参数 | 类型 | 长度 | 默认值 | 输出参数 |
| --- | --- | ---: | --- | --- |
| @XMMC | varchar | 5000 | 0 | 0 |
| @KSRQ | varchar | 200 | 0 | 0 |
| @JZRQ | varchar | 200 | 0 | 0 |

## 结果集元数据

| 序号 | 字段 | 类型 | 可空 | 错误 |
| ---: | --- | --- | --- | --- |
| 0 |  |  | NULL | The metadata could not be determined because statement 'INSERT INTO #TEMP_RESULT_ZJ     |

## 空参数执行尝试

- return_code：`0`
- line_count：`3`

样本输出：

```text
Warning: Null value is eliminated by an aggregate or other SET operation.
Msg 468, Level 16, State 9, Server 16a49df30c98, Procedure dbo.UP_USP_SELECT_YSYFHZB_XM_ZJ, Line 149
Cannot resolve the collation conflict between "Chinese_PRC_CI_AS" and "SQL_Latin1_General_CP1_CI_AS" in the equal to operation.
```

## 判断

旧过程空参数直接执行失败；对账前需要根据参数语义构造真实条件，或处理过程内部依赖限制。

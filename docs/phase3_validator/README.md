# Phase3 数据校验器使用说明

## 快速命令
- 运行 smoke 测试基线（默认只跑 sc_smoke）：  
  `make test MODULE=smart_construction_core TEST_TAGS=sc_smoke`
- 运行数据校验器并生成报告：  
  `make validate`  
  报告输出：`addons/smart_construction_core/var/validate/<db>_<timestamp>.json`

## 规则列表（code / severity / 说明）
- `SC.VAL.COMP.001` (ERROR)：采购/结算/付款公司一致性校验。
- `SC.VAL.PROJ.001` (WARN)：关键单据必须挂项目（付款申请/结算单/采购订单）。
- `SC.VAL.3WAY.001` (ERROR)：三单匹配链路完整性（付款→结算→采购）。
- `SC.VAL.AMT.001` (WARN)：金额/数量合理性（不允许负数）。

## 输出说明
- 汇总：`VALIDATE: db=<db> rules=<n> issues=<total>`
- 每条规则：`[OK|ERROR|WARN] <code>: <title> checked=<n> issues=<m>`
- 报告文件：JSON 结构化输出，位于 `addons/smart_construction_core/var/validate/`

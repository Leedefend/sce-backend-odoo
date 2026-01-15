# 初始化能力评分表（v1）

说明：每项 0/1/2 分（不可用/可用/稳定可验收）。总分 40，>=32 视为工程级可持续。

## 1. 可复现性（10）

| 指标 | 分数 | 备注 |
| --- | --- | --- |
| 同命令跨环境可复现 | 2 | make db.reset / db.demo.reset |
| reset 后无手工步骤 | 2 | verify.baseline / verify.demo |
| demo/seed 顺序清晰 | 2 | reset_verify.md |
| dbfilter 默认与放开流程明确 | 2 | db_strategy.md |
| runtime 权限检查明确 | 2 | DEPLOY_ODDO17_BASELINE.md |

## 2. 可验收性（10）

| 指标 | 分数 | 备注 |
| --- | --- | --- |
| 一键 gate 验收存在 | 2 | gate.full |
| baseline 与 demo 验收分离 | 2 | verify.baseline / verify.demo |
| audit 产物可导出 | 2 | make audit.pull |
| 失败定位入口清晰 | 2 | reset_verify.md / razor flow |
| 模块状态/标记可核验 | 2 | verify.demo 输出 |

## 3. 隔离与安全（10）

| 指标 | 分数 | 备注 |
| --- | --- | --- |
| DEV 与 DEMO/PROD 隔离 | 2 | db 命名规则 |
| 非预期 DB 不可访问 | 2 | dbfilter |
| 降噪有审计记录 | 2 | noiseoff.sql |
| seed/demo 不污染基线 | 2 | db.reset vs db.demo.reset |
| 分支库流程受控 | 2 | db_strategy.md |

## 4. 可回滚与自愈（10）

| 指标 | 分数 | 备注 |
| --- | --- | --- |
| razor flow 明确 | 2 | db_init_razor_flow.md |
| 税组/税率自愈 | 2 | core post_init_hook |
| 默认阶段归档可验证 | 2 | core post_init_hook |
| 初始化失败可恢复 | 2 | noiseon + db.rebuild |
| 最小恢复动作无隐性状态 | 2 | reset/verify 组合 |

## 当前评分（基线）

- 总分：38 / 40
- 主要扣分点：
- 运行态权限检查未自动化（计划：preflight check）
- audit 产物未进入 CI artifact（计划：ci.upload_artifacts）

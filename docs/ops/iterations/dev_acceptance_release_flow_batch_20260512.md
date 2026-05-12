# Dev Acceptance Release Flow Batch 20260512

## 1. 本轮变更

- 目标：把上传备份后的 dev 验收发布流程规范化为可重复的 Makefile 入口和 runbook。
- 完成：
  - 新增 `scripts/ops/dev_acceptance_release_probe.py`，只读校验上传包、前端发布面、API 入口和可选真实用户 `system.init`。
  - 新增 `make verify.dev.acceptance.release`。
  - 新增 `make release.dev.acceptance.publish`，串联 dev 静态包重建和发布验收探针。
  - 新增 `docs/ops/dev_acceptance_release_runbook_v1.md`。
- 未完成：未自动化数据库恢复；恢复仍需人工确认后按运行态恢复流程执行。

## 2. 影响范围

- 模块：`Makefile`、`scripts/ops/dev_acceptance_release_probe.py`、`docs/ops/dev_acceptance_release_runbook_v1.md`
- 启动链：否
- contract：否
- 路由：否

## 3. 风险

- P0：无，本批次不执行数据库写入。
- P1：验收用户密码不应写入仓库或日志；通过环境变量传入。
- P2：如果 nginx 端口被切到 80，需要显式覆盖 `ACCEPTANCE_BASE_URL`。

## 4. 验证

- 命令：
  - `python3 -m py_compile scripts/ops/dev_acceptance_release_probe.py`
  - `ENV=dev ENV_FILE=.env.dev DB_NAME=sc_demo ACCEPTANCE_BACKUP_DIR=/tmp/20260512T125816 ACCEPTANCE_BASE_URL=http://127.0.0.1:18081 make verify.dev.acceptance.release`
  - `ENV=dev ENV_FILE=.env.dev DB_NAME=sc_demo ACCEPTANCE_BACKUP_DIR=/tmp/20260512T125816 ACCEPTANCE_BASE_URL=http://127.0.0.1:18081 ACCEPTANCE_LOGIN=wutao ACCEPTANCE_PASSWORD=<redacted> make release.dev.acceptance.publish`
- 结果：PASS。上传包校验、frontend served asset、intent OPTIONS/GET、`wutao` 登录和 `system.init` 均通过。

## 5. 产物

- snapshot：N/A
- logs：N/A
- e2e：`artifacts/backend/dev_acceptance_release_probe.json`

## 6. 回滚

- commit：回退本批次文档、脚本和 Makefile target。
- 方法：删除新增 target 和脚本后继续使用原 `make verify.frontend.build` 手工验收路径。

## 7. 下一批次

- 目标：如需进一步自动化恢复，需要单独批次定义 destructive restore target、确认 DB/filestore 回滚策略和审批边界。
- 前置条件：Owner 明确允许自动化替换 dev 验收库。

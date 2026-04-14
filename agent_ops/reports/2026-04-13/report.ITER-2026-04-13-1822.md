# ITER-2026-04-13-1822 项目骨架目标身份快照非写库复演

## 任务结论

- 结果：FAIL
- 触发停止条件：`acceptance_failed`
- 失败命令：`ENV=dev DB_NAME=sc_demo make odoo.shell.exec`

## 已完成

- 创建任务契约：`agent_ops/tasks/ITER-2026-04-13-1822.yaml`
- 任务契约校验：PASS
- 通过 Makefile 确认并启动 Odoo shell 只读导出入口

## 失败原因

Odoo shell 已连接 `sc_demo` 并加载 registry，但导出脚本尝试在容器内写入：

```text
/mnt/data/migration_samples/project_existing_identity_snapshot_target_v1.csv
```

容器内 `/mnt/data` 不存在或无权限，触发：

```text
PermissionError: [Errno 13] Permission denied: '/mnt/data'
```

因此 `make odoo.shell.exec` 返回 2。

## 安全性结论

- 数据库写入：未发生
- ORM create/write/unlink：未调用
- 正式导入：未发生
- 模型/视图/字段改动：未发生
- 高风险路径改动：未发生

## 未完成产物

- `data/migration_samples/project_existing_identity_snapshot_target_v1.csv`
- `artifacts/migration/project_dry_run_target_identity_result_v1.json`
- `docs/migration_alignment/project_dry_run_target_identity_report_v1.md`
- `docs/migration_alignment/project_import_go_no_go_v3.md`
- `agent_ops/state/task_results/ITER-2026-04-13-1822.json`

## 恢复建议

新开恢复批次，改用容器确认可写的挂载路径导出身份快照，例如先写入 `/mnt/artifacts/...`，再在宿主仓库中将该快照同步到 `data/migration_samples/project_existing_identity_snapshot_target_v1.csv`，之后复跑 no-write importer。

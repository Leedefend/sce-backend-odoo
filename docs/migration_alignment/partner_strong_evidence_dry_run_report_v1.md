# 强证据 Partner Dry-Run 报告 v1

任务：`ITER-2026-04-13-1848`

## 范围

输入：

- `artifacts/migration/partner_strong_evidence_dry_run_input_v1.csv`
- 369 个强证据 partner 候选

运行方式：

- 不调用 ORM；
- 不写数据库；
- 不创建 partner；
- 只与当前 partner baseline 做名称级 create/reuse 模拟。

## 结果

| dry-run action | 数量 |
|---|---:|
| create_candidate | 369 |
| reuse_existing_exact | 0 |
| reuse_existing_normalized | 0 |
| manual_review_existing_duplicate | 0 |
| reject | 0 |

## 解释

当前 369 个强证据候选在现有 partner baseline 中没有命中可复用 partner，因此 dry-run 全部判定为 `create_candidate`。

这不等于可以真实创建。真实创建前仍需：

- partner legacy identity 字段或外部 ID 对照策略；
- 字段安全切片；
- 小样本真实写入授权；
- 写后只读复核；
- rollback dry-run。

## 重建目标适配

本 dry-run 符合 1847 的新迁移目标：

- 输入文件固定；
- 结果可重复；
- 输出逐行 action；
- 不依赖当前人工临时状态；
- 不写数据库。


# 附件补全闭环专题 v1

分支：`iteration/attachment-closure-v1`

## 目标

把历史附件从“在线源可补拉”推进到“本地可审计、可重试、可验收”的正式能力。

## 第一批范围

1. 建立只读完整性审计：统计 `sc.legacy.file.index` 是否能解析到本地文件。
2. 区分索引缺口、文件缺口、零字节文件、正式 `ir.attachment` URL 缺口。
3. 保持默认只报告不失败；需要收口时通过严格模式把缺文件转为门禁失败。
4. 后续基于审计结果补下载重试、进度快照和生产验收记录。
5. 建立后台镜像任务验收：读取 job result JSON，并抽查在线源索引是否能解析到本地镜像文件。

## 非目标

- 不直接改写锁定历史业务事实。
- 不把在线 fallback 当作最终完整性证明。
- 不在没有证据的情况下批量创建正式业务附件关系。

## 当前验收入口

```bash
DB_NAME=sc_demo make verify.legacy_attachment.mirror.completeness.audit
```

默认扫描 5000 条索引，适合日常开发快速判断。全量扫描：

```bash
LEGACY_ATTACHMENT_COMPLETENESS_LIMIT=0 \
DB_NAME=sc_demo make verify.legacy_attachment.mirror.completeness.audit
```

也可以通过 Make 专用参数传入：

```bash
make verify.legacy_attachment.mirror.completeness.audit \
  DB_NAME=sc_demo \
  ATTACHMENT_AUDIT_SOURCE_CONTAINS=online_old \
  ATTACHMENT_AUDIT_LIMIT=5000
```

严格模式：

```bash
LEGACY_ATTACHMENT_COMPLETENESS_STRICT=1 \
LEGACY_ATTACHMENT_COMPLETENESS_ALLOW_MISSING_FILES=0 \
DB_NAME=sc_demo make verify.legacy_attachment.mirror.completeness.audit
```

## 后台任务验收入口

后台任务验收入口会递归读取 `ATTACHMENT_JOB_AUDIT_JOB_ROOT` 下的 JSON 结果文件，并以 `counts`、`model`、`mirror_root` 等字段识别 `legacy_online_attachment_mirror.py` 产物；不要求结果文件必须使用固定文件名。

日常抽样：

```bash
make verify.legacy_online_attachment.mirror.job.audit \
  DB_NAME=sc_demo \
  ATTACHMENT_JOB_AUDIT_SOURCE_CONTAINS=online_old \
  ATTACHMENT_JOB_AUDIT_INDEX_LIMIT=5000
```

生产验收使用专用只读 `.prod` 目标，必须显式设置 `PROD_READONLY_VERIFY=1`。该目标默认：

- 严格模式：`LEGACY_ATTACHMENT_JOB_AUDIT_STRICT=1`
- 全量索引：`LEGACY_ATTACHMENT_JOB_AUDIT_INDEX_LIMIT=0`
- job 失败零容忍：`LEGACY_ATTACHMENT_JOB_AUDIT_ALLOW_JOB_FAILURES=0`
- 缺本地文件零容忍：`LEGACY_ATTACHMENT_JOB_AUDIT_ALLOW_MISSING_FILES=0`

执行示例：

```bash
PROD_READONLY_VERIFY=1 \
make verify.legacy_online_attachment.mirror.job.audit.prod \
  ENV=prod \
  DB_NAME=sc_demo \
  ATTACHMENT_JOB_AUDIT_JOB_ROOT=/data/odoo/legacy_attachments/online_mirror/_jobs/prod_online_attachment_mirror_YYYYMMDDTHHMMSS+0800 \
  ATTACHMENT_JOB_AUDIT_SOURCE_CONTAINS=online_old
```

生产完整性复核也使用只读 `.prod` 目标：

```bash
PROD_READONLY_VERIFY=1 \
make verify.legacy_attachment.mirror.completeness.audit.prod \
  ENV=prod \
  DB_NAME=sc_demo \
  ATTACHMENT_AUDIT_SOURCE_CONTAINS=online_old
```

完整性 `.prod` 目标会同时检查：

- `sc.legacy.file.index` 索引记录是否能解析到本地非零字节文件。
- 正式 `ir.attachment` 中仍指向 legacy URL 的附件是否已有本地文件承接。

输出：

- `/mnt/artifacts/backend/legacy_online_attachment_mirror_job_audit.json`
- `/mnt/artifacts/backend/legacy_online_attachment_mirror_job_audit.md`

两个审计入口默认只在终端打印摘要，完整样例和明细写入 JSON/Markdown artifact。需要调试完整终端输出时，可追加：

```bash
LEGACY_ATTACHMENT_COMPLETENESS_PRINT_FULL=1
LEGACY_ATTACHMENT_JOB_AUDIT_PRINT_FULL=1
```

或使用 Make 参数：

```bash
ATTACHMENT_AUDIT_PRINT_FULL=1
ATTACHMENT_JOB_AUDIT_PRINT_FULL=1
```

后台任务结果的关键收口计数来自生产镜像脚本真实输出：

- `files_local_ok`: 已下载且本地非零字节文件存在。
- `files_download_failed`: 下载异常。
- `files_local_missing`: 下载后仍未形成有效本地文件。
- `online_fetch_failed`: 在线源文件列表获取失败。

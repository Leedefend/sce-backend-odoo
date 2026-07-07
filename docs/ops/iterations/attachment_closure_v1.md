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
- job 结果目录：`LEGACY_ATTACHMENT_JOB_ROOT=/mnt/artifacts/backend/legacy-online-mirror-jobs`
- job 失败零容忍：`LEGACY_ATTACHMENT_JOB_AUDIT_ALLOW_JOB_FAILURES=0`
- 缺本地文件零容忍：`LEGACY_ATTACHMENT_JOB_AUDIT_ALLOW_MISSING_FILES=0`

执行示例：

```bash
PROD_READONLY_VERIFY=1 \
make verify.legacy_online_attachment.custody.evidence.prod \
  ENV=prod \
  DB_NAME=sc_demo \
  ATTACHMENT_JOB_AUDIT_SOURCE_CONTAINS=online_old

PROD_READONLY_VERIFY=1 \
make verify.legacy_online_attachment.mirror.job.audit.prod \
  ENV=prod \
  DB_NAME=sc_demo \
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

## 残差摘要口径

严格完整性审计失败时，先保留完整缺失 TSV，再生成去重残差摘要：

```bash
make verify.legacy_attachment.missing_residual.summarize \
  ATTACHMENT_MISSING_RESIDUAL_INPUT=/data/odoo/legacy_attachments/checks/prod_legacy_attachment_missing_YYYYMMDDTHHMMSS+0800.tsv \
  ATTACHMENT_MISSING_RESIDUAL_OUTPUT=/data/odoo/legacy_attachments/checks/prod_legacy_attachment_missing_unique_summary.json
```

残差汇报必须区分：

- `reference_rows`：索引引用行数，可能包含同一文件被多条业务记录引用。
- `unique_missing_paths`：唯一缺失路径数量，用于实际补文件工作量。
- `nonzero_unique_paths`：旧索引声明有大小的缺失文件，应优先追补。
- `zero_size_unique_paths`：旧索引大小为 0 的缺失记录，应单独判定为旧源元数据残差，不得与真实非零文件混为一类。

## 自定义前端浏览器验收

后端 custody 只说明文件可被服务端定位；生产可用性还必须验证自定义前端能打开或下载。
生产验收必须分两步执行：

1. 先在生产服务器生成浏览器样本清单，清单中的每个样本都必须已经解析到生产本地文件，并记录本地文件大小与 sha256。
2. 再用自定义前端浏览器会话下载或预览附件，并把浏览器实际拿到的字节 sha256 与生产本地文件 sha256 做强一致比较。

样本清单入口：

```bash
ENV=prod \
ENV_FILE=.env.prod \
DB_NAME=sc_prod \
PROD_READONLY_VERIFY=1 \
make verify.legacy_attachment.frontend_browser.sample_manifest.prod \
  LEGACY_ATTACHMENT_BROWSER_SAMPLE_MANIFEST_OUTPUT=/mnt/artifacts/backend/legacy_attachment_frontend_browser_samples_all_models.json
```

浏览器验收入口：

```bash
FRONTEND_URL=http://127.0.0.1:5179 \
DB_NAME=sc_prod \
E2E_LOGIN=<login> \
E2E_PASSWORD=<password> \
LEGACY_ATTACHMENT_BROWSER_SAMPLES_FILE=<local-sample-manifest.json> \
node scripts/verify/legacy_attachment_frontend_browser_acceptance.js
```

或使用 Make 入口：

```bash
DB_NAME=sc_prod \
E2E_LOGIN=<login> \
E2E_PASSWORD=<password> \
make verify.legacy_attachment.frontend_browser.acceptance.host \
  LEGACY_ATTACHMENT_BROWSER_FRONTEND_URL=http://127.0.0.1:5179 \
  LEGACY_ATTACHMENT_BROWSER_SAMPLES_FILE=<local-sample-manifest.json>
```

该验收使用浏览器登录自定义前端，通过前端 session 调用 `file.download`，并在浏览器内验证：

- 图片附件可生成 blob 预览且图片尺寸有效。
- PDF 附件可生成预览 blob，文件头为 `%PDF-`。
- Office 文档类附件可触发浏览器下载，下载文件大小与返回内容一致。
- 若样本包含 `expected_local_sha256` 和 `expected_local_size`，浏览器实际返回内容必须与生产本地文件完全一致，并输出 `production_local_file_verified=true`。

2026-07-07 生产全模型验收结论：

```text
sample_manifest_prod PASS
required_model_count=10
covered_model_count=10
sample_count=10
missing_models=[]

frontend_browser_acceptance admin PASS
covered_models=10/10
production_local_file_verified=10/10

frontend_browser_acceptance business_user PASS
covered_models=9/10
production_local_file_verified=9/9
excluded_model=sc.project.member.staging
excluded_reason=business user has no read permission on model sc.project.member.staging
```

全模型范围：

```text
construction.contract
construction.contract.line
payment.request
payment.request.line
project.project
sc.legacy.direct.acceptance.fact
sc.legacy.fund.confirmation.document
sc.legacy.payment.residual.fact
sc.project.member.staging
sc.receipt.invoice.line
```

硬性判定：

- 对生产 `legacy-file://` 迁移附件，已按模型全覆盖抽样验证自定义前端能打开或下载。
- 浏览器实际拿到的字节与生产服务器 `/mnt/legacy-files` 本地文件 sha256 完全一致，因此该结论证明的是生产服务器自己的附件系统生效，不是旧在线文件系统兜底。
- `sc.project.member.staging` 对普通业务用户不可读，属于模型权限边界；管理员口径已覆盖该模型附件链路。
- 全量旧附件索引中剩余 121 条本地文件缺失引用仍是独立残差；这些缺失路径不能被本次浏览器验收视为已可打开。
- `type=url` 且仍为外部 `http` URL 的附件不属于 `legacy-file://` 本地 custody 证明范围，需要按在线 URL 残差单独分类。

## 自定义前端上传闭环验收

历史附件可读不等于业务办理附件闭环。业务办理场景还必须证明新附件能从自定义前端上传到生产附件系统，并能从同一业务记录读回。

验收入口：

```bash
FRONTEND_URL=http://127.0.0.1:5179 \
DB_NAME=sc_prod \
E2E_LOGIN=<business-login> \
E2E_PASSWORD=<password> \
MVP_MODEL=project.project \
RECORD_ID=<writable-record-id> \
ACTION_ID=<form-action-id> \
MENU_ID=<menu-id> \
node scripts/verify/attachment_upload_frontend_browser_acceptance.js
```

或使用 Make 入口：

```bash
DB_NAME=sc_prod \
E2E_LOGIN=<business-login> \
E2E_PASSWORD=<password> \
MVP_MODEL=project.project \
RECORD_ID=<writable-record-id> \
ACTION_ID=<form-action-id> \
MENU_ID=<menu-id> \
make verify.attachment_upload.frontend_browser.acceptance.host \
  LEGACY_ATTACHMENT_BROWSER_FRONTEND_URL=http://127.0.0.1:5179
```

该验收必须覆盖：

- 真实业务用户登录自定义前端。
- 打开真实业务表单的附件上传控件。
- 通过浏览器文件选择上传一个受控小文件。
- 从 `file.upload` 响应取得 `ir.attachment` id。
- 通过 `file.download` intent 读回，sha256 与上传文件一致。
- 通过前端附件列表打开 `AttachmentViewer`，再点击弹窗下载，浏览器下载文件 sha256 与上传文件一致。
- 生产后端复核上传附件为 `type=binary`，`store_fname` 有值，`db_datas` 为空，证明新附件走 Odoo filestore 而不是旧在线源兜底。
- 验收结束必须删除测试附件，并确认 `remaining_ids=[]`。

2026-07-07 生产上传闭环结论：

```text
frontend_upload_acceptance PASS
business_user=wutao
model=project.project
record_id=71
action_id=506
menu_id=790
attachment_id=21806
fixture_sha256=6d8ca743f8b5113126c9f7e2b31443ad4d054f33404a118d2bb4283d37d7cd57
intent_download_sha256=6d8ca743f8b5113126c9f7e2b31443ad4d054f33404a118d2bb4283d37d7cd57
ui_download_sha256=6d8ca743f8b5113126c9f7e2b31443ad4d054f33404a118d2bb4283d37d7cd57
console_errors=0
backend_type=binary
backend_store_fname=d2/d299238ab19f37f1efd324545d9299dfc33eab6b
backend_db_datas_present=false
cleanup_ok=true
readonly_recheck_remaining_count=0
```

上传闭环硬性判定：

- 业务办理附件上传链路已在生产真实业务表单上通过。
- 新上传附件进入生产 Odoo `ir.attachment` 标准二进制/filestore 体系，不依赖旧在线文件系统。
- 上传后 intent 读回和 UI 下载读回的字节 sha256 均与原始上传文件一致。
- 验收附件已提交清理，并经只读复核确认不在生产业务记录上残留测试附件。

## 用户可达办理面上传矩阵

单个业务表单通过仍不足以证明“所有办理面”无遗漏。生产验收必须先生成上传办理面清单，再对用户可达办理面执行矩阵验收。

生产只读清单入口：

```bash
ENV=prod \
ENV_FILE=.env.prod \
DB_NAME=sc_prod \
PROD_READONLY_VERIFY=1 \
E2E_LOGIN=<business-login> \
make verify.attachment_upload.surface_manifest.prod \
  ATTACHMENT_UPLOAD_SURFACE_MANIFEST_OUTPUT=/mnt/artifacts/backend/attachment_upload_surface_manifest.json
```

浏览器矩阵入口：

```bash
FRONTEND_URL=http://127.0.0.1:5179 \
DB_NAME=sc_prod \
E2E_LOGIN=<business-login> \
E2E_PASSWORD=<password> \
ATTACHMENT_UPLOAD_BROWSER_SAMPLES_FILE=<selected-samples.json> \
node scripts/verify/attachment_upload_frontend_browser_matrix_acceptance.js
```

2026-07-07 生产矩阵结果：

```text
surface_manifest PASS
allowed_model_count=267
browser_upload_candidate_count=87
user_visible_handling_surface_sample_count=23

frontend_upload_matrix result=PARTIAL_PASS
passed=17/23 in first matrix run
settlement_order_rerun=PASS
effective_passed=18/23
failed_or_blocked=5/23
cleanup_ok=true
readonly_recheck_remaining_count=0
```

已完整通过的用户可达办理面：

```text
project.project
construction.contract
project.tags
sc.dashboard.cockpit.fact
sc.document.admin.document
sc.financing.loan
sc.fund.account.operation
sc.hr.payroll.document
sc.invoice.registration
sc.legacy.fund.daily.line
sc.legacy.invoice.tax.fact
sc.office.admin.document
sc.settlement.adjustment
sc.settlement.order
sc.tax.deduction.registration
sc.treasury.reconciliation
tender.bid
tender.doc.purchase
```

未闭合办理面分类：

```text
BUSINESS_STATE_WRITE_POLICY_BLOCKED:
  sc.expense.claim
  sc.general.contract
  sc.payment.execution
  sc.receipt.income

NO_UPLOAD_CONTROL_ON_PAGE:
  sc.legacy.payment.residual.fact
```

矩阵判定：

- 18 个用户可达办理面已证明上传、intent 读回、前端弹窗下载三者 sha256 一致。
- 4 个历史已确认单据被业务写策略阻断，错误信息均为“只允许补充...”类限制；这不是 filestore/附件读写主链路失败，但说明这些办理面是否允许补附件需要产品规则明确。
- `sc.legacy.payment.residual.fact` 页面没有实际上传控件，属于表单契约/页面暴露边界缺口；如果该菜单被定义为可办理附件面，需要补契约或从上传办理面清单中排除。
- 本轮产生的验收附件已全部提交清理，并经只读复核确认无 `production upload acceptance %` 残留。

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

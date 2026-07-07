# Production Deployment Record

## 1. 基本信息

| 项目 | 值 |
| --- | --- |
| 部署编号 | `main_full_alignment_20260707` |
| 部署窗口 | `2026-07-07 17:12-18:23 Asia/Shanghai` |
| 操作人 | `Codex assisted` |
| 审批人 | `user approved` |
| 生产主机 | `sc-prod` |
| 生产目录 | `/opt/sce/production/sce-backend-odoo` |
| 生产数据库 | `sc_prod` |
| 发布类型 | `full tree` |
| 发布包 | `git main full tree @ 2cfe88590323687afaae47b5500036140862d115` |
| 发布包 sha256 | `ae319ca6565ffd38b1555b4f5c41cd7e25c7512f0360ac591c5c969ef4034015` |
| 目标 commit/tag | `2cfe88590323687afaae47b5500036140862d115` |

## 2. 发布范围声明

本次发布范围：

- [x] 生产代码目录改造为标准 Git 工作区。
- [x] 生产代码全量对齐 `origin/main@2cfe88590323687afaae47b5500036140862d115`。
- [x] 子模块 `addons_external/oca_server_ux@2b908a8e68ddde906ea45be7b5fb24676f29f8cc` 对齐。
- [x] 生产 `.env.prod` 作为环境配置例外保留，并设置 `skip-worktree`。
- [x] 已安装 `smart_*` 模块完成生产升级。

变更文件清单：

```text
full tracked Git tree from main@2cfe88590323687afaae47b5500036140862d115
exclude runtime data: database, filestore, Docker volumes, /data/odoo legacy attachment mirrors
environment exception: .env.prod preserved from production and marked skip-worktree
```

模块清单：

```text
smart_core
smart_construction_bootstrap
smart_construction_bundle
smart_construction_core
smart_construction_custom
smart_construction_portal
smart_construction_scene
smart_construction_seed
smart_license_core
smart_owner_bundle
smart_owner_core
smart_scene
```

Migration 清单：

```text
No standalone migration script was run. Module upgrade loaded module XML/data/migrations through Odoo registry update.
```

## 3. 发布前状态

生产服务状态：

```text
sc-backend-odoo-prod-odoo-1    healthy
sc-backend-odoo-prod-db-1      healthy
sc-backend-odoo-prod-redis-1   healthy
HTTP / => 303 SEE OTHER -> /web
```

生产模块版本：

```text
installed smart_* modules listed in section 2 were present before upgrade.
smart_construction_demo|uninstalled|
smart_construction_demo XMLID count=0
```

日常开发与生产差异登记：

| 差异类型 | 结果 | 说明 |
| --- | --- | --- |
| 发布包文件差异 | `0` | 生产 Git 工作区已对齐目标主线提交 |
| 模块版本差异 | `PASS` | 已安装 `smart_*` 模块已执行 `mod.upgrade` |
| 全量代码树差异 | `0` | `git status --short` clean，`HEAD=origin/main=2cfe88590323687afaae47b5500036140862d115` |
| 数据差异 | `PASS` | 非 demo 污染、业务 readiness、附件 custody 探针通过 |

## 4. 备份

生产写入前已记录完整回滚点。

| 类型 | 路径 | 校验 | 结果 |
| --- | --- | --- | --- |
| 数据库 | `/data/backups/prod_main_alignment_20260707T1712_main_align/sc_prod_20260707T1712_main_align.dump` | `sha256=ae319ca6565ffd38b1555b4f5c41cd7e25c7512f0360ac591c5c969ef4034015` | `PASS` |
| filestore | `/data/backups/prod_main_alignment_20260707T1712_main_align/sc_prod_filestore_20260707T1712_main_align.tar.gz` | `sha256=b3deb9e63d5296ef3d7fe220711ac8af6373d2e4f71654ab0929d25ab22dd349` | `PASS` |
| 代码文件 | `/data/backups/prod_main_alignment_20260707T1712_main_align/sce-backend-odoo_code_20260707T1712_main_align.tar.gz` | `sha256=3dba687f6e36f39d483d0b4219b95abcb4de4ef10b0b5433fd77ac05ae3a8e60` | `PASS` |
| 切换前目录 | `/opt/sce/production/sce-backend-odoo.pre_main_align_20260707T1712` | `directory retained` | `PASS` |

备份验证命令：

```bash
sha256sum /data/backups/prod_main_alignment_20260707T1712_main_align/*
test -d /opt/sce/production/sce-backend-odoo.pre_main_align_20260707T1712
```

## 5. Prod-Sim 验证

本次发布的核心目标是将生产服务器本身从非 Git 增量树改造为主线 Git 工作区。执行前已完成本地、日常开发服务器和生产增量发布验证；本次生产窗口以完整数据库、filestore 和代码备份作为回滚点执行全量代码树切换。

| 检查项 | 结果 | 证据 |
| --- | --- | --- |
| 生产备份 | `PASS` | `/data/backups/prod_main_alignment_20260707T1712_main_align` |
| 候选主线工作区构建 | `PASS` | `main@2cfe88590323687afaae47b5500036140862d115` |
| 模块升级 | `PASS` | production `make mod.upgrade` |
| 业务烟测 | `PASS` | production `smoke.business_full` |
| 角色矩阵 | `PASS` | production `smoke.role_matrix` |
| 非 demo 污染 | `PASS` | production `verify.non_demo_data_contamination` |

prod-sim 运行 ID：

```text
production-main-full-alignment-20260707
```

## 6. 生产执行摘要

发布包校验：

```text
target commit=2cfe88590323687afaae47b5500036140862d115
origin/main=2cfe88590323687afaae47b5500036140862d115
submodule addons_external/oca_server_ux=2b908a8e68ddde906ea45be7b5fb24676f29f8cc
full_tree_git_clean_except_env_prod=1
```

文件同步和备份：

```bash
pg_dump -U odoo -Fc sc_prod > /data/backups/prod_main_alignment_20260707T1712_main_align/sc_prod_20260707T1712_main_align.dump
tar -C /data/docker/volumes/sc_prod_odoo_data/_data/filestore -czf ... sc_prod
tar -C /opt/sce/production -czf ... sce-backend-odoo
mv sce-backend-odoo sce-backend-odoo.pre_main_align_20260707T1712
mv sce-backend-odoo.git-main-2cfe88590 sce-backend-odoo
git switch -C main 2cfe88590323687afaae47b5500036140862d115
git update-index --skip-worktree .env.prod
```

模块升级：

```bash
ENV=prod ENV_FILE=.env.prod DB_NAME=sc_prod PROD_DANGER=1 \
  CODEX_NEED_UPGRADE=1 \
  MODULE="smart_core,smart_construction_bootstrap,smart_construction_bundle,smart_construction_core,smart_construction_custom,smart_construction_portal,smart_construction_scene,smart_construction_seed,smart_license_core,smart_owner_bundle,smart_owner_core,smart_scene" \
  make mod.upgrade
```

服务健康：

```text
sc-backend-odoo-prod-odoo-1    running healthy
sc-backend-odoo-prod-db-1      running healthy
sc-backend-odoo-prod-redis-1   running healthy
HTTP / => 303 SEE OTHER -> /web
```

## 7. 发布后验证

最低验证矩阵：

| 检查项 | 结果 | 摘要 |
| --- | --- | --- |
| `verify.baseline` | `PASS` | `PASS ALL on sc_prod` |
| `verify.p0` | `PASS` | 登录环境 `prod`，P0 通过 |
| `smoke.business_full` | `PASS` | 材料计划、合同、结算、付款申请全链路通过 |
| `smoke.role_matrix` | `PASS` | 角色读写边界与审批路径通过 |
| `verify.non_demo_data_contamination` | `PASS` | `PASS db=sc_prod mode=default` |
| `history.attachment.custody.probe.prod` | `PASS` | `history_attachment_custody_ready`，gap_count=0，legacy_url_attachments=19541 |
| 服务健康 | `PASS` | `running healthy`，HTTP `/` 返回 `303 SEE OTHER` |

补充验证：

```text
verify.business_system.usability_readiness.prod PASS
decision=ready_for_business_system_use
history_business_usable_ready gap_count=0
formal_business_backfill_ready gap_count=0
lowcode_config_boundary_guard PASS
business_config_guard_inventory PASS
backend_contract_boundary_guard PASS
production_release_flow_guard PASS
production_deployment_record_guard PASS
```

Demo 状态：

```text
smart_construction_demo XMLID count=0
smart_construction_demo|uninstalled|
```

## 8. 回滚点

| 回滚对象 | 路径/版本 | 操作说明 |
| --- | --- | --- |
| 数据库 | `/data/backups/prod_main_alignment_20260707T1712_main_align/sc_prod_20260707T1712_main_align.dump` | 按生产恢复 runbook 恢复 |
| filestore | `/data/backups/prod_main_alignment_20260707T1712_main_align/sc_prod_filestore_20260707T1712_main_align.tar.gz` | 按生产恢复 runbook 恢复 |
| 原生产代码目录 | `/opt/sce/production/sce-backend-odoo.pre_main_align_20260707T1712` | 停止 Odoo 后切回目录并执行 `prod.restart.safe` |
| 代码归档 | `/data/backups/prod_main_alignment_20260707T1712_main_align/sce-backend-odoo_code_20260707T1712_main_align.tar.gz` | 解压恢复后执行 `prod.restart.safe` |

## 9. 收口结论

- [x] 本次发布包范围已与生产对齐。
- [x] 生产模块版本已达到目标版本。
- [x] 生产服务健康检查通过。
- [x] 生产验证矩阵全部通过。
- [x] demo 模块和 demo XMLID 状态符合生产要求。
- [x] 生产与日常开发服务器全量一致。

最终发布结论：

```text
本次生产全量主线对齐已完成。生产服务器代码目录已从非 Git 增量树改造为标准 Git 工作区，main 分支对齐 origin/main@2cfe88590323687afaae47b5500036140862d115；生产 .env.prod 作为环境配置例外保留。生产服务健康，完整验证矩阵通过，具备生产运行条件。
```

## 10. 后续事项

| 事项 | 负责人 | 截止时间 | 状态 |
| --- | --- | --- | --- |
| 后续生产发布以 `git fetch && git checkout "$APPROVED_MAIN_COMMIT"` 或 release tag 为标准入口 | `TBD` | `TBD` | `open` |
| 清理旧生产目录 `/opt/sce/production/sce-backend-odoo.pre_main_align_20260707T1712` 前至少保留一个发布观察周期 | `TBD` | `TBD` | `open` |
| `.env.prod` 后续从仓库跟踪文件迁出或改为模板化配置，避免配置例外长期存在 | `TBD` | `TBD` | `open` |

## 11. 附件 Custody Evidence 补充部署

2026-07-07 19:15 +0800，生产从 `origin/main` 快进到
`46d434177d9c96e335777723fd79f6da435a34e5`，部署范围仅包含附件在线源 custody
evidence 生成器、附件 job audit 默认证据目录、生产发布流程文档和守卫更新；不涉及 Odoo
模块代码升级，不需要 `mod.upgrade`。

生产对齐状态：

```text
HEAD=origin/main=46d434177d9c96e335777723fd79f6da435a34e5
git status --short: clean
production_git_authority_guard: PASS
production_release_flow_guard: PASS
```

新增标准链路：

```bash
ENV=prod ENV_FILE=.env.prod DB_NAME=sc_prod PROD_READONLY_VERIFY=1 make verify.legacy_online_attachment.custody.evidence.prod
ENV=prod ENV_FILE=.env.prod DB_NAME=sc_prod PROD_READONLY_VERIFY=1 make verify.legacy_online_attachment.mirror.job.audit.prod
```

在线源附件验收结果：

```text
verify.legacy_online_attachment.custody.evidence.prod PASS
file_index_rows=69352
files_local_ok=69352
files_local_missing=0
zero_size_local_file=0
output=/mnt/artifacts/backend/legacy-online-mirror-jobs/custody_evidence_20260707T111524Z/sc_legacy_file_index_online_custody_evidence.json

verify.legacy_online_attachment.mirror.job.audit.prod PASS
strict=true
mirror_result_files=1
job_failure_count=0
missing_files=0
json_output=/mnt/artifacts/backend/legacy_online_attachment_mirror_job_audit.json
```

全量旧附件索引残差仍单独成立，不能与在线源附件闭环混同：

```text
file_index_rows=243713
local_file_ok=243592
missing_local_file=121
missing_by_source:
  BASE_SYSTEM_FILE=114
  T_BILL_FILE=7
```

残差去重摘要：

```text
reference_rows=121
unique_missing_paths=120
duplicate_reference_rows=1
nonzero_unique_paths=16
zero_size_unique_paths=104
nonzero_unique_bytes=2947165
summary=/data/odoo/legacy_attachments/checks/prod_legacy_attachment_missing_unique_summary.json
```

补充结论：

```text
生产在线源附件（online_old_scbs / online_old_scbsly）已经完成本地 custody evidence 和严格 job audit 闭环。
生产全量旧附件索引仍有 121 条本地文件缺失引用，对应 120 个唯一缺失路径；其中 16 个为非零文件、104 个为旧索引大小为 0 的记录，应继续作为旧源残差专项处理。
```

## 12. 自定义前端附件浏览器验收

2026-07-07 19:26-19:29 +0800，使用本地自定义前端验收实例
`http://127.0.0.1:5179`，通过 SSH 转发连接生产后端 `sc_prod`，以浏览器登录后的前端
session 验证生产已有迁移附件可打开或下载。生产后端和生产附件数据真实，验收过程不写生产数据。

样本：

```text
image: ir.attachment/971  2.jpg
pdf:   ir.attachment/977  施工合同.pdf
docx:  ir.attachment/999  董礼兵身份证.docx
```

结果：

```text
legacy_attachment_frontend_browser_acceptance PASS
id mode:
  image decoded_bytes=108978 natural_width=1080 natural_height=1440
  pdf decoded_bytes=313781 header=%PDF-
  docx decoded_bytes=98071 browser_download=PASS zip_header=true
url mode:
  image decoded_bytes=108978 natural_width=1080 natural_height=1440
  pdf decoded_bytes=313781 header=%PDF-
  docx decoded_bytes=98071 browser_download=PASS zip_header=true
```

真实业务页面入口补充验证：

```text
frontend route=/a/625?menu_id=343&db=sc_prod
model=sc.receipt.invoice.line
menu=收款发票
attachment_count_link_rendered=true
attachment_viewer_opened=true
viewer_file=施工合同.docx
browser_download_suggested_filename=施工合同.docx
browser_download_saved_bytes=3343474
browser_download_zip_header=true
console_errors=0
```

证据目录：

```text
artifacts/legacy-attachment-frontend-browser/20260707T112642
artifacts/legacy-attachment-frontend-browser/20260707T112658
artifacts/legacy-attachment-frontend-browser/ui-entry-20260707T1127
artifacts/legacy-attachment-frontend-browser/ui-download-20260707T1129
```

## 13. 全模型附件浏览器强验收

2026-07-07 19:51-19:53 +0800，扩大到生产 `ir.attachment` 中所有
`type=url` 且 `url like legacy-file://%` 的业务模型。先在生产服务器生成样本清单，
再通过本地自定义前端浏览器实例连接生产后端下载或预览，最后比较浏览器实际返回字节与
生产本地文件 sha256。

生产样本清单：

```text
command=ENV=prod ENV_FILE=.env.prod DB_NAME=sc_prod PROD_READONLY_VERIFY=1 make verify.legacy_attachment.frontend_browser.sample_manifest.prod
output=/mnt/artifacts/backend/legacy_attachment_frontend_browser_samples_all_models.json
status=PASS
required_model_count=10
covered_model_count=10
sample_count=10
missing_models=[]
expected_source=production_local_legacy_file_root
```

模型分布：

| 模型 | 生产 legacy-file 附件数 | 浏览器验收 |
| --- | ---: | --- |
| `construction.contract` | 1 | `PASS` |
| `construction.contract.line` | 1 | `PASS` |
| `payment.request` | 5443 | `PASS` |
| `payment.request.line` | 4689 | `PASS` |
| `project.project` | 464 | `PASS` |
| `sc.legacy.direct.acceptance.fact` | 2 | `PASS` |
| `sc.legacy.fund.confirmation.document` | 1 | `PASS` |
| `sc.legacy.payment.residual.fact` | 1 | `PASS` |
| `sc.project.member.staging` | 7860 | `PASS` with admin, permission-denied for business user |
| `sc.receipt.invoice.line` | 1079 | `PASS` |

管理员全模型浏览器验收：

```text
artifact=artifacts/legacy-attachment-frontend-browser/20260707T115308/summary.json
legacy_attachment_frontend_browser_acceptance PASS
sample_count=10
covered_models=10/10
production_local_file_verified=10/10
request_mode=url
```

普通业务用户权限口径验收：

```text
artifact=artifacts/legacy-attachment-frontend-browser/20260707T115334/summary.json
legacy_attachment_frontend_browser_acceptance PASS
sample_count=9
covered_models=9/10
production_local_file_verified=9/9
excluded_model=sc.project.member.staging
excluded_reason=model read permission denied for business user
```

中间失败记录用于证明权限边界：

```text
artifact=artifacts/legacy-attachment-frontend-browser/20260707T115159/summary.json
result=expected_fail
reason=PERMISSION_DENIED on sc.project.member.staging
passed_before_failure=8
production_local_file_verified_before_failure=8/8
```

样本本地文件 sha256 证明：

| 模型 | 附件 | 生产本地文件 | sha256 |
| --- | --- | --- | --- |
| `construction.contract` | `dzfp_23512000000096427896_四川保盛建设集团有限公司_20230927150933(1).pdf` | `/mnt/legacy-files/UserFile/2023/09/27/0f1dd02adcb3411491054bbc1cf1d0c2_135003.pdf` | `229cb2d5cf7a1e7dcc24bcfae8e0a67ed16dbf4d5e59038538cd199b14c4067c` |
| `construction.contract.line` | `dzfp_23512000000096427896_四川保盛建设集团有限公司_20230927150933(1).pdf` | `/mnt/legacy-files/UserFile/2023/09/27/0f1dd02adcb3411491054bbc1cf1d0c2_135003.pdf` | `229cb2d5cf7a1e7dcc24bcfae8e0a67ed16dbf4d5e59038538cd199b14c4067c` |
| `payment.request` | `学院零星机械租赁合同模板.doc` | `/mnt/legacy-files/OldSystem/File_New/OutContract/2020/5/26/d8ccebd639f226b87d01bf64e83f2382.doc` | `ac8be0f0026bca64e473402c4a76f2e07548dc823500aad7cf60c016b4497a51` |
| `payment.request.line` | `学院零星机械租赁合同模板.doc` | `/mnt/legacy-files/OldSystem/File_New/OutContract/2020/5/26/d8ccebd639f226b87d01bf64e83f2382.doc` | `ac8be0f0026bca64e473402c4a76f2e07548dc823500aad7cf60c016b4497a51` |
| `project.project` | `邦泰.翡翠城预埋管道工程.doc` | `/mnt/legacy-files/OldSystem/File_New/OutContract/2020/12/25/67f9025bf605b7077353cfee5ab39d06.doc` | `d9c1c84c64d8b5a0d10a13475974a57f37649c35ee751c66514683563376dfc5` |
| `sc.legacy.direct.acceptance.fact` | `98eccfb212ee4241be2e0fcb5719b4f7.jpg` | `/mnt/legacy-files/OldSystem/File_New/SignalPic/98eccfb212ee4241be2e0fcb5719b4f7.jpg` | `a1d5b705e00cd0f79779a2dc2c31975b6babf622bc117d64cae8af024a09248f` |
| `sc.legacy.fund.confirmation.document` | `image.png` | `/mnt/legacy-files/UserFile/2026/02/06/83e3919481c644a89c582524a7d3761e_45554.png` | `ff509c5d2c809f50dd69f9b11c18130f97132af8a16b687870a0bdfd1ff02559` |
| `sc.legacy.payment.residual.fact` | `2026（769号）.pdf` | `/mnt/legacy-files/UserFile/2026/03/19/cb5f5b05a95d4a118f2bd1f5406be539_174096.pdf` | `9fcc5d0d0dcafefba717a5397685ec20ffe2e954c80f81787ed787b0f4ff155e` |
| `sc.project.member.staging` | `邦泰.翡翠城预埋管道工程.doc` | `/mnt/legacy-files/OldSystem/File_New/OutContract/2020/12/25/67f9025bf605b7077353cfee5ab39d06.doc` | `d9c1c84c64d8b5a0d10a13475974a57f37649c35ee751c66514683563376dfc5` |
| `sc.receipt.invoice.line` | `张文浩（建筑）.doc` | `/mnt/legacy-files/OldSystem/File_New/Credentials/2019/7/24/a0a52e623399ec232cab20fde6f6c860.doc` | `d4273129fd02c6f5f52ac4ab69618a3fdf839d8adccfbec3e325f50c01e3a6a8` |

强验收结论：

```text
生产 legacy-file:// 迁移附件已完成全模型浏览器可用性抽样验收。
10/10 模型均存在生产本地文件样本，浏览器实际返回内容与 /mnt/legacy-files 下生产本地文件 sha256 完全一致。
因此，本结论证明生产服务器自己的附件系统已经生效，不依赖旧在线文件系统兜底。
普通业务用户无法读取 sc.project.member.staging 是预期模型权限边界，不是附件系统失败。
全量旧附件索引剩余 121 条本地文件缺失引用仍按残差专项处理，不能并入本次已验证范围。
```

## 14. 业务办理附件上传闭环验收

2026-07-07 20:03 +0800，补充验证生产真实业务办理中的新附件上传能力。验收通过本地自定义前端
实例 `http://127.0.0.1:5179` 连接生产后端 `sc_prod`，使用普通业务用户打开
`project.project/71` 的项目台账表单，执行浏览器文件选择上传、前端回显、intent 读回和弹窗下载。

验收命令：

```bash
FRONTEND_URL=http://127.0.0.1:5179 \
DB_NAME=sc_prod \
E2E_LOGIN=wutao \
MVP_MODEL=project.project \
RECORD_ID=71 \
ACTION_ID=506 \
MENU_ID=790 \
node scripts/verify/attachment_upload_frontend_browser_acceptance.js
```

浏览器验收结果：

```text
artifact=artifacts/attachment-upload-frontend-browser/20260707T120322/summary.json
attachment_upload_frontend_browser_acceptance PASS
attachment_id=21806
fixture_sha256=6d8ca743f8b5113126c9f7e2b31443ad4d054f33404a118d2bb4283d37d7cd57
intent_download_sha256=6d8ca743f8b5113126c9f7e2b31443ad4d054f33404a118d2bb4283d37d7cd57
ui_download_sha256=6d8ca743f8b5113126c9f7e2b31443ad4d054f33404a118d2bb4283d37d7cd57
console_errors=0
```

生产后端 filestore 复核：

```text
attachment_id=21806
name=production upload acceptance 1783425802983.txt
res_model=project.project
res_id=71
type=binary
mimetype=text/plain
file_size=103
checksum=d299238ab19f37f1efd324545d9299dfc33eab6b
store_fname=d2/d299238ab19f37f1efd324545d9299dfc33eab6b
db_datas_present=false
```

清理结果：

```text
deleted_attachment_ids=[21805,21806]
remaining_ids=[]
cleanup_ok=true
readonly_recheck_remaining_count=0
```

上传闭环结论：

```text
业务办理附件上传链路已在生产真实业务表单通过。
新附件写入生产 Odoo ir.attachment 标准二进制/filestore 体系，store_fname 有值且 db_datas 为空。
上传文件、file.download intent 读回、AttachmentViewer 弹窗下载三者 sha256 完全一致。
验收附件已提交清理，并经只读复核确认生产业务记录未残留测试附件。
```

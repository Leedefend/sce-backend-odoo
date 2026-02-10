# Docs Restructure Plan v0.1（中文）

## 0. 范围与约束
- 范围：`docs/`、`artifacts/contract`、`artifacts/docs` 以及全仓 markdown 索引。
- 对齐基线：仅基于现有能力（scene / intent / contract / guard / verify），不发明新能力。
- 执行约束：验证与导出优先使用现有 Makefile 目标（本轮已执行：`contract.catalog.export`、`contract.evidence.export`、`audit.intent.surface`）。
- 本文性质：前置盘点 + 结构重构方案，不做大规模迁移改动。

## 1. 文档盘点摘要
数据来源：`artifacts/docs/docs_audit_20260210_090905.json`

### 1.1 总览
- Markdown 文件总数：1202
- 判定为“过时/临时”条目：67
- 标题重复条目：705（大量来自模板、归档和三方目录，需分层处理）
- 缺关键链接条目：4

### 1.2 关键问题（docs 主目录相关）
1. `docs/ops/releases/` 下存在较多 `TEMP_*` 文件，和正式 release 证据混放。
2. `docs/ops/releases/archive/temp/` 与当前 release 文档边界不清晰，检索噪声高。
3. `docs/contract/*` 核心文档与 `docs/contract/README.md` 的互链不完整（`reason_codes.md`、`suggested_action_contract.md` 等）。
4. 版本化前端历史说明（如 `frontend_v0_3_notes.md` ~ `v0_7`）与当前阶段文档共层级，维护成本高。

### 1.3 疑似过时/临时文件（节选）
- `docs/ops/releases/archive/temp/temp/TEMP_phase_10_batch_contract_pr_body.md`
- `docs/ops/releases/archive/temp/temp/TEMP_phase_10_pr_a_body.md`
- `docs/ops/releases/archive/temp/temp/TEMP_phase_9_8_progress.md`
- `docs/ops/releases/archive/temp/TEMP_repo_audit_summary.md`
- `docs/ops/releases/archive/temp/frontend_history/frontend_v0_3_notes.md`
- `docs/ops/releases/archive/frontend_history/frontend_v0_7_ui_notes.md`

## 2. 能力矩阵 -> 文档位置映射

| 能力域 | 当前权威位置 | 现状判断 | 风险 |
|---|---|---|---|
| Contract | `docs/contract/README.md` `docs/contract/contract_v1.md` `docs/contract/exports/intent_catalog.json` `docs/contract/exports/scene_catalog.json` | 基本完整 | 文档互链不足 |
| Reason Codes | `docs/contract/reason_codes.md` + `addons/smart_core/utils/reason_codes.py` | 语义已收口 | README 回链缺失 |
| Suggested Action Contract | `docs/contract/suggested_action_contract.md` + `frontend/apps/web/src/app/suggested_action/*` | 规则与守卫齐全 | 与总 contract 导航耦合弱 |
| Release / Ops | `docs/ops/releases/*` | 证据丰富 | TEMP 与正式混放 |
| Gate / Verify | `Makefile` 的 `verify.*` / `gate.*` + `scripts/verify/*` | 执行链完整 | 文档化入口分散 |
| Scene / Intent Catalogs | `docs/contract/exports/*.json` `artifacts/docs/intent_surface_report.json` | 可机读 | 缺统一索引页 |

## 3. 目标目录结构提案（v0.1）

```text
docs/
  README.md                      # 文档总入口（新增）
  contract/
    README.md                    # 合约总览（保留，增强导航）
    contract_v1.md
    reason_codes.md
    suggested_action_contract.md
    exports/
      intent_catalog.json
      scene_catalog.json
  ops/
    README.md                    # 运维/流程入口（新增）
    releases/
      current/                   # 当前阶段可追溯文档（新增）
      archive/                   # 历史归档（保留）
      templates/                 # 模板统一命名（由 _templates 迁移）
  audit/
    README.md                    # 审计说明（新增）
    latest/                      # 最新审计可见产物（新增索引，不存大型中间件）
```

## 4. 目录责任边界
- `docs/contract/`：平台对外契约承诺（接口 shape、reason code、前后端契约说明）。
- `docs/ops/releases/current/`：当前阶段发布证据与执行结论（可直接给 reviewer）。
- `docs/ops/releases/archive/temp/`：历史阶段材料，默认不参与日常阅读路径。
- `docs/audit/`：审计方法、规则、latest 索引；机器产物仍保留在 `artifacts/`。
- `artifacts/docs/`：机器生成清单与一次性盘点结果，不承诺长期可读格式。

## 5. 合并/迁移/废弃建议清单

### 5.1 迁移（建议）
1. `docs/ops/releases/current/phase_11_backend_closure.md` -> `docs/ops/releases/current/phase_11_backend_closure.md`
2. `docs/ops/releases/current/phase_11_1_contract_visibility.md` -> `docs/ops/releases/current/phase_11_1_contract_visibility.md`
3. `docs/ops/releases/current/phase_10_my_work_v1_evidence.md` -> `docs/ops/releases/current/phase_10_my_work_v1_evidence.md`
4. `docs/ops/releases/_templates/*` -> `docs/ops/releases/templates/*`

### 5.2 废弃/归档（建议）
1. `docs/ops/releases/TEMP_*.md`：统一迁移至 `archive/temp/` 或删除（保留必要引用）。
2. `docs/ops/releases/archive/temp/frontend_history/frontend_v0_3_notes.md` ~ `frontend_v0_7*.md`：迁移到 `archive/frontend_history/`。
3. `docs/audit/node_missing_notes.md`：若已被后续机制替代，归档。

### 5.3 链接修复（建议）
1. `docs/contract/reason_codes.md` 增加回链到 `docs/contract/README.md`。
2. `docs/contract/suggested_action_contract.md` 增加回链到 `docs/contract/README.md`。
3. `docs/contract/contract_v1.md` 与 `baseline_rules.md` 增加统一“返回总览”链接。

## 6. 建议新增 Makefile 文档验证目标（仅计划）
> 本轮不落地，仅列入下一 PR。

1. `verify.docs.inventory`
- 作用：输出 markdown 清单和分类统计到 `artifacts/docs/`。

2. `verify.docs.links`
- 作用：检查 docs 内部相对链接有效性、关键 hub 回链完整性。

3. `verify.docs.toc`
- 作用：检查关键文档标题层级与目录一致性（contract/ops/audit）。

4. `verify.docs.temp_guard`
- 作用：阻止新增 `TEMP_*.md` 直接进入 `docs/ops/releases/current/`。

5. `verify.docs.contract_sync`
- 作用：校验 `docs/contract/*.md` 与 `docs/contract/exports/*.json` 的版本锚点一致。

## 7. 分阶段执行建议

### Phase A（低风险，1 PR）
- 新增 `docs/README.md`、`docs/ops/README.md`、`docs/audit/README.md`。
- 修复 `docs/contract/*` 与 README 互链。

### Phase B（中风险，1 PR）
- `releases` 分层（`current/`、`archive/`、`templates/`）+ 批量迁移。
- 更新所有引用路径。

### Phase C（门禁化，1 PR）
- 新增 docs 校验脚本与 Makefile 目标。
- 将 `verify.docs.links + verify.docs.temp_guard` 纳入 `verify.contract.preflight` 或专用 `verify.docs.all`。

## 8. 本轮交付物
- `docs/audit/plans/docs_restructure_plan.zh.md`
- `docs/audit/plans/docs_restructure_plan.en.md`
- `artifacts/docs/docs_audit_20260210_090905.json`


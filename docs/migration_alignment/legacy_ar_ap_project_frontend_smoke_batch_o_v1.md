# 应收应付报表（项目）专用前端契约 Smoke Batch-O

## 1. 批次定位

- Layer Target：Frontend Contract Gate
- Module：`scripts/verify`、`Makefile`
- Reason：通用 `tree_view_smoke` 使用跨模型 grouped signature baseline，应用到 `sc.ar.ap.project.summary` 会因业务分组数据不同误报。需要为应收应付报表（项目）固化专用前端契约 smoke，直接验证本报表的列、字段标签、权限和关键数据行。

## 2. 新增门禁

新增脚本：

```bash
scripts/verify/fe_ar_ap_project_summary_smoke.js
```

新增 Make target：

```bash
make verify.portal.ar_ap_project_summary_smoke.container
```

验证内容：

- 真实用户登录，默认 `wutao/123456`
- `load_view(model=sc.ar.ap.project.summary, view_type=tree)` 成功
- 必要列存在：
  - `project_id`
  - `partner_name`
  - `payable_pricing_method_text`
  - `tax_deduction_rate`
  - `actual_available_balance`
- 关键字段中文标签正确：
  - 往来单位
  - 计价方式
  - 抵扣比例
  - 实际可用余额
- 权限为只读报表：`read=true, write=false, create=false, unlink=false`
- `api.data` 可读取 `56` 条项目级余额行
- `api.data` 可读取 `7471` 条非零项目级抵扣比例行

## 3. 验证结果

运行命令：

```bash
ENV=test ENV_FILE=.env.prod.sim DB_NAME=sc_prod_sim \
  E2E_LOGIN=wutao E2E_PASSWORD=123456 \
  make verify.portal.ar_ap_project_summary_smoke.container
```

结果：PASS

同时验证：

- `node --check scripts/verify/fe_ar_ap_project_summary_smoke.js`：PASS
- `corepack pnpm -C frontend/apps/web typecheck:strict`：PASS
- `git diff --check`：PASS
- `make verify.restricted`：SKIP，当前仓库无该 target

## 4. 产物

脚本运行产物写入：

```text
/mnt/artifacts/codex/ar-ap-project-summary/<timestamp>/
```

包含：

- `login.log`
- `load_view.log`
- `project_balance_rows.log`
- `tax_rate_rows.log`
- `summary.md`

## 5. 后续建议

下一轮可以继续补用户可读性提示：在原生视图或前端显示层明确 `实际可用余额` 和 `抵扣比例` 是项目级指标，避免用户在导出或透视中按行求和。

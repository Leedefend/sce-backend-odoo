# P0 Alignment Verification

## 验证目标

- baseline guard 与 readiness audit 不再冲突
- 首发链路前端不再通过关键词推断业务动作
- 首发产品范围形成单一口径

## 验证命令

- `make verify.platform_kernel_baseline_guard`
- `make verify.product.final_slice_readiness_audit`
- `make verify.architecture.orchestration_platform_guard`
- `make verify.architecture.five_layer_workspace_audit`

## 首发链路手动验证

- 登录
- 进入项目创建
- 最小字段创建
- 自动进入驾驶舱
- 检查 block 是否正常展示
- 检查是否出现 `fallback` / `unknown` / 空 block

## 验收标准

- baseline guard PASS
- final slice readiness PASS
- architecture guards PASS
- 首发链路无 fallback/unknown/空 block

## 结果记录

- `make verify.platform_kernel_baseline_guard` -> `PASS`
- `make verify.product.final_slice_readiness_audit` -> `READY_FOR_SLICE`
- `make verify.architecture.orchestration_platform_guard` -> `PASS`
- `make verify.architecture.five_layer_workspace_audit` -> `PASS`
- `make verify.frontend.typecheck.strict` -> `PASS`
- `make verify.product.project_flow.initiation_dashboard ENV=test ENV_FILE=.env.prod.sim COMPOSE_PROJECT_NAME=sc-backend-odoo-prod-sim PROJECT=sc-backend-odoo-prod-sim DB_NAME=sc_prod_sim E2E_LOGIN=svc_e2e_smoke E2E_PASSWORD=demo` -> `PASS`
- `make verify.portal.login_browser_smoke.prod_sim ENV=test ENV_FILE=.env.prod.sim COMPOSE_PROJECT_NAME=sc-backend-odoo-prod-sim PROJECT=sc-backend-odoo-prod-sim DB_NAME=sc_prod_sim E2E_LOGIN=svc_e2e_smoke E2E_PASSWORD=demo` -> `PASS`
  - 证据：[summary.json](/mnt/wsl/docker-desktop-bind-mounts/Ubuntu/0bf88c91312832ece483d20f9dd0da58b3449c7beac0658c5397b284fcec1f13/artifacts/codex/login-browser-smoke/20260323T033851Z/summary.json)
  - `fresh_login` -> `/a/504?menu_id=278&scene_key=project.initiation...`
  - `auth_401_redirect` -> `/login?redirect=%2Fa%2F504...`
  - `relogin_after_401` -> `/f/project.project/new?menu_id=278&scene_key=project.initiation`

## 补充说明

- 本轮完成了 P0 联合验证中的自动化部分
- 首发链路“项目创建 -> 驾驶舱”已补到浏览器级 smoke 证据
- 仍未做人工录像式逐步验收，但已不再是“只有后端 smoke、没有浏览器证据”

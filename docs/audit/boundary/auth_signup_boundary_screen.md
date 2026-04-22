# auth_signup Boundary Screen (ITER-2026-04-05-1033)

## Scope

- stage: `screen`
- target file: `addons/smart_construction_core/controllers/auth_signup.py`
- objective: classify ownership and boundary risk for auth signup family only.

## Route Facts

| route | handler | file | auth/type | current responsibility | mainline impact | classification |
| --- | --- | --- | --- | --- | --- | --- |
| `/web/signup` | `web_auth_signup` | `addons/smart_construction_core/controllers/auth_signup.py` | `public/http` | signup entry, captcha gate, password policy, default groups, activation mail dispatch | non-frontend-api mainline (website/auth side path) | auth onboarding endpoint |
| `/sc/auth/activate/<string:token>` | `sc_activate_account` | `addons/smart_construction_core/controllers/auth_signup.py` | `public/http` | activation token consume, account enable, redirect to login | non-frontend-api mainline (email callback path) | auth activation endpoint |

## Object-Level Record

### Object 1
- 对象类型：Controller + Route
- 文件路径：`addons/smart_construction_core/controllers/auth_signup.py`
- 类/函数/route/intention 名：`ScAuthSignup.web_auth_signup` / `/web/signup`
- 当前职责：注册表单处理、限流、口令校验、邮箱域白名单、激活流程触发
- 当前调用上游：浏览器登录页入口（`addons/smart_construction_core/views/web_login_views.xml`）
- 当前调用下游：`res.users.signup`、`sc.signup.throttle`、`mail.mail`、`res.partner.signup_prepare`
- 涉及数据对象：`res.users`、`res.partner`、`sc.signup.throttle`
- 是否对外暴露：是（public website）
- 是否主链：否（不在 `/api/*` 前端主运行链）
- 是否跨行业复用：中（通用 auth onboarding 语义）
- 是否依赖 smart_core 内部：否
- 是否依赖 smart_construction_scene 内部：否
- 是否涉及 platform/menu/app/scene/ops/pack/telemetry：否（auth lifecycle）
- 当前建议归属层：专用 auth 场景线（独立于 runtime API 迁移线）
- 风险等级：P1
- 备注证据：`addons/smart_construction_core/controllers/auth_signup.py` 中含完整注册策略与账号激活前置

### Object 2
- 对象类型：Controller + Route
- 文件路径：`addons/smart_construction_core/controllers/auth_signup.py`
- 类/函数/route/intention 名：`ScAuthSignup.sc_activate_account` / `/sc/auth/activate/<string:token>`
- 当前职责：激活 token 校验、用户启用、token 清理、登录页回跳
- 当前调用上游：激活邮件链接（同文件 `_send_activation_email`）
- 当前调用下游：`res.partner._signup_retrieve_partner`、`res.users.write`
- 涉及数据对象：`res.partner`、`res.users`
- 是否对外暴露：是（public URL）
- 是否主链：否（激活回调侧链）
- 是否跨行业复用：中（通用账号激活语义）
- 是否依赖 smart_core 内部：否
- 是否依赖 smart_construction_scene 内部：否
- 是否涉及 platform/menu/app/scene/ops/pack/telemetry：否
- 当前建议归属层：专用 auth 场景线（独立治理）
- 风险等级：P2
- 备注证据：同文件 `@http.route("/sc/auth/activate/<string:token>")`

## Boundary Decision (Screen Only)

1. `auth_signup` family is **not** part of the migrated platform runtime API chain (`/api/*`).
2. No scene/capability/ops/pack coupling is observed in `auth_signup.py`.
3. Boundary risk exists as **domain placement issue**, not runtime API ownership conflict:
   - signup/activation policy is currently hosted in industry module;
   - semantics are reusable auth lifecycle, suitable for isolated auth-governance line.

## Risk & Priority

- overall level: `P1`
- rationale:
  - external public exposure + identity lifecycle semantics;
  - but not P0 runtime mainline and no platform scene coupling.

## Next Suggestion

- open dedicated follow-up chain: `auth_signup ownership screen -> migration design -> bounded implement`.
- keep current file stable in this batch (no code move in screen stage).

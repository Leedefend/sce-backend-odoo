# Release Checklist — <VERSION>

## 前置条件
- 工作区干净
- Tag 本地与远端均存在
- Release Notes 已审阅

## Guard 验证（必须）
- `ENV=prod make verify.prod.guard` 通过（guard-only）
- `scripts/verify/prod_guard_smoke.sh` 产出 JSON 结果
- 仅当 JSON 报告 `rc=0` 时允许发布

## 生产安全检查
- `ENV=prod` 禁止：`make db.reset`, `make demo.*`, `make ci.*`, `make gate.*`
- `ENV=prod` 必须 `PROD_DANGER=1`：`mod.install`, `mod.upgrade`, policy apply
- 生产 seed 需显式 DB：`SEED_DB_NAME_EXPLICIT=1`

## Seed Base（如需执行）
- 仅允许 `SC_SEED_PROFILE=base`
- `SC_BOOTSTRAP_USERS=1` 必须同时提供 `SEED_ALLOW_USERS_BOOTSTRAP=1` 与密码

## 发布后
- 记录 guard JSON 到发布日志
- 确认 `main` 与 tag 一致

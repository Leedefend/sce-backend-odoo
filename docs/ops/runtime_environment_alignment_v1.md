# Runtime Environment Alignment v1

## Goal

一次性对齐日常开发、测试专用、模拟生产验收三套运行环境，避免 `sc_demo` / `sc_test` 混用。

## Runtime Matrix

- `daily (dev)`
  - backend: `http://localhost:8069`
  - database: `sc_demo`
  - frontend: `http://127.0.0.1:5174`
  - startup: `make fe.dev.daily`

- `test`
  - backend: `http://localhost:8071`
  - database: `sc_test`
  - frontend: `http://127.0.0.1:5174`
  - startup: `make fe.dev.test`

- `uat (prod-sim)`
  - backend: `http://localhost:18069`
  - database: `sc_prod_sim`
  - frontend: `http://127.0.0.1:5174`
  - startup: `make fe.dev.uat`

## One-Time Alignment

- 对齐并重启 daily/test：
  - `make ops.runtime.align`
- 仅检查当前对齐状态：
  - `make ops.runtime.align.check`

## Frontend HMR Baseline

- 统一入口：`scripts/dev/frontend_dev_reset.sh`
- 支持 profile：`daily` / `test` / `uat`
- 自动行为：
  - 根据 profile 注入 `VITE_API_PROXY_TARGET` 和 `VITE_ODOO_DB`
  - 优先 tmux 启动；不可用时回退到 nohup
  - 自动 readiness 检查 `http://127.0.0.1:5174/`

## Recommended Daily Workflow

1. `make ops.runtime.align.check`
2. `make fe.dev.daily`
3. 打开 `http://127.0.0.1:5174/?db=sc_demo`

测试联调改为：

1. `make fe.dev.test`
2. 打开 `http://127.0.0.1:5174/?db=sc_test`

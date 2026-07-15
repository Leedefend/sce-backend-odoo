# 旧系统在线采集配置契约 v1

## 边界

在线采集属于 P4 运维交付工具。默认模式为 `offline`；预检只解析配置，不解析 DNS、不建立网络连接、不访问数据库、不创建采集成功 manifest。

所有 secret 只能由运行时环境或既有 secret manager 注入。文档、Make、Compose、CI 和脚本不得提供用户名、密码或 token 默认值。SCBSLY 不得回退使用 SCBS 凭据。

## 全局配置

| 变量 | 必需条件 | 语义 |
| --- | --- | --- |
| `SCBS_CAPTURE_MODE` | 始终 | `offline`（默认）或 `online` |
| `SCBS_ONLINE_CAPTURE_CONFIRM` | online | 必须精确为受控确认值；不是 secret |
| `SCBS_CAPTURE_DESTINATION_ALLOWLIST` | online | 逗号分隔的允许 origin；必须包含目标 Base URL origin |
| `SCBS_CAPTURE_DRY_RUN` | 可选 | 仅表达采集调用方 dry-run 意图，不放宽其他门禁 |

## SCBS

| 变量 | online 必需 | 语义 |
| --- | ---: | --- |
| `OLD_SCBS_BASE_URL` | 是 | 来源 Base URL；不得带 URL 内嵌凭据、query 或 fragment |
| `OLD_SCBS_USERNAME` | 是 | 由 secret 环境注入的用户名 |
| `OLD_SCBS_PASSWORD` | 是 | 由 secret 环境注入的密码 |
| `OLD_SCBS_REQUEST_TIMEOUT_SECONDS` | 否 | 请求超时，范围 1–600 秒，默认 90 |
| `OLD_SCBS_REQUEST_RETRY_LIMIT` | 否 | 重试上限，范围 0–10，默认 3 |
| `OLD_SCBS_CAPTURE_WINDOW` | 是 | 允许采集的业务时间窗口标识 |
| `SCBS_CAPTURE_RAW_OUTPUT_DIR` | 是 | 不可变原始资产输出目录 |
| `SCBS_CAPTURE_MANIFEST_OUTPUT_DIR` | 是 | manifest/checksum 输出目录 |
| `SCBS_CAPTURE_AUDIT_LOG_PATH` | 是 | 脱敏网络请求审计日志位置 |

## SCBSLY

| 变量 | online 必需 | 语义 |
| --- | ---: | --- |
| `SCBSLY_BASE_URL` | 是 | 来源 Base URL；不得带 URL 内嵌凭据、query 或 fragment |
| `SCBSLY_USERNAME` | 是 | SCBSLY 专用用户名，不回退到 SCBS |
| `SCBSLY_PASSWORD` | 是 | SCBSLY 专用密码，不回退到 SCBS |
| `SCBSLY_REQUEST_TIMEOUT_SECONDS` | 否 | 请求超时，范围 1–600 秒，默认 90 |
| `SCBSLY_REQUEST_RETRY_LIMIT` | 否 | 重试上限，范围 0–10，默认 3 |
| `SCBSLY_CAPTURE_WINDOW` | 是 | 允许采集的业务时间窗口标识 |
| `SCBSLY_CAPTURE_RAW_OUTPUT_DIR` | 是 | 不可变原始资产输出目录 |
| `SCBSLY_CAPTURE_MANIFEST_OUTPUT_DIR` | 是 | manifest/checksum 输出目录 |
| `SCBSLY_CAPTURE_AUDIT_LOG_PATH` | 是 | 脱敏网络请求审计日志位置 |

## 预检

离线默认检查：

```bash
make online.capture.preflight
```

online readiness 检查必须由运行环境注入上述变量，并显式设置 `ONLINE_CAPTURE_REQUIRE_ONLINE=1`。预检输出只包含变量缺失原因、布尔状态和非敏感路径，不输出变量值。

任一必需配置缺失、包含占位符、确认值错误、目标不在 allowlist 或 URL 含凭据时，命令在任何网络请求前以退出码 `78` 失败。

## 日志与产物

- 禁止记录 password、Authorization、Cookie、token、请求 body 和带凭据 URL。
- preflight 失败不得生成采集成功 manifest、截图或 Playwright trace。
- replay 与数据库访问不属于 preflight；在线采集不得隐式触发 replay。
- 当前数据状态仍为 `DATA_BASELINE_NOT_FROZEN` 和 `ONLINE_CONTINUITY_NOT_ESTABLISHED`。

English: [online_capture_configuration_contract_v1.en.md](online_capture_configuration_contract_v1.en.md)

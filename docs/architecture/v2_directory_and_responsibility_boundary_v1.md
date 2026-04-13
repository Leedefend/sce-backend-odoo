# v2 目录与职责边界规范 v1

## 目录建议

```text
addons/smart_core/v2/
  controllers/
  intents/
    registry.py
    registry_entries/
    schemas/
  handlers/
  services/
  orchestrators/
  parsers/
  builders/
  policies/
  contracts/
    schemas/
    snapshots/
  scripts/verify/
  tests/
```

## 职责边界

### controller
- 只做协议适配与上下文提取
- 禁止业务查询/契约拼装

### registry
- 只做 intent 注册与查询
- 禁止执行逻辑

### dispatcher
- 只做分发、校验、权限前置、异常壳
- 禁止业务编排

### handler
- 只做用例级编排入口
- 禁止深度 ORM 查询与 contract 直拼

### service
- 只做领域事实处理
- 禁止前端 contract 字段命名

### orchestrator
- 只做跨 service 编排
- 禁止视图解析细节

### parser
- 只做结构解释
- 禁止业务决策与权限裁剪

### builder
- 只做对外 contract 输出
- 禁止 ORM 访问

### policy
- 统一权限/能力/可见性策略
- 禁止散落到 handler/service/parser

### verify
- 只做门禁与回归审计
- 必须可自动运行

## 禁止反模式

- controller 直接查业务并返回 JSON
- handler 同时写业务+解析+契约
- parser 直接做业务规则
- builder 直接查数据库
- service 直接返回前端专用 dict

## 执行要求

- 新增功能必须声明落点层级。
- 每批次必须明确“不做项”。
- 合同变更必须同步 snapshot 与 verify。

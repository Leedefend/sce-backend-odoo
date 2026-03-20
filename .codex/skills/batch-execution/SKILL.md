---
name: batch-execution
description: 按 Batch-A/B/C 节奏执行开发与验证，保证单批次收口、可验证、可回滚。
metadata:
  short-description: 批次执行（强约束版）
---

# Batch Execution (Project Standard)

## Use When
- 执行 P0/P1/P2 或 Batch-A/B/C 迭代
- 控制范围、防止跨批次扩散
- 组织“一主一辅”并行执行
- 需要明确批次验收与回滚策略

## Batch Definition（必须声明）
每个批次必须包含：

- 当前批次：Batch-X
- 目标：唯一核心目标（仅一条）
- 范围：允许修改的模块/文件
- 不做：明确禁止修改内容

## Execution Workflow（强制流程）

### 1️⃣ 批次初始化
- 校验输入是否包含：目标 / 范围 / 不做
- 若缺失 → 停止执行

---

### 2️⃣ 边界锁定
- 仅允许修改“范围”内内容
- 出现范围外需求 → 标记扩散并中止

---

### 3️⃣ 语义前置检查（必须通过）
以下任一未明确 → 禁止编码：

- role 真源
- compat 策略
- default_route（如涉及）
- contract version 规则

---

### 4️⃣ 实现顺序（强制）
必须按顺序执行：

1. 契约/schema（后端）
2. handler/service 修改
3. 前端消费（如涉及）
4. 验证与测试

禁止跳序。

---

### 5️⃣ 并行约束（严格）
仅允许：

- 主线：实现
- 辅线：验证 / 文档

禁止：

- 双主线实现
- 多模块核心改造并行

---

### 6️⃣ 验证执行（必须独立完成）
必须包含：

- verify（restricted）
- contract snapshot
- guard 检查（role / version / contract）
- 前端 smoke（如涉及）

未完成验证 → 禁止进入下一批次

---

### 7️⃣ 收口与输出
必须完成：

- 风险识别
- 回滚路径确认
- 文档同步

## Hard Rules（必须执行）

- 一次只允许一个主批次目标
- 禁止跨批次扩散
- 未完成验证禁止进入下一批次
- 禁止边开发边改目标
- 契约优先于实现
- 前端不得推导后端语义
- 启动链必须保持：
  login → system.init → ui.contract

## Forbidden Actions（禁止）

- 同时重构 `login + system.init`
- 同时修改 `contract + UI`
- 在语义未确定时编码
- 在未验证时合并代码
- 修改未声明范围内容

## Required Output（强制输出格式）

### 执行结果

- 代码改动清单：
- 修改文件路径：

---

### 验证结果

- verify：
- snapshot：
- guard：

---

### 产物路径

- logs：
- snapshots：
- docs：

---

### 风险与回滚

- 风险：
- 回滚方式：

---

### 文档更新

- 更新内容：
- 更新位置：

## Batch Start Template
```text
当前批次：Batch-X

目标：
（仅一个核心目标）

范围：
（允许修改的模块/文件）

不做：
（明确禁止内容）
```

## Batch Stop Conditions（必须停止）

出现以下情况必须停止执行：

- 发现范围外修改需求
- 核心语义未定义
- 验证失败
- 契约结构不稳定

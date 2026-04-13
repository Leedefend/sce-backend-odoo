# v2 最小主链实施顺序 v1

## 目标

用最小路径构建可运行主链，避免局部优化打断整体重建。

## 最小主链顺序

1. registry
2. dispatcher
3. handler
4. service / orchestrator
5. parser
6. builder
7. governance gate

## 每层最小交付

### registry
- 可注册/可列出/可检测重复

### dispatcher
- 统一分发与错误壳

### handler
- 至少一组 system + app + meta 代表意图可运行

### service / orchestrator
- 结果对象化，层级边界清晰

### parser
- 有统一 ParseResult 骨架

### builder
- Envelope + Contract Builder 生效

### governance gate
- common output contract
- expected checks snapshot
- failure-path 守卫

## 本阶段不做

- 不做旧模块深度修补
- 不做跨模块大重构
- 不做未声明入口扩展

## 阶段推进规则

- 当前层未闭环，不进入下一层。
- 层内先实现最小闭环，再做优化。
- 每轮必须有可验证产物（脚本/快照/报告）。

# @sc/design-tokens

跨端统一设计令牌（Design Tokens）基础包。

## 目标
- 单一事实源：所有端共享同一套 token 输入。
- 语义优先：业务样式仅消费 semantic token。
- 跨端导出：web / mobile / mini 稳定输出。

## 目录
- `tokens/base.json`: 原子值（颜色、间距、圆角、字体等）
- `tokens/semantic.light.json`: 亮色语义 token
- `tokens/semantic.dark.json`: 暗色语义 token
- `tokens/component.json`: 组件级 token
- `platform/*.json`: 平台差异覆盖
- `scripts/build_tokens.py`: 生成 CSS variables 与 TS 常量

## 用法
```bash
python3 frontend/packages/design-tokens/scripts/build_tokens.py
```

## 输出
- `dist/web/tokens.css`（默认 light）
- `dist/web/tokens.light.css`
- `dist/web/tokens.dark.css`
- `dist/shared/tokens.ts`（含 `light/dark/mobile_light/mini_light` 变体）

## 质量要求
- 默认严格模式：引用未解析将失败。
- 单测：`python3 -m unittest frontend/packages/design-tokens/tests_build_tokens.py`

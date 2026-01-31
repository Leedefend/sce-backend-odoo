# Continue DeepSeek 配置指南

本文档记录了 Continue 工具与 DeepSeek 模型集成的配置方法和故障排除指南。

## 配置路径差异

### Windows 插件配置路径
```
C:\Users\<用户名>\.continue\config.yaml
```

### WSL CLI 配置路径
```
~/.continue/config.yaml
```

## 配置示例

```yaml
name: local-deepseek
version: 1.0.0
schema: v1
models:
  - name: DeepSeek Chat
    provider: openai
    model: deepseek-chat
    apiKey: sk-***  # 注意：必须是驼峰命名的 apiKey
    apiBase: https://api.deepseek.com/v1
  - name: DeepSeek Coder
    provider: openai
    model: deepseek-coder
    apiKey: sk-***  # 注意：必须是驼峰命名的 apiKey
    apiBase: https://api.deepseek.com/v1
roles:
  chat: DeepSeek Chat
  edit: DeepSeek Chat
  apply: DeepSeek Chat
  summarize: DeepSeek Chat
  autocomplete: DeepSeek Coder
allowAnonymousTelemetry: false
experimental:
  disableIndexing: true
```

## DeepSeek 可用模型

通过以下命令获取最新的可用模型列表：

```bash
curl -H "Authorization: Bearer sk-***" \
  https://api.deepseek.com/v1/models
```

当前主要模型：
- `deepseek-chat` - 通用对话模型
- `deepseek-coder` - 代码专用模型
- `deepseek-reasoner` - 推理专用模型（如可用）

## 解决"闪烁"问题（工程缺陷）

### 问题根源
1. **命令混淆**: `continue` 是 bash 内置关键字（用于循环控制），真正的 Continue CLI 是 `cn`
2. **交互模式**: 默认的交互式 TUI 在 VS Code/TTY 下会频繁重绘和请求确认
3. **渲染机制**: Continue 的终端集成导致"闪烁"现象

### 正确使用方式
```bash
# ❌ 错误：使用 bash 内置命令
continue --help  # 显示的是 bash 循环控制帮助

# ✅ 正确：使用 Continue CLI
cn --help        # 显示 Continue CLI 帮助
```

### 解决方案：使用 Makefile 统一入口

项目已集成 Continue CLI，推荐使用 Makefile targets：

#### 1. 无闪烁批处理模式（默认推荐）
```bash
# 使用项目配置，避免闪烁
make cn.p PROMPT="任务描述"

# 示例：文档化分析
make cn.p PROMPT="分析 smart_construction_core 的文档缺失情况"
```

#### 2. 管道输入模式
```bash
# 从文件读取任务
cat task.txt | make cn.p.stdin

# 复杂任务分解
echo "步骤1: 分析问题" | make cn.p.stdin
echo "步骤2: 提供方案" | make cn.p.stdin
```

#### 3. 交互式模式（仅需人工确认时使用）
```bash
# 保留 TUI，可能闪烁
make cn.tui
```

#### 4. 快速测试
```bash
# 验证集成是否正常
make cn.test
```

### 技术实现
- **脚本**: `scripts/ops/cn_print.sh` - 强制 `--print` 模式
- **配置**: 优先使用项目配置 `tools/continue/config/continue-deepseek.json`
- **超时**: 默认 180 秒，可设置 `CN_TIMEOUT` 环境变量调整

### 为什么选择批处理模式
1. **稳定性**: 无界面重绘，输出稳定
2. **自动化**: 适合 CI/CD 和脚本集成
3. **可复现**: 相同的输入产生相同的输出
4. **成本控制**: 避免会话态管理开销

## 一键自检命令（无闪烁版）

### 使用 Makefile 自检
```bash
# 测试 Continue 集成
make cn.test

# 完整自检流程
make cn.p PROMPT="DeepSeek CLI 自检：请回复当前模型名称和配置状态"
```

### 手动自检命令
```bash
# 验证命令可用性
which cn && cn --version

# 检查配置路径
ls -la ~/.continue/config.yaml ~/.continue/config.json 2>/dev/null

# 检查项目配置
ls -la tools/continue/config/

# 检查日志中的模型请求
tail -20 ~/.continue/logs/cn.log 2>/dev/null | grep -i "model\|deepseek\|apiBase" || echo "日志未找到"

# 验证 API 连通性（注意打码）
curl -s -H "Authorization: Bearer sk-***" \
  https://api.deepseek.com/v1/models 2>/dev/null | jq -r '.data[].id' | grep deepseek || echo "API 测试跳过"
```

### 故障排查
```bash
# 1. 检查进程
ps aux | grep -i cn | grep -v grep

# 2. 检查环境变量
env | grep -i deepseek

# 3. 测试简单请求
cn --print "test" 2>&1 | head -5
```

## 常见错误对照表

### 1. "Chat disabled until a model is available"
**原因**: config.yaml 的 schema 或字段格式不正确
**解决方案**:
- 检查 YAML 格式是否正确
- 确认 `schema: v1` 存在
- 确认 `models` 数组格式正确

### 2. "401 key invalid" 但 curl 测试返回 200
**原因**:
- Continue 没有正确读取本地 config 文件
- API Key 字段名错误（必须是 `apiKey` 而不是 `apikey`）
- Provider 路由错误（应该是 `provider: openai`）

**解决方案**:
```bash
# 检查字段名
grep -i "apikey\|apiKey" ~/.continue/config.yaml

# 检查 provider
grep -i "provider" ~/.continue/config.yaml
```

### 3. 请求跑到 Cloudflare/AWS GA
**原因**: Continue 仍在使用 Hub/Cloud 路由
**解决方案**:
- 确认 `apiBase` 设置为 `https://api.deepseek.com/v1`
- 检查日志中是否有 `api.deepseek.com` 域名
- 重启 Continue 服务

### 4. 模型响应慢或无响应
**原因**: 网络问题或 API 限流
**解决方案**:
```bash
# 测试网络连通性
curl -I https://api.deepseek.com/v1/models

# 检查日志中的响应时间
grep -i "response\|timeout\|error" ~/.continue/logs/cn.log | tail -10
```

## 环境变量配置

建议使用环境变量管理 API Key：

1. 创建环境变量文件：
```bash
echo "DEEPSEEK_API_KEY=sk-***" > ~/.continue/.env
```

2. 在 config.yaml 中引用：
```yaml
apiKey: ${env:DEEPSEEK_API_KEY}
```

## 日志调试

Continue 日志位置：
- `~/.continue/logs/cn.log` - 主日志文件
- `~/.continue/logs/cn1.log` - 备份日志文件

查看实时日志：
```bash
tail -f ~/.continue/logs/cn.log | grep -i "deepseek\|model\|error"
```

## 注意事项

1. **API Key 安全**: 永远不要将真实的 API Key 提交到版本控制系统
2. **配置备份**: 修改配置前备份原文件
3. **模型选择**: 根据任务类型选择合适的模型（chat/coder/reasoner）
4. **网络环境**: 确保可以访问 `api.deepseek.com` 域名
5. **版本兼容**: 检查 Continue 版本与配置 schema 的兼容性

## 参考链接

- [DeepSeek API 文档](https://platform.deepseek.com/api-docs/)
- [Continue 官方文档](https://docs.continue.dev/)
- [OpenAI 兼容 API 规范](https://platform.openai.com/docs/api-reference)
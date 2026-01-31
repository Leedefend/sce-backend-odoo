# Continue AI 助手环境变量配置指南

## 问题
当前 Continue 的 API key 以明文形式存储在配置文件中，存在安全风险。

## 解决方案
将 API key 从明文配置改为环境变量方式。

## 配置步骤

### 1. 创建环境变量文件
在项目根目录创建 `.env.continue` 文件（已添加到 `.gitignore`）：
```bash
# Continue AI 配置
OPENAI_API_KEY=your_openai_api_key_here
CONTINUE_API_KEY=your_continue_api_key_here
```

### 2. 更新 Continue 配置文件
将 Continue 配置文件更新为使用环境变量：

**Windows (PowerShell)**：
```powershell
# 设置环境变量（当前会话）
$env:OPENAI_API_KEY = "your_openai_api_key_here"

# 永久设置环境变量
[System.Environment]::SetEnvironmentVariable('OPENAI_API_KEY', 'your_openai_api_key_here', 'User')
```

**macOS/Linux (Bash)**：
```bash
# 设置环境变量
export OPENAI_API_KEY="your_openai_api_key_here"

# 永久设置（添加到 ~/.bashrc 或 ~/.zshrc）
echo 'export OPENAI_API_KEY="your_openai_api_key_here"' >> ~/.bashrc
```

### 3. Continue 配置文件示例
创建或更新 `.continue/config.json`：

```json
{
  "models": [
    {
      "title": "GPT-4",
      "provider": "openai",
      "model": "gpt-4",
      "apiKey": "${env:OPENAI_API_KEY}"
    }
  ],
  "tabAutocompleteModel": {
    "title": "GPT-4",
    "provider": "openai",
    "model": "gpt-4",
    "apiKey": "${env:OPENAI_API_KEY}"
  },
  "embeddingsProvider": {
    "provider": "openai",
    "apiKey": "${env:OPENAI_API_KEY}"
  },
  "allowAnonymousTelemetry": false,
  "experimental": {
    "disableIndexing": true
  }
}
```

### 4. 验证配置
重启 VS Code 或 Continue 扩展，验证 AI 助手是否正常工作。

## 安全建议

1. **不要提交敏感信息**：确保 `.env.continue` 文件已添加到 `.gitignore`
2. **使用不同的环境**：为开发、测试、生产环境使用不同的 API key
3. **定期轮换密钥**：定期更新 API key 增强安全性
4. **最小权限原则**：使用具有最小必要权限的 API key

## 故障排除

### 问题：环境变量未加载
**解决方案**：
1. 重启 VS Code
2. 在终端中运行 `echo $env:OPENAI_API_KEY` (Windows) 或 `echo $OPENAI_API_KEY` (macOS/Linux) 验证环境变量
3. 检查 Continue 扩展日志

### 问题：API key 无效
**解决方案**：
1. 验证 OpenAI API key 是否正确
2. 检查 API key 是否有足够的额度
3. 确认网络连接正常

## 参考链接
- [Continue 官方文档](https://docs.continue.dev)
- [OpenAI API 文档](https://platform.openai.com/docs/api-reference)
- [环境变量最佳实践](https://12factor.net/config)
```

## 下一步
1. 将实际的 API key 迁移到环境变量
2. 更新团队文档
3. 配置 CI/CD 环境变量
4. 定期审计密钥使用情况
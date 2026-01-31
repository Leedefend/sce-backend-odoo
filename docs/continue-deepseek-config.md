# Continue CLI 配置 DeepSeek 模型指南

## 当前状态
你已成功连接 Continue 服务，但当前使用的是 Claude 3.7 Sonnet 模型。

## 配置 DeepSeek 模型的完整步骤

### 1. 获取 DeepSeek API Key

1. 访问 [DeepSeek 官网](https://platform.deepseek.com)
2. 注册/登录账号
3. 进入 API Keys 页面
4. 创建新的 API Key
5. 复制 API Key

### 2. 设置环境变量

#### Windows (PowerShell):
```powershell
# 设置 DeepSeek API Key
$env:DEEPSEEK_API_KEY = "你的_deepseek_api_key"

# 永久设置（可选）
[System.Environment]::SetEnvironmentVariable('DEEPSEEK_API_KEY', '你的_deepseek_api_key', 'User')
```

#### macOS/Linux (Bash):
```bash
# 设置 DeepSeek API Key
export DEEPSEEK_API_KEY="你的_deepseek_api_key"

# 永久设置（添加到 ~/.bashrc 或 ~/.zshrc）
echo 'export DEEPSEEK_API_KEY="你的_deepseek_api_key"' >> ~/.bashrc
```

### 3. 配置 Continue

#### 方法一：使用 JSON 配置文件

1. 将配置文件复制到 Continue 配置目录：

```bash
# Windows
copy config\continue-deepseek.json "%USERPROFILE%\.continue\config.json"

# macOS/Linux
cp config/continue-deepseek.json ~/.continue/config.json
```

2. 或者手动创建 `~/.continue/config.json`：

```json
{
  "models": [
    {
      "title": "DeepSeek Coder",
      "provider": "openai",
      "model": "deepseek-coder",
      "apiKey": "${env:DEEPSEEK_API_KEY}",
      "apiBase": "https://api.deepseek.com",
      "contextLength": 16384
    },
    {
      "title": "DeepSeek Chat",
      "provider": "openai",
      "model": "deepseek-chat",
      "apiKey": "${env:DEEPSEEK_API_KEY}",
      "apiBase": "https://api.deepseek.com",
      "contextLength": 32768
    }
  ],
  "defaultModel": "DeepSeek Coder",
  "tabAutocompleteModel": {
    "title": "DeepSeek Coder",
    "provider": "openai",
    "model": "deepseek-coder",
    "apiKey": "${env:DEEPSEEK_API_KEY}",
    "apiBase": "https://api.deepseek.com"
  },
  "allowAnonymousTelemetry": false
}
```

#### 方法二：使用 TypeScript 配置文件

1. 创建 `~/.continue/config.ts`：

```typescript
import { Config } from "@continuedev/server";

export function modifyConfig(config: Config): Config {
  config.models = [
    {
      title: "DeepSeek Coder",
      provider: "openai",
      model: "deepseek-coder",
      apiKey: process.env.DEEPSEEK_API_KEY || "",
      apiBase: "https://api.deepseek.com",
      contextLength: 16384,
    },
    {
      title: "DeepSeek Chat",
      provider: "openai",
      model: "deepseek-chat",
      apiKey: process.env.DEEPSEEK_API_KEY || "",
      apiBase: "https://api.deepseek.com",
      contextLength: 32768,
    },
  ];
  
  config.defaultModel = "DeepSeek Coder";
  
  config.tabAutocompleteModel = {
    title: "DeepSeek Coder",
    provider: "openai",
    model: "deepseek-coder",
    apiKey: process.env.DEEPSEEK_API_KEY || "",
    apiBase: "https://api.deepseek.com",
  };
  
  return config;
}
```

### 4. 重启 Continue

重启 Continue CLI 或 VS Code 扩展：

```bash
# 如果使用 CLI，重启服务
continue restart

# 或者在 VS Code 中
# 1. 按 Ctrl+Shift+P
# 2. 输入 "Developer: Reload Window"
# 3. 按 Enter
```

### 5. 验证配置

1. 在 Continue CLI 中，你应该看到模型切换为 DeepSeek Coder
2. 测试模型是否正常工作：

```
# 在 Continue CLI 中输入
@ 请用 Python 写一个简单的 Hello World 程序
```

## DeepSeek 模型说明

### 可用模型

1. **DeepSeek Coder**
   - 专为代码生成优化
   - 上下文长度：16K tokens
   - 适合：编程、代码补全、调试

2. **DeepSeek Chat**
   - 通用对话模型
   - 上下文长度：32K tokens
   - 适合：文档编写、问题解答、分析

### API 端点
- 基础 URL: `https://api.deepseek.com`
- 兼容 OpenAI API 格式

## 故障排除

### 问题 1：API Key 无效
**解决方案：**
1. 验证 DeepSeek API Key 是否正确
2. 检查是否有足够的额度
3. 确认网络连接正常

### 问题 2：模型不显示
**解决方案：**
1. 检查配置文件路径：`~/.continue/config.json`
2. 验证 JSON 格式是否正确
3. 重启 Continue 服务

### 问题 3：连接超时
**解决方案：**
1. 检查网络连接
2. 确认 API 端点可访问：`https://api.deepseek.com`
3. 尝试使用代理（如果需要）

## 高级配置

### 多模型切换
在 Continue CLI 中，你可以使用命令切换模型：

```
/model DeepSeek Coder      # 切换到 DeepSeek Coder
/model DeepSeek Chat       # 切换到 DeepSeek Chat
/model GPT-4              # 切换到 GPT-4（如果配置了）
```

### 自定义提示词
在配置中添加系统提示词：

```json
{
  "models": [
    {
      "title": "DeepSeek Coder",
      "provider": "openai",
      "model": "deepseek-coder",
      "apiKey": "${env:DEEPSEEK_API_KEY}",
      "apiBase": "https://api.deepseek.com",
      "systemMessage": "你是一个专业的编程助手，擅长 Python、JavaScript、TypeScript 等语言。"
    }
  ]
}
```

## 性能优化

1. **缓存设置**：
```json
{
  "experimental": {
    "disableIndexing": true,
    "cacheProvider": "sqlite"
  }
}
```

2. **上下文长度**：根据需求调整，较短的上下文长度响应更快

3. **温度设置**：
```json
{
  "models": [
    {
      "title": "DeepSeek Coder",
      "provider": "openai",
      "model": "deepseek-coder",
      "apiKey": "${env:DEEPSEEK_API_KEY}",
      "apiBase": "https://api.deepseek.com",
      "completionOptions": {
        "temperature": 0.1,  // 较低温度，更确定性输出
        "topP": 0.95
      }
    }
  ]
}
```

## 参考链接

- [DeepSeek 官方文档](https://platform.deepseek.com/api-docs/)
- [Continue 配置文档](https://docs.continue.dev/customization/models)
- [OpenAI 兼容 API 文档](https://platform.openai.com/docs/api-reference)

---

**下一步：**
1. 获取 DeepSeek API Key
2. 设置环境变量
3. 复制配置文件到 `~/.continue/config.json`
4. 重启 Continue 服务
5. 验证 DeepSeek 模型是否正常工作

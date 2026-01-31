# DeepSeek 快速配置指南

## 当前状态
✅ 你已成功连接 Continue 服务
⚠️  当前使用模型：Claude 3.7 Sonnet
🎯 目标：切换到 DeepSeek 模型

## 快速配置步骤（3分钟完成）

### 步骤 1：获取 DeepSeek API Key
1. 访问 https://platform.deepseek.com
2. 注册/登录账号
3. 进入 API Keys 页面
4. 点击 "Create new API key"
5. 复制 API Key（以 `sk-` 开头）

### 步骤 2：运行配置脚本

#### Windows 用户：
```powershell
# 1. 打开 PowerShell
# 2. 运行配置脚本
.\scripts\setup-continue-deepseek.ps1

# 3. 按照提示输入 API Key
```

#### macOS/Linux 用户：
```bash
# 1. 给脚本执行权限
chmod +x scripts/setup-continue-deepseek.sh

# 2. 运行配置脚本
./scripts/setup-continue-deepseek.sh

# 3. 按照提示输入 API Key
```

### 步骤 3：重启 Continue

#### 在 Continue CLI 中：
1. 按 `Ctrl+C` 停止当前会话
2. 重新运行 `continue` 命令

#### 在 VS Code 中：
1. 按 `Ctrl+Shift+P`
2. 输入 `Developer: Reload Window`
3. 按 `Enter`

### 步骤 4：验证配置

在 Continue CLI 中输入以下命令验证：

```
# 查看可用模型
/model

# 切换到 DeepSeek Coder
/model DeepSeek Coder

# 测试模型
@ 用 Python 写一个简单的计算器程序
```

## 手动配置（如果脚本不工作）

### 1. 设置环境变量

**Windows (PowerShell):**
```powershell
$env:DEEPSEEK_API_KEY = "你的_api_key_here"
```

**macOS/Linux (Bash):**
```bash
export DEEPSEEK_API_KEY="你的_api_key_here"
```

### 2. 创建配置文件

创建文件：`C:\Users\你的用户名\.continue\config.json` (Windows) 或 `~/.continue/config.json` (macOS/Linux)

内容：
```json
{
  "models": [
    {
      "title": "DeepSeek Coder",
      "provider": "openai",
      "model": "deepseek-coder",
      "apiKey": "${env:DEEPSEEK_API_KEY}",
      "apiBase": "https://api.deepseek.com"
    }
  ],
  "defaultModel": "DeepSeek Coder"
}
```

### 3. 重启 Continue

## 常见问题

### Q1: 如何知道配置是否成功？
A: 在 Continue CLI 中输入 `/model`，应该能看到 "DeepSeek Coder" 在模型列表中。

### Q2: DeepSeek API Key 无效怎么办？
A: 检查：
1. API Key 是否正确复制（包含 `sk-` 前缀）
2. 是否有足够的额度
3. 网络连接是否正常

### Q3: 如何切换回其他模型？
A: 使用 `/model` 命令：
```
/model Claude 3.7 Sonnet  # 切换回 Claude
/model GPT-4              # 切换到 GPT-4
```

### Q4: 配置后 Continue 无法启动？
A: 检查配置文件 JSON 格式是否正确，可以使用 [JSONLint](https://jsonlint.com/) 验证。

## DeepSeek 模型特点

- **DeepSeek Coder**: 专为编程优化，代码生成能力强
- **DeepSeek Chat**: 通用对话，上下文更长（32K）
- **性价比高**: 相比 GPT-4 成本更低
- **响应速度快**: 通常比 Claude 响应更快

## 高级功能

### 自定义系统提示
在配置中添加：
```json
{
  "models": [
    {
      "title": "DeepSeek Coder",
      "provider": "openai",
      "model": "deepseek-coder",
      "apiKey": "${env:DEEPSEEK_API_KEY}",
      "apiBase": "https://api.deepseek.com",
      "systemMessage": "你是一个专业的 Python 开发助手，擅长 Odoo 开发和建筑工程管理系统。"
    }
  ]
}
```

### 多模型配置
```json
{
  "models": [
    {
      "title": "DeepSeek Coder",
      "provider": "openai",
      "model": "deepseek-coder",
      "apiKey": "${env:DEEPSEEK_API_KEY}",
      "apiBase": "https://api.deepseek.com"
    },
    {
      "title": "Claude 3.7 Sonnet",
      "provider": "anthropic",
      "model": "claude-3-7-sonnet-20250219"
    }
  ]
}
```

## 获取帮助

1. **详细文档**: 查看 `docs/continue-deepseek-config.md`
2. **配置文件示例**: 查看 `config/continue-deepseek.json`
3. **脚本帮助**: 运行配置脚本查看帮助信息

---

**立即开始：**
1. 获取 DeepSeek API Key
2. 运行配置脚本
3. 重启 Continue
4. 享受 DeepSeek 的强大功能！

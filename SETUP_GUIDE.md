# Continue CLI 配置和使用指南

## 问题诊断

根据检查，你的 `cn` 命令可能没有正确配置。以下是解决方案：

## 解决方案

### 步骤 1：安装 Continue

```powershell
# 以管理员身份打开 PowerShell
# 安装 Continue CLI
npm install -g @continuedev/cli

# 验证安装
continue --version
```

### 步骤 2：设置 DeepSeek API Key

```powershell
# 设置环境变量
$env:DEEPSEEK_API_KEY = "sk-你的_deepseek_api_key"

# 永久设置（推荐）
[System.Environment]::SetEnvironmentVariable('DEEPSEEK_API_KEY', 'sk-你的_api_key', 'User')
```

### 步骤 3：创建配置文件

创建文件：`C:\Users\Admin\.continue\config.json`

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

### 步骤 4：创建 cn 别名

打开 PowerShell 配置文件：
```powershell
# 编辑配置文件
notepad $PROFILE
```

添加以下内容：
```powershell
# Continue 别名
function cn {
    continue @args
}

# 其他有用别名
Set-Alias -Name cna -Value continue
Set-Alias -Name ai -Value continue
```

保存文件，然后重新加载：
```powershell
. $PROFILE
```

### 步骤 5：验证配置

```powershell
# 测试 cn 命令
cn --version

# 测试 Continue
continue --help

# 测试 DeepSeek 连接
cn "你好，请用中文回答"
```

## 快速测试脚本

创建一个测试脚本 `test-continue.ps1`：

```powershell
# 测试 Continue 配置
echo "=== Continue 配置测试 ==="

echo "1. 检查 Continue 安装:"
if (Get-Command continue -ErrorAction SilentlyContinue) {
    echo "   ✅ Continue 已安装"
    continue --version
} else {
    echo "   ❌ Continue 未安装"
}

echo "\n2. 检查配置文件:"
$configPath = "$env:USERPROFILE\.continue\config.json"
if (Test-Path $configPath) {
    echo "   ✅ 配置文件存在: $configPath"
    Get-Content $configPath | Select-Object -First 10
} else {
    echo "   ❌ 配置文件不存在"
}

echo "\n3. 检查环境变量:"
if ($env:DEEPSEEK_API_KEY) {
    echo "   ✅ DeepSeek API Key 已设置"
} else {
    echo "   ❌ DeepSeek API Key 未设置"
}

echo "\n4. 检查 cn 命令:"
if (Get-Command cn -ErrorAction SilentlyContinue) {
    echo "   ✅ cn 命令可用"
} else {
    echo "   ❌ cn 命令不可用"
}

echo "\n=== 测试完成 ==="
```

运行测试：
```powershell
.\test-continue.ps1
```

## 常见问题

### Q1: `cn` 命令不存在
**原因**: PowerShell 配置文件未加载或别名未设置
**解决**: 
```powershell
# 重新加载配置文件
. $PROFILE

# 或手动创建别名
function cn { continue @args }
```

### Q2: Continue 未安装
**解决**:
```powershell
# 安装 Continue
npm install -g @continuedev/cli

# 如果 npm 不可用，先安装 Node.js
# 访问 https://nodejs.org 下载安装
```

### Q3: 配置文件错误
**解决**:
1. 检查 JSON 格式：https://jsonlint.com
2. 确保文件路径正确：`C:\Users\Admin\.continue\config.json`
3. 重启 PowerShell

### Q4: API Key 无效
**解决**:
1. 获取有效的 DeepSeek API Key：https://platform.deepseek.com
2. 验证 API Key：
```powershell
# 测试 API 连接
$apiKey = $env:DEEPSEEK_API_KEY
$body = @{
    model = "deepseek-chat"
    messages = @(@{role = "user"; content = "Hello"})
} | ConvertTo-Json

Invoke-RestMethod -Uri "https://api.deepseek.com/v1/chat/completions" \
    -Method Post \
    -Headers @{"Authorization" = "Bearer $apiKey"; "Content-Type" = "application/json"} \
    -Body $body
```

## 使用示例

### 交互模式
```powershell
# 启动交互模式
cn

# 在交互模式中：
@ 请帮我写一个Python函数
! ls -la  # 执行 shell 命令
/model    # 查看模型
/clear    # 清除历史
/exit     # 退出
```

### 单次查询
```powershell
# 直接提问
cn "用Python写一个快速排序算法"

# 带文件上下文
cn --context "app.py" "请优化这段代码"
```

### 批量处理
```powershell
# 处理多个文件
foreach ($file in Get-ChildItem *.py) {
    $result = cn "分析 $($file.Name) 中的代码"
    $result | Out-File "$($file.BaseName)_analysis.txt"
}
```

## 高级配置

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
      "title": "GPT-4",
      "provider": "openai",
      "model": "gpt-4",
      "apiKey": "${env:OPENAI_API_KEY}"
    }
  ],
  "defaultModel": "DeepSeek Coder"
}
```

### 自定义系统提示
```json
{
  "models": [{
    "title": "DeepSeek Coder",
    "provider": "openai",
    "model": "deepseek-coder",
    "apiKey": "${env:DEEPSEEK_API_KEY}",
    "apiBase": "https://api.deepseek.com",
    "systemMessage": "你是一个专业的编程助手，擅长 Python 和 Odoo 开发。请用中文回答，代码注释用英文。"
  }]
}
```

## 立即开始

1. **安装 Continue**: `npm install -g @continuedev/cli`
2. **设置 API Key**: `$env:DEEPSEEK_API_KEY = "sk-xxx"`
3. **创建配置文件**: 复制上面的 JSON 配置
4. **创建别名**: 在 PowerShell 配置文件中添加 `function cn { continue @args }`
5. **测试**: `cn "你好"`

如果还有问题，请提供具体的错误信息。
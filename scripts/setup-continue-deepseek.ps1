# Continue DeepSeek 配置脚本 (PowerShell)
# 使用方法: .\scripts\setup-continue-deepseek.ps1

Write-Host "=== Continue DeepSeek 配置工具 ===" -ForegroundColor Cyan

# 1. 检查 Continue 配置目录
$continueDir = "$env:USERPROFILE\.continue"
if (-not (Test-Path $continueDir)) {
    Write-Host "创建 Continue 配置目录..." -ForegroundColor Yellow
    New-Item -ItemType Directory -Path $continueDir -Force | Out-Null
}

# 2. 询问 DeepSeek API Key
$deepseekKey = Read-Host "请输入 DeepSeek API Key (留空跳过)"

if ($deepseekKey) {
    # 设置环境变量
    Write-Host "设置环境变量..." -ForegroundColor Yellow
    $env:DEEPSEEK_API_KEY = $deepseekKey
    
    # 可选：永久设置
    $setPermanent = Read-Host "是否永久设置环境变量？(y/n)"
    if ($setPermanent -eq 'y') {
        [System.Environment]::SetEnvironmentVariable('DEEPSEEK_API_KEY', $deepseekKey, 'User')
        Write-Host "已永久设置环境变量" -ForegroundColor Green
    }
}

# 3. 复制配置文件
Write-Host "复制配置文件..." -ForegroundColor Yellow
$configSource = "$PSScriptRoot\..\config\continue-deepseek.json"
$configDest = "$continueDir\config.json"

if (Test-Path $configSource) {
    Copy-Item -Path $configSource -Destination $configDest -Force
    Write-Host "配置文件已复制到: $configDest" -ForegroundColor Green
} else {
    Write-Host "警告：配置文件不存在: $configSource" -ForegroundColor Red
    
    # 创建默认配置
    $defaultConfig = @'
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
  "allowAnonymousTelemetry": false,
  "experimental": {
    "disableIndexing": true
  }
}
'@
    
    Set-Content -Path $configDest -Value $defaultConfig -Encoding UTF8
    Write-Host "已创建默认配置文件" -ForegroundColor Green
}

# 4. 验证配置
Write-Host "\n验证配置..." -ForegroundColor Cyan
if (Test-Path $configDest) {
    $configContent = Get-Content $configDest -Raw
    if ($configContent -match 'deepseek') {
        Write-Host "✅ DeepSeek 配置检测成功" -ForegroundColor Green
    } else {
        Write-Host "⚠️  配置文件中未找到 DeepSeek 配置" -ForegroundColor Yellow
    }
} else {
    Write-Host "❌ 配置文件不存在" -ForegroundColor Red
}

# 5. 检查环境变量
if ($env:DEEPSEEK_API_KEY) {
    Write-Host "✅ DeepSeek API Key 已设置" -ForegroundColor Green
} else {
    Write-Host "⚠️  DeepSeek API Key 未设置" -ForegroundColor Yellow
    Write-Host "   请手动设置: `$env:DEEPSEEK_API_KEY = '你的_api_key'" -ForegroundColor Yellow
}

# 6. 显示下一步操作
Write-Host "\n=== 下一步操作 ===" -ForegroundColor Cyan
Write-Host "1. 重启 Continue 服务:" -ForegroundColor White
Write-Host "   - 在 VS Code 中: Ctrl+Shift+P -> 'Developer: Reload Window'" -ForegroundColor Gray
Write-Host "   - 在 CLI 中: 重启 continue 进程" -ForegroundColor Gray
Write-Host "\n2. 验证模型:" -ForegroundColor White
Write-Host "   - 在 Continue 中输入 '/model' 查看可用模型" -ForegroundColor Gray
Write-Host "   - 输入 '/model DeepSeek Coder' 切换到 DeepSeek" -ForegroundColor Gray
Write-Host "\n3. 测试模型:" -ForegroundColor White
Write-Host "   - 输入 '@ 写一个 Python Hello World 程序'" -ForegroundColor Gray

Write-Host "\n=== 配置完成 ===" -ForegroundColor Green
Write-Host "配置文件位置: $configDest" -ForegroundColor Gray
Write-Host "文档参考: docs/continue-deepseek-config.md" -ForegroundColor Gray
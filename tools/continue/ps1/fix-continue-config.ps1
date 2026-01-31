# Continue 一键配置修复脚本

Write-Host "=== Continue 配置修复 ===" -ForegroundColor Cyan

# 1. 安装 Continue
Write-Host "\n1. 安装 Continue CLI..." -ForegroundColor Yellow
try {
    npm install -g @continuedev/cli
    if ($LASTEXITCODE -eq 0) {
        Write-Host "   ✅ Continue 安装成功" -ForegroundColor Green
    } else {
        Write-Host "   ❌ Continue 安装失败" -ForegroundColor Red
        Write-Host "   请手动安装: npm install -g @continuedev/cli" -ForegroundColor Gray
    }
} catch {
    Write-Host "   ❌ 安装出错: $_" -ForegroundColor Red
}

# 2. 创建配置文件
Write-Host "\n2. 创建配置文件..." -ForegroundColor Yellow
$configPath = "$env:USERPROFILE\.continue\config.json"
$configDir = Split-Path $configPath -Parent

if (-not (Test-Path $configDir)) {
    New-Item -ItemType Directory -Path $configDir -Force | Out-Null
}

$configContent = @'
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
  "allowAnonymousTelemetry": false,
  "experimental": {
    "disableIndexing": true
  }
}
'@

Set-Content -Path $configPath -Value $configContent -Encoding UTF8
Write-Host "   ✅ 配置文件已创建: $configPath" -ForegroundColor Green

# 3. 设置 cn 别名
Write-Host "\n3. 设置 cn 别名..." -ForegroundColor Yellow
$profilePath = $PROFILE.CurrentUserCurrentHost

if (-not (Test-Path $profilePath)) {
    New-Item -ItemType File -Path $profilePath -Force | Out-Null
    Write-Host "   创建 PowerShell 配置文件: $profilePath" -ForegroundColor Gray
}

# 检查是否已存在 cn 别名
$profileContent = Get-Content $profilePath -Raw -ErrorAction SilentlyContinue
if ($profileContent -notmatch "function cn") {
    $aliasContent = @'

# Continue AI 助手别名
function cn {
    continue @args
}

# 其他有用别名
Set-Alias -Name cna -Value continue
Set-Alias -Name ai -Value continue
'@
    
    Add-Content -Path $profilePath -Value $aliasContent
    Write-Host "   ✅ cn 别名已添加到配置文件" -ForegroundColor Green
} else {
    Write-Host "   ⚠️  cn 别名已存在" -ForegroundColor Yellow
}

# 4. 提示设置 API Key
Write-Host "\n4. 设置 DeepSeek API Key:" -ForegroundColor Yellow
Write-Host "   请运行以下命令设置 API Key:" -ForegroundColor White
Write-Host "   ```powershell" -ForegroundColor Gray
Write-Host "   # 临时设置" -ForegroundColor Gray
Write-Host "   `$env:DEEPSEEK_API_KEY = 'sk-你的_api_key'" -ForegroundColor Gray
Write-Host "   " -ForegroundColor Gray
Write-Host "   # 永久设置" -ForegroundColor Gray
Write-Host "   [System.Environment]::SetEnvironmentVariable('DEEPSEEK_API_KEY', 'sk-你的_api_key', 'User')" -ForegroundColor Gray
Write-Host "   ```" -ForegroundColor Gray

# 5. 重新加载配置文件
Write-Host "\n5. 重新加载配置文件..." -ForegroundColor Yellow
try {
    . $profilePath
    Write-Host "   ✅ 配置文件已重新加载" -ForegroundColor Green
} catch {
    Write-Host "   ⚠️  重新加载失败，请重启 PowerShell" -ForegroundColor Yellow
}

# 6. 验证配置
Write-Host "\n6. 验证配置:" -ForegroundColor Cyan

# 检查 Continue
$continueCmd = Get-Command continue -ErrorAction SilentlyContinue
if ($continueCmd) {
    Write-Host "   ✅ Continue 命令可用" -ForegroundColor Green
} else {
    Write-Host "   ❌ Continue 命令不可用" -ForegroundColor Red
}

# 检查 cn 别名
$cnCmd = Get-Command cn -ErrorAction SilentlyContinue
if ($cnCmd) {
    Write-Host "   ✅ cn 命令可用" -ForegroundColor Green
} else {
    Write-Host "   ❌ cn 命令不可用，请重启 PowerShell" -ForegroundColor Red
}

# 检查配置文件
if (Test-Path $configPath) {
    Write-Host "   ✅ 配置文件存在" -ForegroundColor Green
} else {
    Write-Host "   ❌ 配置文件不存在" -ForegroundColor Red
}

Write-Host "\n=== 配置完成 ===" -ForegroundColor Green
Write-Host "\n下一步:" -ForegroundColor White
Write-Host "1. 获取 DeepSeek API Key: https://platform.deepseek.com" -ForegroundColor Gray
Write-Host "2. 设置 API Key (见上面的命令)" -ForegroundColor Gray
Write-Host "3. 重启 PowerShell 或运行: . `$PROFILE" -ForegroundColor Gray
Write-Host "4. 测试: cn "你好，请用中文回答"" -ForegroundColor Gray

Write-Host "\n如果仍有问题，请查看详细指南: tools/continue/docs/SETUP_GUIDE.md" -ForegroundColor Gray

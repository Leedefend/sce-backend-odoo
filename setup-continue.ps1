# Continue 配置和安装脚本

Write-Host "=== Continue AI 助手配置工具 ===" -ForegroundColor Cyan

# 1. 检查 Continue 安装
Write-Host "检查 Continue 安装状态..." -ForegroundColor Yellow

$continueInstalled = $false

# 检查 npm 安装
$npmCheck = npm list -g @continuedev/cli --depth=0 2>$null
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Continue 已通过 npm 安装" -ForegroundColor Green
    $continueInstalled = $true
}

# 检查其他安装方式
if (-not $continueInstalled) {
    Write-Host "❌ Continue 未安装或未找到" -ForegroundColor Red
    
    $installChoice = Read-Host "是否安装 Continue？(y/n)"
    if ($installChoice -eq 'y') {
        Write-Host "正在安装 Continue..." -ForegroundColor Yellow
        npm install -g @continuedev/cli
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ Continue 安装成功" -ForegroundColor Green
            $continueInstalled = $true
        } else {
            Write-Host "❌ Continue 安装失败" -ForegroundColor Red
            exit 1
        }
    }
}

# 2. 配置 DeepSeek API Key
Write-Host "\n=== 配置 DeepSeek API Key ===" -ForegroundColor Cyan

$deepseekKey = Read-Host "请输入 DeepSeek API Key (留空跳过)"

if ($deepseekKey) {
    # 设置环境变量
    $env:DEEPSEEK_API_KEY = $deepseekKey
    Write-Host "✅ 已设置临时环境变量" -ForegroundColor Green
    
    # 永久设置
    $setPermanent = Read-Host "是否永久设置环境变量？(y/n)"
    if ($setPermanent -eq 'y') {
        [System.Environment]::SetEnvironmentVariable('DEEPSEEK_API_KEY', $deepseekKey, 'User')
        Write-Host "✅ 已永久设置环境变量" -ForegroundColor Green
    }
}

# 3. 创建配置文件
Write-Host "\n=== 创建配置文件 ===" -ForegroundColor Cyan

$continueDir = "$env:USERPROFILE\.continue"
if (-not (Test-Path $continueDir)) {
    New-Item -ItemType Directory -Path $continueDir -Force | Out-Null
    Write-Host "创建配置目录: $continueDir" -ForegroundColor Yellow
}

$configPath = "$continueDir\config.json"
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
  "allowAnonymousTelemetry": false
}
'@

Set-Content -Path $configPath -Value $configContent -Encoding UTF8
Write-Host "✅ 配置文件已创建: $configPath" -ForegroundColor Green

# 4. 创建别名
Write-Host "\n=== 创建命令别名 ===" -ForegroundColor Cyan

$profilePath = $PROFILE.CurrentUserCurrentHost
if (-not (Test-Path $profilePath)) {
    New-Item -ItemType File -Path $profilePath -Force | Out-Null
}

# 添加 cn 别名
$aliasContent = @'

# Continue AI 助手别名
function cn {
    continue @args
}

Set-Alias -Name cna -Value continue
'@

Add-Content -Path $profilePath -Value $aliasContent
Write-Host "✅ 已添加 cn 别名到 PowerShell 配置文件" -ForegroundColor Green

# 5. 重新加载配置文件
Write-Host "重新加载 PowerShell 配置文件..." -ForegroundColor Yellow
. $profilePath

# 6. 验证配置
Write-Host "\n=== 验证配置 ===" -ForegroundColor Cyan

Write-Host "1. 检查配置文件:" -ForegroundColor White
if (Test-Path $configPath) {
    Write-Host "   ✅ 配置文件存在" -ForegroundColor Green
    $config = Get-Content $configPath -Raw | ConvertFrom-Json
    Write-Host "   📋 默认模型: $($config.defaultModel)" -ForegroundColor Gray
} else {
    Write-Host "   ❌ 配置文件不存在" -ForegroundColor Red
}

Write-Host "\n2. 检查环境变量:" -ForegroundColor White
if ($env:DEEPSEEK_API_KEY) {
    Write-Host "   ✅ DeepSeek API Key 已设置" -ForegroundColor Green
} else {
    Write-Host "   ⚠️  DeepSeek API Key 未设置" -ForegroundColor Yellow
}

Write-Host "\n3. 检查命令别名:" -ForegroundColor White
if (Get-Command cn -ErrorAction SilentlyContinue) {
    Write-Host "   ✅ cn 命令可用" -ForegroundColor Green
} else {
    Write-Host "   ❌ cn 命令不可用，请重启 PowerShell" -ForegroundColor Red
}

# 7. 使用说明
Write-Host "\n=== 使用说明 ===" -ForegroundColor Cyan
Write-Host "\n1. 启动 Continue:" -ForegroundColor White
Write-Host "   cn                    # 进入交互模式" -ForegroundColor Gray
Write-Host "   continue              # 同上" -ForegroundColor Gray

Write-Host "\n2. 常用命令:" -ForegroundColor White
Write-Host "   @ 你的问题            # 提问" -ForegroundColor Gray
Write-Host "   /model                # 查看可用模型" -ForegroundColor Gray
Write-Host "   /model DeepSeek Coder # 切换模型" -ForegroundColor Gray
Write-Host "   /clear                # 清除对话历史" -ForegroundColor Gray
Write-Host "   /exit                 # 退出" -ForegroundColor Gray

Write-Host "\n3. 直接查询:" -ForegroundColor White
Write-Host "   cn "用Python写一个Hello World"" -ForegroundColor Gray
Write-Host "   continue "分析这段代码"" -ForegroundColor Gray

Write-Host "\n4. 验证安装:" -ForegroundColor White
Write-Host "   cn --version          # 查看版本" -ForegroundColor Gray
Write-Host "   continue --help       # 查看帮助" -ForegroundColor Gray

Write-Host "\n=== 配置完成 ===" -ForegroundColor Green
Write-Host "\n下一步:" -ForegroundColor White
Write-Host "1. 重启 PowerShell 或运行: . `$PROFILE" -ForegroundColor Gray
Write-Host "2. 测试命令: cn "你好，请介绍一下你自己"" -ForegroundColor Gray
Write-Host "3. 如果遇到问题，查看配置文件: $configPath" -ForegroundColor Gray
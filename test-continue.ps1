# Continue 配置测试脚本

Write-Host "=== Continue 配置测试 ===" -ForegroundColor Cyan

# 1. 检查 Continue 安装
Write-Host "\n1. 检查 Continue 安装:" -ForegroundColor White
$continueCmd = Get-Command continue -ErrorAction SilentlyContinue
if ($continueCmd) {
    Write-Host "   ✅ Continue 已安装" -ForegroundColor Green
    Write-Host "   路径: $($continueCmd.Source)" -ForegroundColor Gray
    
    # 尝试获取版本
    try {
        $version = continue --version 2>&1
        Write-Host "   版本: $version" -ForegroundColor Gray
    } catch {
        Write-Host "   版本: 无法获取" -ForegroundColor Yellow
    }
} else {
    Write-Host "   ❌ Continue 未安装" -ForegroundColor Red
    Write-Host "   请运行: npm install -g @continuedev/cli" -ForegroundColor Gray
}

# 2. 检查 cn 命令
Write-Host "\n2. 检查 cn 命令:" -ForegroundColor White
$cnCmd = Get-Command cn -ErrorAction SilentlyContinue
if ($cnCmd) {
    Write-Host "   ✅ cn 命令可用" -ForegroundColor Green
    Write-Host "   类型: $($cnCmd.CommandType)" -ForegroundColor Gray
    Write-Host "   定义: $($cnCmd.Definition)" -ForegroundColor Gray
} else {
    Write-Host "   ❌ cn 命令不可用" -ForegroundColor Red
    Write-Host "   请添加别名到 PowerShell 配置文件:" -ForegroundColor Gray
    Write-Host "   function cn { continue @args }" -ForegroundColor Gray
}

# 3. 检查配置文件
Write-Host "\n3. 检查配置文件:" -ForegroundColor White
$configPath = "$env:USERPROFILE\.continue\config.json"
if (Test-Path $configPath) {
    Write-Host "   ✅ 配置文件存在" -ForegroundColor Green
    Write-Host "   路径: $configPath" -ForegroundColor Gray
    
    # 检查内容
    try {
        $config = Get-Content $configPath -Raw | ConvertFrom-Json -ErrorAction Stop
        Write-Host "   默认模型: $($config.defaultModel)" -ForegroundColor Gray
        
        if ($config.models) {
            Write-Host "   配置的模型:" -ForegroundColor Gray
            foreach ($model in $config.models) {
                Write-Host "     - $($model.title)" -ForegroundColor Gray
            }
        }
    } catch {
        Write-Host "   ⚠️  配置文件格式错误" -ForegroundColor Yellow
    }
} else {
    Write-Host "   ❌ 配置文件不存在" -ForegroundColor Red
    Write-Host "   请创建: $configPath" -ForegroundColor Gray
}

# 4. 检查环境变量
Write-Host "\n4. 检查环境变量:" -ForegroundColor White
if ($env:DEEPSEEK_API_KEY) {
    Write-Host "   ✅ DeepSeek API Key 已设置" -ForegroundColor Green
    Write-Host "   Key: $($env:DEEPSEEK_API_KEY.Substring(0, 10))..." -ForegroundColor Gray
} else {
    Write-Host "   ❌ DeepSeek API Key 未设置" -ForegroundColor Red
    Write-Host "   请设置: `$env:DEEPSEEK_API_KEY = 'sk-你的_api_key'" -ForegroundColor Gray
}

# 5. 检查 Continue 配置目录
Write-Host "\n5. 检查 Continue 目录:" -ForegroundColor White
$continueDir = "$env:USERPROFILE\.continue"
if (Test-Path $continueDir) {
    Write-Host "   ✅ Continue 目录存在" -ForegroundColor Green
    Write-Host "   路径: $continueDir" -ForegroundColor Gray
    
    # 列出文件
    $files = Get-ChildItem $continueDir -File | Select-Object -First 5
    if ($files) {
        Write-Host "   文件:" -ForegroundColor Gray
        foreach ($file in $files) {
            Write-Host "     - $($file.Name)" -ForegroundColor Gray
        }
    }
} else {
    Write-Host "   ❌ Continue 目录不存在" -ForegroundColor Red
}

# 6. 测试 Continue 连接
Write-Host "\n6. 测试 Continue 连接:" -ForegroundColor White
if ($continueCmd -and $env:DEEPSEEK_API_KEY) {
    Write-Host "   正在测试..." -ForegroundColor Yellow
    
    # 创建一个简单的测试
    $testFile = "$env:TEMP\test_continue.txt"
    "这是一个测试文件，用于验证 Continue 是否能读取上下文。" | Out-File $testFile
    
    try {
        # 尝试运行 continue
        $result = continue "请说 'Hello'" 2>&1
        if ($LASTEXITCODE -eq 0 -or $result -match "Hello") {
            Write-Host "   ✅ Continue 连接正常" -ForegroundColor Green
        } else {
            Write-Host "   ⚠️  Continue 连接可能有问题" -ForegroundColor Yellow
            Write-Host "   输出: $($result | Select-Object -First 2)" -ForegroundColor Gray
        }
    } catch {
        Write-Host "   ❌ Continue 测试失败" -ForegroundColor Red
        Write-Host "   错误: $_" -ForegroundColor Gray
    }
    
    # 清理
    Remove-Item $testFile -ErrorAction SilentlyContinue
} else {
    Write-Host "   ⚠️  跳过测试 (Continue 或 API Key 未配置)" -ForegroundColor Yellow
}

Write-Host "\n=== 测试完成 ===" -ForegroundColor Cyan
Write-Host "\n建议:" -ForegroundColor White
if (-not $continueCmd) {
    Write-Host "1. 安装 Continue: npm install -g @continuedev/cli" -ForegroundColor Gray
}
if (-not $cnCmd) {
    Write-Host "2. 创建 cn 别名: function cn { continue @args }" -ForegroundColor Gray
}
if (-not (Test-Path $configPath)) {
    Write-Host "3. 创建配置文件: $configPath" -ForegroundColor Gray
}
if (-not $env:DEEPSEEK_API_KEY) {
    Write-Host "4. 设置 API Key: `$env:DEEPSEEK_API_KEY = 'sk-xxx'" -ForegroundColor Gray
}

Write-Host "\n详细指南请查看: SETUP_GUIDE.md" -ForegroundColor Gray
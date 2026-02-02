#!/bin/bash
# 验证屏幕闪烁修复脚本

echo "=== 屏幕闪烁修复验证 ==="
echo ""

# 检查关键文件是否存在
echo "1. 检查配置文件:"
check_files=(
    ".devcontainer/docker-compose.devcontainer.yml"
    ".devcontainer/Dockerfile.dev"
    ".devcontainer/devcontainer.json"
    ".devcontainer/bashrc"
    "docker-compose.yml"
    "scripts/restart-dev.sh"
    "scripts/check-terminal.sh"
)

all_files_ok=true
for file in "${check_files[@]}"; do
    if [ -f "$file" ]; then
        echo "   ✓ $file"
    else
        echo "   ✗ $file (缺失)"
        all_files_ok=false
    fi
done
echo ""

# 检查Docker容器配置
echo "2. 检查Docker容器TTY配置:"
if command -v docker >/dev/null 2>&1; then
    containers=$(docker ps --format "{{.Names}}" | grep -E "(sc-backend-odoo-odoo-|sc-dev)" || true)
    
    if [ -n "$containers" ]; then
        for container in $containers; do
            tty=$(docker inspect "$container" --format='{{.Config.Tty}}' 2>/dev/null || echo "检查失败")
            stdin=$(docker inspect "$container" --format='{{.Config.OpenStdin}}' 2>/dev/null || echo "检查失败")
            term=$(docker inspect "$container" --format='{{range .Config.Env}}{{println .}}{{end}}' 2>/dev/null | grep TERM || echo "未找到")
            
            echo "   $container:"
            echo "     TTY: $tty"
            echo "     STDIN: $stdin"
            echo "     TERM: $term"
        done
    else
        echo "   未找到相关容器"
    fi
else
    echo "   Docker不可用"
fi
echo ""

# 检查环境变量
echo "3. 检查关键环境变量:"
important_vars=("TERM" "COLORTERM" "LANG" "LC_ALL")
for var in "${important_vars[@]}"; do
    value="${!var}"
    if [ -n "$value" ]; then
        echo "   ✓ $var=$value"
    else
        echo "   ⚠️  $var (未设置)"
    fi
done
echo ""

# 总结
echo "=== 验证结果 ==="
if $all_files_ok; then
    echo "✅ 所有配置文件都存在"
else
    echo "❌ 有些配置文件缺失"
fi

echo ""
echo "=== 下一步 ==="
echo "如果屏幕闪烁问题仍然存在，请尝试："
echo "1. 完全重启VS Code"
echo "2. 在VS Code中重新打开Dev Container："
echo "   - 按 F1"
echo "   - 输入 'Dev Containers: Reopen in Container'"
echo "3. 运行完整重启：./scripts/restart-dev.sh"
echo ""
echo "要检查当前终端配置：./scripts/check-terminal.sh"
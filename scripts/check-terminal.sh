#!/bin/bash
# 检查终端配置脚本

echo "=== 终端配置检查 ==="
echo ""

# 检查环境变量
echo "1. 环境变量检查:"
echo "   TERM: $TERM"
echo "   COLORTERM: $COLORTERM"
echo "   LANG: $LANG"
echo "   LC_ALL: $LC_ALL"
echo ""

# 检查终端类型
echo "2. 终端类型检查:"
if [ -t 1 ]; then
    echo "   ✓ 这是一个交互式终端"
    echo "   终端设备: $(tty 2>/dev/null || echo 'N/A')"
else
    echo "   ✗ 这不是一个交互式终端"
fi
echo ""

# 检查终端能力
echo "3. 终端能力检查:"
if command -v tput >/dev/null 2>&1; then
    echo "   ✓ tput 可用"
    echo "   颜色支持:"
    echo "     - 颜色数: $(tput colors 2>/dev/null || echo 'N/A')"
    echo "     - 列数: $(tput cols 2>/dev/null || echo 'N/A')"
    echo "     - 行数: $(tput lines 2>/dev/null || echo 'N/A')"
else
    echo "   ✗ tput 不可用"
fi
echo ""

# 检查Docker容器TTY设置
echo "4. Docker容器检查:"
if command -v docker >/dev/null 2>&1; then
    echo "   ✓ Docker 可用"
    echo "   当前容器TTY状态:"
    docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Command}}" | grep -E "(sc-|odoo|dev)" || echo "   未找到相关容器"
else
    echo "   ✗ Docker 不可用"
fi
echo ""

# 检查屏幕闪烁相关设置
echo "5. 屏幕闪烁相关检查:"
echo "   stty设置:"
stty -a 2>/dev/null | grep -E "erase|intr|quit|eof" || echo "   stty不可用"
echo ""

echo "=== 建议 ==="
if [ "$TERM" != "xterm-256color" ] && [ "$TERM" != "screen-256color" ]; then
    echo "⚠️  建议设置: export TERM=xterm-256color"
fi

if [ -z "$COLORTERM" ]; then
    echo "⚠️  建议设置: export COLORTERM=truecolor"
fi

echo ""
echo "要解决屏幕闪烁问题，请运行: ./scripts/restart-dev.sh"
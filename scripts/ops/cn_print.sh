#!/bin/bash
# Continue CLI 无闪烁批处理入口脚本
# 强制使用 --print 模式，避免交互式 TUI 闪烁问题
# 用法: 
#   1. 参数模式: scripts/ops/cn_print.sh "prompt..."
#   2. 管道模式: cat prompt.txt | scripts/ops/cn_print.sh

set -euo pipefail

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 超时设置（秒）- 可配置
CN_TIMEOUT="${CN_TIMEOUT:-180}"

# 配置优先级（从高到低）：
# 1. 环境变量 CN_CONFIG（由 Makefile 传入）
# 2. 用户配置 (~/.continue/config.json)
# 3. 用户配置 (~/.continue/config.yaml)
# 4. 项目配置 (tools/continue/config/continue-deepseek.json)

# 项目配置路径
ROOT_DIR="${ROOT_DIR:-$(cd "$(dirname "$0")/../.." && pwd)}"
PROJECT_CONFIG="$ROOT_DIR/tools/continue/config/continue-deepseek.json"
USER_CONFIG_JSON="$HOME/.continue/config.json"
USER_CONFIG_YAML="$HOME/.continue/config.yaml"

# 选择配置文件（简单回退）
CONFIG_FILE=""
CONFIG_SOURCE=""

# 配置优先级（从高到低）：
# 1. 用户配置（通常有有效API Key）
# 2. 传入配置（由Makefile传入）
# 3. 项目配置（可能没有有效API Key）

# 优先用户配置（通常有效）
if [[ -f "$USER_CONFIG_JSON" ]]; then
    CONFIG_FILE="$USER_CONFIG_JSON"
    CONFIG_SOURCE="用户JSON配置"
    echo -e "${GREEN}✓ 使用用户 JSON 配置: $USER_CONFIG_JSON${NC}"
elif [[ -f "$USER_CONFIG_YAML" ]]; then
    CONFIG_FILE="$USER_CONFIG_YAML"
    CONFIG_SOURCE="用户YAML配置"
    echo -e "${GREEN}✓ 使用用户 YAML 配置: $USER_CONFIG_YAML${NC}"
elif [[ -n "${CN_CONFIG:-}" && -f "$CN_CONFIG" ]]; then
    CONFIG_FILE="$CN_CONFIG"
    CONFIG_SOURCE="传入配置"
    echo -e "${BLUE}ℹ 使用传入配置: $CN_CONFIG${NC}"
elif [[ -f "$PROJECT_CONFIG" ]]; then
    CONFIG_FILE="$PROJECT_CONFIG"
    CONFIG_SOURCE="项目配置"
    echo -e "${YELLOW}⚠ 使用项目配置: $PROJECT_CONFIG（用户配置未找到）${NC}"
else
    echo -e "${RED}✗ 错误: 未找到 Continue 配置文件${NC}"
    echo "请检查以下位置:"
    echo "  1. $USER_CONFIG_JSON"
    echo "  2. $USER_CONFIG_YAML"
    echo "  3. $PROJECT_CONFIG"
    exit 1
fi

# 读取提示
PROMPT=""
if [[ $# -gt 0 ]]; then
    # 参数模式: 将所有参数连接为提示
    PROMPT="$*"
    echo -e "${BLUE}ℹ 使用参数模式，提示长度: ${#PROMPT} 字符${NC}"
elif [[ ! -t 0 ]]; then
    # 管道模式: 从 stdin 读取
    PROMPT=$(cat)
    echo -e "${BLUE}ℹ 使用管道模式，提示长度: ${#PROMPT} 字符${NC}"
else
    echo -e "${RED}✗ 错误: 需要提供提示${NC}"
    echo "用法:"
    echo "  参数模式: $0 \"prompt...\""
    echo "  管道模式: cat prompt.txt | $0"
    echo ""
    echo "示例:"
    echo "  $0 \"分析代码问题\""
    echo "  echo \"修复bug\" | $0"
    exit 1
fi

# 验证提示非空
if [[ -z "$PROMPT" ]]; then
    echo -e "${RED}✗ 错误: 提示为空${NC}"
    exit 1
fi

# 超时设置（秒）
TIMEOUT=180

echo -e "${GREEN}▶ 开始执行 Continue 批处理任务${NC}"
echo "配置: $CONFIG_FILE"
echo "超时: ${CN_TIMEOUT}秒"
echo "提示摘要: ${PROMPT:0:100}..."

# 硬修复：强制headless、禁用TUI、禁用重绘
echo -e "${BLUE}ℹ 应用硬修复: CI=1 NO_COLOR=1 TERM=dumb${NC}"

# 临时错误文件
ERROR_FILE=$(mktemp /tmp/cn_print.err.XXXXXX)
trap 'rm -f "$ERROR_FILE"' EXIT

# 执行命令（硬修复版本）
set +e  # 允许命令失败，以便处理超时
if CI=1 NO_COLOR=1 TERM=dumb timeout $CN_TIMEOUT cn --print --config "$CONFIG_FILE" -- "$PROMPT" 2>"$ERROR_FILE"; then
    echo -e "${GREEN}✓ 任务完成${NC}"
    # 检查是否有警告信息
    if [[ -s "$ERROR_FILE" ]]; then
        echo -e "${YELLOW}⚠ 警告信息:${NC}"
        cat "$ERROR_FILE" | head -20
    fi
    exit 0
else
    EXIT_CODE=$?
    if [[ $EXIT_CODE -eq 124 ]]; then
        echo -e "${YELLOW}⚠ 任务超时 (${CN_TIMEOUT}秒)${NC}"
        echo "建议:"
        echo "  1. 简化任务描述"
        echo "  2. 增加超时时间: export CN_TIMEOUT=300"
        echo "  3. 分步骤执行复杂任务"
    elif [[ $EXIT_CODE -eq 1 ]]; then
        echo -e "${RED}✗ 任务失败: Continue CLI 错误${NC}"
        if [[ -s "$ERROR_FILE" ]]; then
            echo "错误详情:"
            cat "$ERROR_FILE" | head -20
        fi
        echo "可能原因:"
        echo "  1. 配置错误"
        echo "  2. API Key 无效"
        echo "  3. 网络问题"
    else
        echo -e "${RED}✗ 任务失败，退出码: $EXIT_CODE${NC}"
        if [[ -s "$ERROR_FILE" ]]; then
            echo "错误详情:"
            cat "$ERROR_FILE" | head -20
        fi
    fi
    exit $EXIT_CODE
fi

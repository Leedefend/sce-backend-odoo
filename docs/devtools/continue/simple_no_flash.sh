#!/bin/bash
# 简单的无闪烁包装脚本
# 仅使用 --print 模式，适用于大多数任务

set -e

if [ $# -lt 1 ]; then
    echo "用法: $0 \"任务描述\" [输出文件]"
    echo "示例: $0 \"修复代码bug\" output.txt"
    exit 1
fi

PROMPT="$1"
OUTPUT_FILE="${2:-/dev/stdout}"
TIMEOUT=${3:-120}  # 默认120秒超时

echo "开始处理任务: $PROMPT"
echo "超时设置: ${TIMEOUT}秒"

# 使用 timeout 命令防止无限等待
if timeout $TIMEOUT cn --print "$PROMPT" > "$OUTPUT_FILE" 2>&1; then
    echo "✓ 任务完成"
    if [ "$OUTPUT_FILE" != "/dev/stdout" ]; then
        echo "输出保存到: $OUTPUT_FILE"
        echo "文件大小: $(wc -l < "$OUTPUT_FILE") 行"
    fi
else
    EXIT_CODE=$?
    if [ $EXIT_CODE -eq 124 ]; then
        echo "✗ 任务超时 (${TIMEOUT}秒)"
        echo "建议:"
        echo "1. 简化任务描述"
        echo "2. 增加超时时间: $0 \"$PROMPT\" $OUTPUT_FILE 300"
        echo "3. 分步骤执行复杂任务"
    else
        echo "✗ 任务失败，退出码: $EXIT_CODE"
        echo "请检查 Continue 服务状态"
    fi
    exit $EXIT_CODE
fi
#!/bin/bash
# Continue 无闪烁包装脚本
# 用法: ./no_flash.sh "任务描述" [输出文件]

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 参数检查
if [ $# -lt 1 ]; then
    echo -e "${RED}错误: 需要任务描述作为参数${NC}"
    echo "用法: $0 \"任务描述\" [输出文件]"
    echo "示例: $0 \"修复代码中的bug\" output.txt"
    exit 1
fi

PROMPT="$1"
OUTPUT_FILE="${2:-continue_output_$(date +%Y%m%d_%H%M%S).txt}"

echo -e "${YELLOW}=== Continue 无闪烁模式启动 ===${NC}"
echo "任务: $PROMPT"
echo "输出文件: $OUTPUT_FILE"
echo "开始时间: $(date)"

# 方法1: 尝试 --print 模式
echo -e "${YELLOW}尝试方法1: --print 模式${NC}"
if timeout 120 cn --print "$PROMPT" > "$OUTPUT_FILE" 2>&1; then
    echo -e "${GREEN}成功! 使用 --print 模式完成${NC}"
    echo "输出已保存到: $OUTPUT_FILE"
    echo "文件大小: $(wc -l < "$OUTPUT_FILE") 行"
    exit 0
else
    echo -e "${YELLOW}方法1失败或超时，尝试方法2${NC}"
fi

# 方法2: 使用临时文件交互
echo -e "${YELLOW}尝试方法2: 文件交互模式${NC}"
TEMP_PROMPT_FILE=$(mktemp)
echo "$PROMPT" > "$TEMP_PROMPT_FILE"

# 创建期望脚本来自动处理交互
EXPECT_SCRIPT=$(mktemp)
cat > "$EXPECT_SCRIPT" << 'EOF'
#!/usr/bin/expect -f
set timeout 300
spawn cn --config ~/.continue/config.yaml --verbose

# 等待提示符
expect "> "

# 发送提示
send "[read file $env(TEMP_PROMPT_FILE)]\r"

# 处理可能的确认
while {1} {
    expect {
        "Press Enter to continue" {
            send "\r"
            exp_continue
        }
        "Do you want to continue?" {
            send "y\r"
            exp_continue
        }
        "Apply these changes?" {
            send "y\r"
            exp_continue
        }
        "> " {
            # 会话结束
            send "exit\r"
            break
        }
        eof {
            break
        }
        timeout {
            puts "超时"
            exit 1
        }
    }
}
EOF

chmod +x "$EXPECT_SCRIPT"
if expect -f "$EXPECT_SCRIPT" > "$OUTPUT_FILE" 2>&1; then
    echo -e "${GREEN}成功! 使用期望脚本完成${NC}"
else
    echo -e "${RED}所有方法都失败了${NC}"
    echo "请检查:"
    echo "1. Continue 服务是否运行"
    echo "2. 网络连接是否正常"
    echo "3. API Key 是否有效"
    exit 1
fi

# 清理
rm -f "$TEMP_PROMPT_FILE" "$EXPECT_SCRIPT"

echo -e "${GREEN}=== 任务完成 ===${NC}"
echo "结束时间: $(date)"
echo "输出文件: $OUTPUT_FILE"
echo "预览前10行:"
head -10 "$OUTPUT_FILE"
#!/usr/bin/env bash
# 清理过期输出物脚本
# 用法: bash scripts/cleanup_outputs.sh [天数]
# 默认清理7天前的文件

DAYS=${1:-7}

echo"🧹 清理 ${DAYS} 天前的输出物..."

# 清理用户目录
if [ -d "$HOME/.jdcloud-routines-ops/outputs" ]; then
    echo "  →清理 ~/.jdcloud-routines-ops/outputs"
    find "$HOME/.jdcloud-routines-ops/outputs" -type f -mtime +${DAYS} -delete 2>/dev/null
fi

# 清理项目目录
if [ -d "./jdcloud-routines-ops/outputs" ]; then
    echo "  → 清理 ./jdcloud-routines-ops/outputs"
    find "./jdcloud-routines-ops/outputs" -type f -mtime +${DAYS} -delete 2>/dev/null
fi

echo "✅清理完成"
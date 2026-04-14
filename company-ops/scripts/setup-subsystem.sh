#!/bin/bash
# setup-subsystem - 子系统完整创建脚本（两阶段）
#
# 用法:
#   bash scripts/setup-subsystem.sh <subsystem-name> [type]
#
# 或直接调用 init_subsystem.py 后运行此脚本的 Phase 2
#   python scripts/init_subsystem.py <subsystem-name> --type=<type>
#   bash scripts/setup-subsystem.sh <subsystem-name> --interactive

set -e

SUBSYSTEM_NAME="${1:-}"
SUBSYSTEM_TYPE="${2:-function}"
INTERACTIVE=false

# 解析参数
for arg in "$@"; do
    case $arg in
        --interactive)
            INTERACTIVE=true
            ;;
    esac
done

if [ -z "$SUBSYSTEM_NAME" ]; then
    echo "用法: $0 <subsystem-name> [type]"
    echo "  type: function, product, tool (默认: function)"
    echo ""
    echo "示例:"
    echo "  $0 财务"
    echo "  $0 研发 function"
    exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
BASE_DIR="$(dirname "$SCRIPT_DIR")"
SUBSYSTEM_PATH="$BASE_DIR/subsystems/$SUBSYSTEM_NAME"

echo "========================================="
echo "子系统创建: $SUBSYSTEM_NAME"
echo "类型: $SUBSYSTEM_TYPE"
echo "========================================="

# Phase 1: 创建基础模板
if [ ! -d "$SUBSYSTEM_PATH" ]; then
    echo ""
    echo "Phase 1: 创建基础模板..."
    python3 "$SCRIPT_DIR/init_subsystem.py" "$SUBSYSTEM_NAME" --type="$SUBSYSTEM_TYPE"
else
    echo "Phase 1: 基础模板已存在，跳过"
fi

# Phase 2: 交互式问答
echo ""
echo "========================================="
echo "Phase 2: 交互式完善"
echo "========================================="
echo ""
echo "请运行以下 Skill 来完成交互式问答："
echo ""
echo "  /new-subsystem"
echo ""
echo "或者在 Claude Code 中输入："
echo "  !new-subsystem $SUBSYSTEM_NAME"
echo ""

if [ "$INTERACTIVE" = true ]; then
    echo "启动交互式问答..."
    # 这里可以添加交互式问答的调用
    echo "交互式问答启动！"
fi

echo ""
echo "完成！子系统已创建在: $SUBSYSTEM_PATH"
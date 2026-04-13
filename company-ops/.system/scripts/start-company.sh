#!/bin/bash
# company-ops 启动脚本
# 用于在 cmux 中启动公司运营系统

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 配置
COMPANY_OPS_ROOT="${COMPANY_OPS_ROOT:-$(cd "$(dirname "$0")/../.." && pwd)}"
WORKSPACE_PREFIX="company-ops"

echo -e "${BLUE}================================================${NC}"
echo -e "${BLUE}    Company-Ops 启动脚本${NC}"
echo -e "${BLUE}================================================${NC}"
echo ""

# 检查是否在 company-ops 目录
if [ ! -f "$COMPANY_OPS_ROOT/CHARTER.md" ]; then
    echo -e "${RED}错误: 未找到 company-ops 根目录${NC}"
    echo "请设置 COMPANY_OPS_ROOT 环境变量或在 company-ops 目录下运行"
    exit 1
fi

echo -e "${GREEN}Company-Ops 根目录: $COMPANY_OPS_ROOT${NC}"
echo ""

# 函数: 创建或切换到工作区
setup_workspace() {
    local workspace_num=$1
    local workspace_name=$2
    local working_dir=$3
    local description=$4

    echo -e "${YELLOW}设置工作区 $workspace_num: $workspace_name${NC}"
    echo "  描述: $description"
    echo "  目录: $working_dir"

    # 检查目录是否存在
    if [ ! -d "$working_dir" ]; then
        echo -e "${RED}  警告: 目录不存在，创建中...${NC}"
        mkdir -p "$working_dir"
    fi

    # 如果在 tmux/cmux 中
    if [ -n "$TMUX" ]; then
        # 创建新窗口
        tmux new-window -t "$WORKSPACE_PREFIX:$workspace_num" -n "$workspace_name" -c "$working_dir" 2>/dev/null || {
            # 窗口可能已存在，切换到它
            tmux select-window -t "$WORKSPACE_PREFIX:$workspace_num" 2>/dev/null || true
        }
    fi

    echo -e "${GREEN}  ✓ 工作区 $workspace_num 就绪${NC}"
    echo ""
}

# 检测是否在 tmux 会话中
if [ -n "$TMUX" ]; then
    echo -e "${GREEN}检测到 tmux 会话，将创建多工作区${NC}"
    echo ""

    # 创建会话（如果不存在）
    tmux has-session -t "$WORKSPACE_PREFIX" 2>/dev/null || {
        tmux new-session -d -s "$WORKSPACE_PREFIX" -c "$COMPANY_OPS_ROOT"
    }
else
    echo -e "${YELLOW}未检测到 tmux 会话，将显示手动设置指南${NC}"
    echo ""
fi

# 工作区 0: 公司总调度
setup_workspace 0 "orchestration" "$COMPANY_OPS_ROOT" "公司总调度 - 全局协调和监控"

# 读取子系统注册表，为每个活跃子系统创建工作区
REGISTRY_FILE="$COMPANY_OPS_ROOT/subsystems/_registry.json"
if [ -f "$REGISTRY_FILE" ]; then
    echo -e "${BLUE}读取子系统注册表...${NC}"

    # 使用 Python 解析 JSON（兼容性更好）
    ACTIVE_SUBSYSTEMS=$(python3 -c "
import json
import sys
with open('$REGISTRY_FILE', 'r') as f:
    registry = json.load(f)
for i, sub in enumerate(registry.get('subsystems', []), 1):
    if sub.get('status') in ['active', 'planned']:
        print(f\"{i}|{sub['id']}|{sub['name']}|{sub.get('status', 'unknown')}\")")
    )

    workspace_num=1
    while IFS='|' read -r idx sub_id sub_name sub_status; do
        sub_dir="$COMPANY_OPS_ROOT/subsystems/$sub_id"
        setup_workspace $workspace_num "$sub_id" "$sub_dir" "$sub_name ($sub_status)"
        workspace_num=$((workspace_num + 1))
    done <<< "$ACTIVE_SUBSYSTEMS"
fi

echo ""
echo -e "${GREEN}================================================${NC}"
echo -e "${GREEN}    启动完成！${NC}"
echo -e "${GREEN}================================================${NC}"
echo ""
echo "工作区列表:"
echo "  0 - orchestration (公司总调度)"
if [ -n "$ACTIVE_SUBSYSTEMS" ]; then
    workspace_num=1
    while IFS='|' read -r idx sub_id sub_name sub_status; do
        echo "  $workspace_num - $sub_id ($sub_name)"
        workspace_num=$((workspace_num + 1))
    done <<< "$ACTIVE_SUBSYSTEMS"
fi
echo ""
echo -e "${YELLOW}下一步:${NC}"
echo "1. 在各工作区中启动 Claude Code"
echo "2. 运行 python shared/tools/check_completeness.py --all 检查系统状态"
echo "3. 查阅 docs/deployment/cmux-workspace-setup.md 了解详细操作"
echo ""

# 如果在 tmux 中，切换到工作区 0
if [ -n "$TMUX" ]; then
    tmux select-window -t "$WORKSPACE_PREFIX:0"
    echo -e "${GREEN}已切换到工作区 0 (公司总调度)${NC}"
fi

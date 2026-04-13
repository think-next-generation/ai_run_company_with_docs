#!/usr/bin/env python3
"""
cmux 工作区初始化脚本

由于 cmux CLI 安全限制（只能从 cmux 内部运行），
此脚本生成需要在 cmux 终端中执行的命令。

用法:
    python shared/tools/cmux_init.py --init        # 生成初始化命令
    python shared/tools/cmux_init.py --status      # 查看状态
    python shared/tools/cmux_init.py --start 财务  # 生成启动命令
    python shared/tools/cmux_init.py --guide       # 显示使用指南
"""

import json
import argparse
from pathlib import Path
from datetime import datetime


class CmuxManager:
    """cmux 工作区管理器（生成命令模式）"""

    def __init__(self, base_path: str = None):
        self.base_path = Path(base_path or ".")
        self.registry_path = self.base_path / "subsystems" / "_registry.json"

    def get_registry(self) -> dict:
        """获取子系统注册表"""
        if self.registry_path.exists():
            with open(self.registry_path, "r", encoding="utf-8") as f:
                return json.load(f)
        return {"subsystems": []}

    def get_subsystems_to_init(self) -> list:
        """获取需要初始化的工作区"""
        registry = self.get_registry()
        return [s for s in registry.get("subsystems", [])
                if s.get("status") in ("active", "planned")]

    def show_init_commands(self):
        """显示初始化命令"""
        print("=" * 60)
        print("📋 cmux 初始化命令")
        print("⚠️ 注意：需要在 cmux 终端面板中运行！")
        print("=" * 60)
        print()

        base = self.base_path.resolve()

        # orchestrator 是第一个工作区（手动打开 cmux 时自动创建）
        print("# 工作区 1: orchestrator (手动打开 cmux 时自动创建)")
        print(f"# cwd: {base}")
        print()

        # 创建子系统工作区
        for i, subsystem in enumerate(self.get_subsystems_to_init(), 2):
            subsystem_id = subsystem["id"]
            subsystem_path = subsystem.get("path", f"subsystems/{subsystem_id}")
            full_path = (self.base_path / subsystem_path).resolve()

            print(f"# 工作区 {i}: {subsystem_id}")
            print(f'cmux new-workspace --name "{subsystem_id}" --cwd "{full_path}"')
            print()

        print("=" * 60)
        print("📖 使用说明:")
        print("  1. 在 cmux 中打开一个终端面板")
        print("  2. 逐行复制粘贴上述命令执行")
        print("  3. 每个命令会创建一个新的工作区")
        print("  4. 使用 Ctrl+Tab 或侧边栏切换工作区")
        print("=" * 60)

    def show_start_commands(self, subsystem_id: str):
        """显示启动子系统命令"""
        registry = self.get_registry()
        subsystem = None

        for s in registry.get("subsystems", []):
            if s["id"] == subsystem_id:
                subsystem = s
                break

        if not subsystem:
            print(f"❌ 未找到子系统: {subsystem_id}")
            return

        subsystem_path = subsystem.get("path", f"subsystems/{subsystem_id}")
        full_path = (self.base_path / subsystem_path).resolve()

        print("=" * 60)
        print(f"📋 启动 {subsystem_id} 命令（请在 cmux 终端面板中执行）")
        print("⚠️ 注意：需要在 cmux 内部运行，不是 macOS 终端！")
        print("=" * 60)
        print()
        print(f"# 在 {subsystem_id} 工作区中运行 Claude")
        print(f'cmux new-workspace --name "{subsystem_id}" --cwd "{full_path}"')
        print()
        print("然后在新的工作区中运行: claude")
        print("=" * 60)

    def show_status(self):
        """显示状态"""
        print("\n📊 工作区配置:")
        print("-" * 50)

        registry = self.get_registry()

        for subsystem in registry.get("subsystems", []):
            status_icon = {
                "active": "🟢",
                "inactive": "⚪",
                "error": "🔴",
                "planned": "🔵"
            }.get(subsystem.get("status", "planned"), "⚪")

            agent_status = subsystem.get("agent", {}).get("status", "stopped")
            agent_icon = "▶️" if agent_status == "running" else "⏸️"

            path = subsystem.get("path", f"subsystems/{subsystem['id']}")
            print(f"  {status_icon} {subsystem['id']:<15} │ {agent_icon} {agent_status:<8} │ {path}")

        print("-" * 50)

    def show_guide(self):
        """显示使用指南"""
        base = self.base_path.resolve()
        print(f"""
╔══════════════════════════════════════════════════════════════╗
║              company-ops cmux 使用指南                        ║
╚══════════════════════════════════════════════════════════════╝

🎯 启动流程:

1. 打开 cmux 应用
2. 第一个工作区会自动打开（当前工作区）
3. 这个工作区就是 orchestrator（总调度）

📁 工作区结构:
   工作区 1 (自动): orchestrator = {base}
""")

        for i, s in enumerate(self.get_subsystems_to_init(), 2):
            path = (self.base_path / s.get("path", f"subsystems/{s['id']}")).resolve()
            print(f"   工作区 {i}: {s['id']} = {path}")

        print("""
🎬 后续步骤:

1. 在 cmux 终端面板中运行 Claude:
   claude

2. 创建其他子系统工作区（在 cmux 中执行）:
""")

        for s in self.get_subsystems_to_init():
            path = (self.base_path / s.get("path", f"subsystems/{s['id']}")).resolve()
            print(f'   cmux new-workspace --name "{s["id"]}" --cwd "{path}"')

        print("""
🔄 常用命令（在 cmux 终端中执行）:

   cmux list-workspaces              # 列出所有工作区
   cmux new-workspace --name <名称>   # 创建新工作区
   cmux focus-window --window <id>    # 切换工作区
""")

    def attach(self):
        """打开 cmux 并导航到 company-ops"""
        import subprocess
        base = self.base_path.resolve()
        subprocess.run(["open", "-a", "cmux", str(base)])
        print(f"✅ 已打开 cmux 并导航到: {base}")
        print("请在工作区中运行初始化命令")


def main():
    parser = argparse.ArgumentParser(
        description="company-ops cmux 工作区管理"
    )
    parser.add_argument(
        "--init", action="store_true",
        help="生成初始化命令"
    )
    parser.add_argument(
        "--status", action="store_true",
        help="显示工作区配置"
    )
    parser.add_argument(
        "--start", metavar="SUBSYSTEM",
        help="生成启动指定子系统的命令"
    )
    parser.add_argument(
        "--guide", action="store_true",
        help="显示使用指南"
    )
    parser.add_argument(
        "--attach", action="store_true",
        help="打开 cmux"
    )
    parser.add_argument(
        "--base-path", default=".",
        help="company-ops 基础路径"
    )

    args = parser.parse_args()

    manager = CmuxManager(args.base_path)

    if args.init:
        manager.show_init_commands()
    elif args.status:
        manager.show_status()
    elif args.start:
        manager.show_start_commands(args.start)
    elif args.guide:
        manager.show_guide()
    elif args.attach:
        manager.attach()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
company-ops 工作区状态监控

显示各子系统运行状态和 cmux 会话信息。

用法:
    python shared/tools/cmux_status.py
    python shared/tools/cmux_status.py --watch
"""

import subprocess
import json
import time
from pathlib import Path
from datetime import datetime


class StatusMonitor:
    """状态监控器"""

    def __init__(self, base_path: str = None):
        self.base_path = Path(base_path or ".")
        self.registry_path = self.base_path / "subsystems" / "_registry.json"

    def get_registry(self) -> dict:
        """获取子系统注册表"""
        if self.registry_path.exists():
            with open(self.registry_path, "r", encoding="utf-8") as f:
                return json.load(f)
        return {"subsystems": []}

    def get_subsystem_status(self, subsystem_id: str) -> dict:
        """获取单个子系统状态"""
        for s in self.get_registry().get("subsystems", []):
            if s["id"] == subsystem_id:
                return s
        return None

    def check_inbox(self, subsystem_id: str) -> list:
        """检查收件箱"""
        inbox_path = self.base_path / "subsystems" / subsystem_id / "inbox"
        messages = []
        if inbox_path.exists():
            for msg_file in inbox_path.glob("*.json"):
                try:
                    with open(msg_file, "r", encoding="utf-8") as f:
                        messages.append(json.load(f))
                except Exception:
                    pass
        return messages

    def check_outbox(self, subsystem_id: str) -> list:
        """检查发件箱"""
        outbox_path = self.base_path / "subsystems" / subsystem_id / "outbox"
        messages = []
        if outbox_path.exists():
            for msg_file in outbox_path.glob("*.json"):
                try:
                    with open(msg_file, "r", encoding="utf-8") as f:
                        messages.append(json.load(f))
                except Exception:
                    pass
        return messages

    def get_all_status(self) -> dict:
        """获取所有子系统状态"""
        registry = self.get_registry()
        result = {
            "timestamp": datetime.now().isoformat(),
            "subsystems": []
        }

        for s in registry.get("subsystems", []):
            status = self._calculate_status(s)
            inbox = self.check_inbox(s["id"])
            outbox = self.check_outbox(s["id"])
            local_graph = self._check_local_graph(s["id"])

            result["subsystems"].append({
                "id": s["id"],
                "name": s.get("name", registry.get("name", s["name"]),
                "status": status,
                "inbox": inbox,
                "outbox": outbox,
                "local_graph": local_graph,
                "last_activity": s.get("last_activity"),
                "pending_tasks": self._get_pending_tasks(s)
            })

            if s["status"] == "active":
                # 检查收件箱
                inbox_count = len(inbox)
                if inbox_count > 0:
                    result["alerts"].append(
                        f"📥 {s['name']}: {inbox_count} 尸消息待处理"
                    )
                # 检查发件箱
                outbox = self.check_outbox(s["id"])
                outbox_count = len(outbox)
                if outbox_count > 0:
                    result["alerts"].append(
                        f"📤 {s['name']}: {outbox_count} 个待发送消息"
                    )

                # 检查本地图谱
                try:
                    graph_path = self.base_path / "subsystems" / s["id"] / "local-graph.json"
                    if graph_path.exists():
                    with open(graph_path, "r", encoding="utf-8") as f:
                        graph = json.load(f)
                        entities = graph.get("entities", [])
                        relations = graph.get("relations", [])
                        stale_count = sum(1 for e in graph.get("entities", []) if e.get("status") == "stale")
                        result["warnings"].append(
                            f"⚠️ {s['name']}: {stale_count} 个实体可能过期"
                        )
            return result

    def show_status(self):
        """显示所有子系统状态"""
        registry = self.get_registry()

        print("\n" + "=" * 60 * "=" * " company-ops 工作区状态 " + "=" * 60 * "=")
        print(f"{'ID': <30} | {'名称': <20} | {'状态': <15} | {'收件箱': <10>} | {'发件箱': <5} | {'待处理': <3> | {'实体': <50} | {'关系': <20} | {'过期': <5}")
            print("-" * 100 * "="")
            print(f"{'ID': <30} | {'名称': <20} | {'状态': <15} | {'收件箱': <10>} | {'发件箱': <5>}")
        print(f"\n{'总活跃子系统': {len(active_subsystems)}")
        for s in active_subsystems:
            print(f"  - {s['id']}")
            print(f"  - {s['name']}")
            print(f"  - 状态: {s['status']}")
            print(f"  - 收件箱: {len(inbox)} 待处理消息")
            print(f"  - 发件箱: {len(outbox)} 待发送消息")
            print(f"  - 本地图: {len(entities)} 实体, {len(relations)} 关系")
            print(f"  - 上次活动: {s['last_activity']}")
        print("\n" + "=" * 60 * "=")
        print("=" * 60 * "=")

        print(f"\n💡 建议:")
        print("  - 清理过期的收件箱消息")
        print("  - 检查发件箱是否有积压的消息")
        print("  - 检查本地图谱是否有过期实体")
        print("  - 考虑使用 watch 模式监控变化")
        print("  - 添加更多子系统以扩展系统")
        print("  - 定期运行此脚本以监控系统健康")
        print("\n📖 使用说明:")
        print("python shared/tools/cmux_status.py --watch")
        print("python shared/tools/cmux_status.py --init  # 初始化工作区")
        print("python shared/tools/cmux_status.py --start 财务  # 启动财务子系统")
        print("python shared/tools/cmux_status.py --stop 财务  # 停止财务子系统")
        print("\n更多信息请参考: docs/deployment/cmux-workspace-setup.md")
        """)

    def show_help(self):
        """显示帮助信息"""
        print("""
用法:
    cmux_init.py --init        初始化所有工作区
    cmux_init.py --status       查看状态
    cmux_init.py --start 财务  启动特定子系统
    cmux_init.py --stop 财务    停止特定子系统

    cmux_status.py              查看所有子系统状态
    cmux_status.py --watch          持续监控状态变化
""")
        print("=" * 60)


if __name__ == "__main__":
    main()

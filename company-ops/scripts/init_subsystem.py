#!/usr/bin/env python3
"""
子系统初始化脚本

用法:
    python init_subsystem.py <子系统名称> [--type function|product|tool]

示例:
    python init_subsystem.py 财务 --type function
    python init_subsystem.py 产品研发 --type product
"""

import os
import sys
import json
from datetime import datetime
from pathlib import Path


# 子系统类型配置
SUBSYSTEM_TYPES = {
    "function": {
        "description": "职能部门",
        "default_dirs": ["inbox", "outbox", "state", "data", "scripts", "libs", "docs", "workspace"],
        "default_files": ["SPEC.md", "CONTRACT.yaml", "CAPABILITIES.yaml", "local-graph.json"]
    },
    "product": {
        "description": "产品线",
        "default_dirs": ["inbox", "outbox", "state", "src", "tests", "docs", "scripts", "libs", "workspace"],
        "default_files": ["SPEC.md", "CONTRACT.yaml", "CAPABILITIES.yaml", "local-graph.json"]
    },
    "tool": {
        "description": "工具系统",
        "default_dirs": ["inbox", "outbox", "state", "src", "bin", "config", "scripts", "libs", "docs"],
        "default_files": ["SPEC.md", "CONTRACT.yaml", "CAPABILITIES.yaml", "local-graph.json"]
    }
}


def create_subsystem(name: str, subsystem_type: str = "function", base_path: str = None):
    """创建子系统目录结构"""

    if base_path is None:
        # 默认在 subsystems/ 下创建
        base_path = Path(__file__).parent.parent / "subsystems"
    else:
        base_path = Path(base_path)

    subsystem_path = base_path / name
    config = SUBSYSTEM_TYPES.get(subsystem_type, SUBSYSTEM_TYPES["function"])

    print(f"Creating subsystem: {name} (type: {subsystem_type})")
    print(f"Path: {subsystem_path}")
    print("-" * 50)

    # 创建目录结构
    for dir_name in config["default_dirs"]:
        dir_path = subsystem_path / dir_name
        dir_path.mkdir(parents=True, exist_ok=True)
        # 创建 .gitkeep 文件
        gitkeep = dir_path / ".gitkeep"
        gitkeep.touch()
        print(f"  + {dir_name}/")

    # 创建核心文件
    created_files = []

    # 1. CLAUDE.md - Agent 运行规范
    claude_md = subsystem_path / "CLAUDE.md"
    claude_md.write_text(f"""# {name} 子系统 Agent

## 身份

你是 {name} 子系统 Agent，负责{config['description']}相关事务。你的工作目录是 `subsystems/{name}/`。

## 文件边界约束

**你只能访问以下目录：**

```
subsystems/{name}/
├── CLAUDE.md          ← 你正在阅读的规范
├── SPEC.md             ← 完整规范文档
├── CONTRACT.yaml       ← 交互契约
├── CAPABILITIES.yaml   ← 能力定义
├── local-graph.json   ← 本地知识图谱
├── inbox/              ← 接收消息
├── outbox/             ← 发送消息
├── state/              ← 状态跟踪
│   ├── goals.md
│   ├── status.md
│   └── metrics.yaml
├── data/               ← 数据存储
├── scripts/            ← 工作脚本
├── libs/               ← 本地库/依赖
├── docs/               ← 工作文档
└── workspace/          ← 工作空间
```

**绝对禁止访问：**
- `../` (父目录除 inbox/outbox 外)
- `../../company-ops/` (Orchestrator 区域)
- `../*/` (其他子系统，除非通过 inbox/outbox 正式通信)
- 任何系统敏感文件

## 核心职责

请参考 SPEC.md 获取完整的职责定义。

## 与其他 Agent 交互

### 与 Orchestrator 通信

**接收任务：**
```bash
ls inbox/
cat inbox/msg_*.json
```

**汇报结果：**
```bash
filename="reply_$(date +%Y%m%d_%H%M%S).json"
cat > "outbox/$filename" << 'EOF'
{{
  "task_id": "xxx",
  "status": "completed",
  "result": "..."
}}
EOF
```

### 与其他子系统通信

通过 inbox/outbox 进行跨子系统通信：
```bash
cat > "../其他子系统/inbox/req_xxx.json" << 'EOF'
{{
  "type": "service_request",
  "content": "..."
}}
EOF
```

## 决策权限

请参考 SPEC.md 中的决策权限矩阵。

## 数据管理

- 敏感数据必须安全存储
- 禁止将子系统数据传到外部
- 保持数据隔离

## 状态更新

完成重要任务后更新 state/status.md：
```bash
cat > state/status.md << 'EOF'
# {name} 状态报告

## 当前状态
**整体状态：** 🟢 运行中
...
EOF
```

## 相关文档

- SPEC.md - 完整规范
- CONTRACT.yaml - 交互协议
- CAPABILITIES.yaml - 能力定义
""")
    created_files.append("CLAUDE.md")
    print(f"  + CLAUDE.md")

    # 2. SPEC.md - 规范文档
    spec_md = subsystem_path / "SPEC.md"
    spec_md.write_text(f"""# {name} 规范文档

## 基本信息

| 属性 | 值 |
|------|-----|
| 子系统ID | `{name}` |
| 名称 | {name} |
| 类型 | {subsystem_type} ({config['description']}) |
| 创建日期 | {datetime.now().strftime('%Y-%m-%d')} |
| 状态 | initializing |

## 概述

{config['description']}子系统，负责...

## 职责范围

### 文件边界

```
subsystems/{name}/
├── CLAUDE.md
├── SPEC.md
├── CONTRACT.yaml
├── CAPABILITIES.yaml
├── local-graph.json
├── inbox/
├── outbox/
├── state/
│   ├── goals.md
│   ├── status.md
│   └── metrics.yaml
├── data/
├── scripts/
├── libs/
├── docs/
└── workspace/
```

### 核心职责

| ID | 职责 | 描述 | 优先级 |
|----|------|------|--------|
| TBD | - | 待定义 | - |

### 边界约束

**属于本子系统范围：**
- 待定义

**不属于本子系统范围：**
- 待定义

## 交互契约

请参考 CONTRACT.yaml

## 能力定义

请参考 CAPABILITIES.yaml

## 更新历史

| 日期 | 版本 | 变更说明 |
|------|------|----------|
| {datetime.now().strftime('%Y-%m-%d')} | 0.1.0 | 初始创建 |

---
*创建时间: {datetime.now().strftime('%Y-%m-%d')}*
""")
    created_files.append("SPEC.md")
    print(f"  + SPEC.md")

    # 3. CONTRACT.yaml - 交互契约
    contract_yaml = subsystem_path / "CONTRACT.yaml"
    contract_yaml.write_text(f"""# CONTRACT.yaml - {name}子系统交互契约

version: "0.1.0"
subsystem_id: {name}
name: {name}
last_updated: "{datetime.now().strftime('%Y-%m-%d')}"
status: initializing

# 交互协议
interaction_protocols:
  request:
    format: intent-based
    description: |
      接收基于意图的请求，支持自然语言描述。
      请求通过 inbox/ 目录以文件形式接收。
    schema:
      type: object
      required: [intent, requestor, deadline]
      properties:
        intent:
          type: string
          description: 意图描述
        requestor:
          type: string
          description: 请求方子系统ID
        payload:
          type: object
          description: 请求参数
        deadline:
          type: string
          format: date-time

  response:
    format: structured
    description: |
      返回结构化的执行结果，通过 outbox/ 目录发送。

# 服务定义
services:
  provided: []
  consumed: []

# 通信通道
channels:
  inbox: inbox/
  outbox: outbox/
""")
    created_files.append("CONTRACT.yaml")
    print(f"  + CONTRACT.yaml")

    # 4. CAPABILITIES.yaml - 能力定义
    capabilities_yaml = subsystem_path / "CAPABILITIES.yaml"
    capabilities_yaml.write_text(f"""# CAPABILITIES.yaml - {name}子系统能力定义

version: "0.1.0"
subsystem_id: {name}
last_updated: "{datetime.now().strftime('%Y-%m-%d')}"

capabilities: []

constraints:
  - id: CONSTR-001
    type: file_boundary
    description: 只能在 subsystem/{name}/ 目录下操作
  - id: CONSTR-002
    type: data_isolation
    description: 禁止访问其他子系统数据
""")
    created_files.append("CAPABILITIES.yaml")
    print(f"  + CAPABILITIES.yaml")

    # 5. local-graph.json - 本地知识图谱
    local_graph = {
        "metadata": {
            "version": "0.1.0",
            "subsystem": name,
            "created_at": datetime.now().isoformat()
        },
        "entities": [],
        "relations": []
    }
    with open(subsystem_path / "local-graph.json", "w", encoding="utf-8") as f:
        json.dump(local_graph, f, ensure_ascii=False, indent=2)
    created_files.append("local-graph.json")
    print(f"  + local-graph.json")

    # 6. state/ 初始文件
    goals_md = subsystem_path / "state" / "goals.md"
    goals_md.write_text(f"""# {name} 目标

## 长期目标

- [ ] 完成子系统初始化

## 当前目标

- 完善 SPEC.md 职责定义
- 定义核心能力
- 配置交互契约
""")
    print(f"  + state/goals.md")

    status_md = subsystem_path / "state" / "status.md"
    status_md.write_text(f"""# {name} 状态报告

## 当前状态

**整体状态：** 🟡 初始化中

**活跃任务：** 0
**阻塞问题：** 0
**待审核决策：** 0

## 本周进展

### 已完成
- [日期] 子系统目录结构创建
- [日期] 基础规范文档创建

### 进行中
- 完善 SPEC.md

### 待开始
- 定义核心能力
- 配置交互契约

## 风险与阻塞

暂无

## 下一步计划

1. 完善 SPEC.md 职责定义
2. 定义核心能力
3. 配置交互契约

---
*报告生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M')}*
""")
    print(f"  + state/status.md")

    metrics_yaml = subsystem_path / "state" / "metrics.yaml"
    metrics_yaml.write_text(f"""# {name} 指标

metrics:
  - name: tasks_completed
    type: counter
    description: 完成的任务数量

  - name: tasks_blocked
    type: gauge
    description: 阻塞的任务数量

  - name: avg_response_time
    type: gauge
    description: 平均响应时间(小时)
""")
    print(f"  + state/metrics.yaml")

    print("-" * 50)
    print(f"Created {len(created_files)} files")
    print(f"Done! Subsystem '{name}' created at: {subsystem_path}")

    # 返回创建的子系统路径
    return str(subsystem_path)


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    name = sys.argv[1]
    subsystem_type = "function"

    # 解析参数
    for arg in sys.argv[2:]:
        if arg.startswith("--type="):
            subsystem_type = arg.split("=")[1]

    create_subsystem(name, subsystem_type)


if __name__ == "__main__":
    main()

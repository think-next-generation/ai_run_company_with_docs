#!/usr/bin/env python3
"""
Subsystem Initialization Script for company-ops.
Creates a new subsystem with all required documents.
"""

import json
import yaml
import sys
import argparse
from pathlib import Path
from datetime import datetime
from typing import Optional


# Subsystem type templates
SUBSYSTEM_TYPES = {
    'function': {
        'description': 'Functional department (财务, 法务, HR, etc.)',
        'default_capabilities': ['planning', 'execution', 'reporting'],
    },
    'product': {
        'description': 'Product line or project',
        'default_capabilities': ['development', 'delivery', 'support'],
    },
    'operation': {
        'description': 'Operational function (marketing, sales, etc.)',
        'default_capabilities': ['execution', 'monitoring', 'optimization'],
    },
    'custom': {
        'description': 'Custom subsystem type',
        'default_capabilities': [],
    }
}


def create_spec_md(subsystem_path: Path, subsystem_id: str, name: str, description: str) -> None:
    """Create SPEC.md for the subsystem."""
    content = f"""# {name} 规范文档

## 基本信息

| 属性 | 值 |
|------|-----|
| 子系统ID | `{subsystem_id}` |
| 名称 | {name} |
| 类型 | [待填写] |
| 创建日期 | {datetime.now().strftime('%Y-%m-%d')} |
| 状态 | planned |

## 概述

{description}

## 职责范围

本子系统负责以下文件范围：

```
{subsystem_path}/
├── SPEC.md           # 本规范文档
├── CONTRACT.yaml     # 交互契约
├── CAPABILITIES.yaml # 能力定义
├── local-graph.json  # 本地知识图谱
└── state/            # 状态跟踪
    ├── goals.md
    ├── status.md
    └── metrics.yaml
```

### 核心职责

1. [待定义：核心职责1]
2. [待定义：核心职责2]
3. [待定义：核心职责3]

### 边界约束

**属于本子系统范围：**
- [待定义]

**不属于本子系统范围：**
- [待定义]

## Agent 团队配置

本子系统运行时，将根据任务需要组建多Agent协作团队：

| 角色 | 职责 | 触发条件 |
|------|------|----------|
| [待定义] | [待定义] | [待定义] |

## 决策权限

| 决策类型 | 权限级别 | 说明 |
|----------|----------|------|
| 日常执行 | 自主 | 无需人工确认 |
| [待定义] | [待定义] | [待定义] |

## 依赖关系

### 提供的服务

本子系统向其他子系统提供以下服务：

- [待定义]

### 消费的服务

本子系统依赖以下外部服务：

- [待定义]

## 更新历史

| 日期 | 版本 | 变更说明 |
|------|------|----------|
| {datetime.now().strftime('%Y-%m-%d')} | 0.1.0 | 初始创建 |

---
*本文档由 init_subsystem.py 自动生成，请根据实际情况完善内容。*
"""
    (subsystem_path / 'SPEC.md').write_text(content, encoding='utf-8')


def create_contract_yaml(subsystem_path: Path, subsystem_id: str, name: str) -> None:
    """Create CONTRACT.yaml for the subsystem."""
    content = {
        'version': '0.1.0',
        'subsystem_id': subsystem_id,
        'name': name,
        'last_updated': datetime.now().strftime('%Y-%m-%d'),
        'status': 'planned',
        'interaction_protocols': {
            'request': {
                'format': 'intent-based',
                'description': '接收基于意图的请求，通过协商引擎处理'
            },
            'response': {
                'format': 'structured',
                'description': '返回结构化的执行结果或协商响应'
            },
            'notification': {
                'format': 'event-based',
                'description': '通过事件通知机制广播状态变更'
            }
        },
        'provides': [
            # 待填写：提供的服务
        ],
        'consumes': [
            # 待填写：消费的服务
        ],
        'constraints': {
            'working_hours': 'flexible',
            'max_concurrent_tasks': 3,
            'requires_human_approval': [],
            'autonomy_level': 'supervised'
        },
        'communication': {
            'inbox': f'subsystems/{subsystem_id}/inbox/',
            'outbox': f'subsystems/{subsystem_id}/outbox/',
            'review_queue': f'human/reviews/{subsystem_id}/'
        }
    }

    with open(subsystem_path / 'CONTRACT.yaml', 'w', encoding='utf-8') as f:
        yaml.dump(content, f, default_flow_style=False, sort_keys=False, allow_unicode=True)


def create_capabilities_yaml(
    subsystem_path: Path,
    subsystem_id: str,
    capabilities: list
) -> None:
    """Create CAPABILITIES.yaml for the subsystem."""
    caps_list = []
    for i, cap in enumerate(capabilities, 1):
        caps_list.append({
            'id': f'CAP-{i:03d}',
            'name': cap,
            'description': f'[待定义：{cap}能力的详细描述]',
            'status': 'planned',
            'skills': [],
            'tools': [],
            'inputs': [],
            'outputs': [],
            'quality_metrics': []
        })

    content = {
        'version': '0.1.0',
        'subsystem_id': subsystem_id,
        'last_updated': datetime.now().strftime('%Y-%m-%d'),
        'capabilities': caps_list,
        'current_maturity': {cap['id']: 0 for cap in caps_list}
    }

    with open(subsystem_path / 'CAPABILITIES.yaml', 'w', encoding='utf-8') as f:
        yaml.dump(content, f, default_flow_style=False, sort_keys=False, allow_unicode=True)


def create_local_graph(subsystem_path: Path, subsystem_id: str, name: str) -> None:
    """Create local-graph.json for the subsystem."""
    content = {
        'metadata': {
            'version': '0.1.0',
            'updated_at': datetime.now().isoformat(),
            'subsystem_id': subsystem_id,
            'description': f'{name} 本地知识图谱'
        },
        'entities': [
            {
                'id': f'subsystem.{subsystem_id}',
                'type': 'subsystem',
                'name': name,
                'description': f'{name} 子系统',
                'created_at': datetime.now().isoformat(),
                'tags': ['core']
            }
        ],
        'relations': [],
        'views': {
            'capability': [],
            'goal': [],
            'dependency': []
        }
    }

    with open(subsystem_path / 'local-graph.json', 'w', encoding='utf-8') as f:
        json.dump(content, f, indent=2, ensure_ascii=False)


def create_state_files(subsystem_path: Path, subsystem_id: str) -> None:
    """Create state tracking files."""
    state_dir = subsystem_path / 'state'
    state_dir.mkdir(exist_ok=True)

    # goals.md
    goals_content = f"""# {subsystem_id} 目标跟踪

## 当前周期目标

| ID | 目标 | 优先级 | 状态 | 截止日期 |
|----|------|--------|------|----------|
| G-001 | 完成子系统初始化和规范定义 | high | in_progress | {datetime.now().strftime('%Y-%m-%d')} |

## 目标分解

### G-001: 完成子系统初始化和规范定义

**背景：** 新创建的子系统，需要完成基础配置

**关键结果：**
- [ ] 完善SPEC.md规范文档
- [ ] 定义CAPABILITIES.yaml能力清单
- [ ] 配置CONTRACT.yaml交互契约
- [ ] 建立初始知识图谱

**依赖：** 无

---
*最后更新：{datetime.now().strftime('%Y-%m-%d %H:%M')}*
"""
    (state_dir / 'goals.md').write_text(goals_content, encoding='utf-8')

    # status.md
    status_content = f"""# {subsystem_id} 状态报告

## 当前状态

**整体状态：** 🟡 初始化中

**活跃任务：** 1
**阻塞问题：** 0
**待审核决策：** 0

## 本周进展

### 已完成
- [日期] 子系统初始化

### 进行中
- 规范文档完善

### 待开始
- 能力定义
- 交互契约配置

## 风险与阻塞

暂无

## 下一步计划

1. 完善SPEC.md
2. 定义核心能力
3. 配置交互契约

---
*报告生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M')}*
"""
    (state_dir / 'status.md').write_text(status_content, encoding='utf-8')

    # metrics.yaml
    metrics_content = {
        'subsystem_id': subsystem_id,
        'period': datetime.now().strftime('%Y-%m'),
        'metrics': {
            'tasks_completed': 0,
            'tasks_in_progress': 1,
            'tasks_blocked': 0,
            'avg_completion_time_hours': 0,
            'quality_score': 0,
            'human_interventions': 0
        },
        'trends': {
            'weekly_completion_rate': [],
            'quality_trend': []
        }
    }

    with open(state_dir / 'metrics.yaml', 'w', encoding='utf-8') as f:
        yaml.dump(metrics_content, f, default_flow_style=False, sort_keys=False, allow_unicode=True)


def create_inbox_outbox(subsystem_path: Path) -> None:
    """Create inbox and outbox directories."""
    (subsystem_path / 'inbox').mkdir(exist_ok=True)
    (subsystem_path / 'inbox' / '.gitkeep').touch()

    (subsystem_path / 'outbox').mkdir(exist_ok=True)
    (subsystem_path / 'outbox' / '.gitkeep').touch()


def update_registry(base_path: Path, subsystem_id: str, name: str, subsystem_type: str) -> None:
    """Update or create the subsystem registry."""
    registry_path = base_path / 'subsystems' / '_registry.json'

    if registry_path.exists():
        with open(registry_path, 'r', encoding='utf-8') as f:
            registry = json.load(f)
    else:
        registry = {
            'version': '0.1.0',
            'updated_at': datetime.now().isoformat(),
            'subsystems': []
        }

    # Check if subsystem already exists
    existing = next((s for s in registry['subsystems'] if s['id'] == subsystem_id), None)
    if existing:
        print(f"⚠️  Subsystem {subsystem_id} already exists in registry, updating...")
        existing.update({
            'name': name,
            'status': 'planned',
            'last_activity': datetime.now().isoformat()
        })
    else:
        registry['subsystems'].append({
            'id': subsystem_id,
            'name': name,
            'description': f'{name} 子系统',
            'path': f'subsystems/{subsystem_id}',
            'status': 'planned',
            'version': '0.1.0',
            'type': subsystem_type,
            'created_at': datetime.now().isoformat(),
            'last_activity': datetime.now().isoformat(),
            'agent': {
                'type': 'claude-code',
                'status': 'stopped'
            },
            'capabilities': [],
            'priority': 'normal'
        })

    registry['updated_at'] = datetime.now().isoformat()

    with open(registry_path, 'w', encoding='utf-8') as f:
        json.dump(registry, f, indent=2, ensure_ascii=False)


def init_subsystem(
    base_path: str,
    subsystem_id: str,
    name: str,
    subsystem_type: str,
    description: str
) -> Path:
    """Initialize a new subsystem."""

    # Validate subsystem_id format
    if not subsystem_id.replace('/', '').replace('-', '').replace('_', '').isalnum():
        raise ValueError(f"Invalid subsystem_id: {subsystem_id}")

    # Determine path
    subsystem_path = Path(base_path) / 'subsystems' / subsystem_id

    if subsystem_path.exists():
        raise FileExistsError(f"Subsystem directory already exists: {subsystem_path}")

    # Create directory structure
    subsystem_path.mkdir(parents=True, exist_ok=True)

    # Get default capabilities based on type
    type_config = SUBSYSTEM_TYPES.get(subsystem_type, SUBSYSTEM_TYPES['custom'])
    capabilities = type_config['default_capabilities']

    # Create all files
    create_spec_md(subsystem_path, subsystem_id, name, description)
    create_contract_yaml(subsystem_path, subsystem_id, name)
    create_capabilities_yaml(subsystem_path, subsystem_id, capabilities)
    create_local_graph(subsystem_path, subsystem_id, name)
    create_state_files(subsystem_path, subsystem_id)
    create_inbox_outbox(subsystem_path)

    # Update registry
    update_registry(Path(base_path), subsystem_id, name, subsystem_type)

    return subsystem_path


def main():
    parser = argparse.ArgumentParser(
        description='Initialize a new subsystem in company-ops',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Create a functional department
  python init_subsystem.py 财务 --name "财务管理" --type function

  # Create a legal department
  python init_subsystem.py 法务 --name "法务合规" --type function

  # Create a product subsystem
  python init_subsystem.py products/example-product --name "示例产品" --type product

  # Create with custom description
  python init_subsystem.py marketing --name "市场营销" --type operation \\
    --description "负责公司品牌推广和市场拓展"
        """
    )

    parser.add_argument(
        'subsystem_id',
        help='Subsystem ID (e.g., 财务, 法务, products/my-product)'
    )
    parser.add_argument(
        '--name', '-n',
        required=True,
        help='Display name for the subsystem'
    )
    parser.add_argument(
        '--type', '-t',
        choices=list(SUBSYSTEM_TYPES.keys()),
        default='function',
        help='Type of subsystem (default: function)'
    )
    parser.add_argument(
        '--description', '-d',
        default='待填写描述',
        help='Description of the subsystem'
    )
    parser.add_argument(
        '--base', '-b',
        default='.',
        help='Base path of company-ops (default: current directory)'
    )

    args = parser.parse_args()

    try:
        subsystem_path = init_subsystem(
            base_path=args.base,
            subsystem_id=args.subsystem_id,
            name=args.name,
            subsystem_type=args.type,
            description=args.description
        )

        print(f"\n✅ 子系统初始化成功！\n")
        print(f"📁 路径: {subsystem_path}")
        print(f"\n📋 创建的文件:")
        print(f"   ├── SPEC.md           # 规范文档")
        print(f"   ├── CONTRACT.yaml     # 交互契约")
        print(f"   ├── CAPABILITIES.yaml # 能力定义")
        print(f"   ├── local-graph.json  # 本地知识图谱")
        print(f"   ├── inbox/            # 接收队列")
        print(f"   ├── outbox/           # 发送队列")
        print(f"   └── state/            # 状态跟踪")
        print(f"       ├── goals.md")
        print(f"       ├── status.md")
        print(f"       └── metrics.yaml")
        print(f"\n📝 下一步:")
        print(f"   1. 完善 SPEC.md 定义职责范围和边界")
        print(f"   2. 配置 CAPABILITIES.yaml 定义能力")
        print(f"   3. 设置 CONTRACT.yaml 交互契约")
        print(f"   4. 在 cmux 中为该子系统创建独立工作区")
        print()

    except FileExistsError as e:
        print(f"❌ 错误: {e}", file=sys.stderr)
        sys.exit(1)
    except ValueError as e:
        print(f"❌ 错误: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"❌ 初始化失败: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()

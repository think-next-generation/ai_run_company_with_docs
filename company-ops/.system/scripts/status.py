#!/usr/bin/env python3
"""
Company-Ops 系统状态检查脚本
用于快速查看系统运行状态
"""

import json
import sys
from pathlib import Path
from datetime import datetime


def get_base_path():
    """获取 company-ops 根目录"""
    script_path = Path(__file__).resolve()
    return script_path.parent.parent.parent


def print_header(title):
    """打印标题"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print('='*60)


def print_status(status, message):
    """打印状态"""
    icons = {
        'ok': '✅',
        'warn': '⚠️ ',
        'error': '❌',
        'info': 'ℹ️ '
    }
    icon = icons.get(status, '•')
    print(f"  {icon} {message}")


def check_phase0(base_path):
    """检查 Phase 0 完成情况"""
    print_header("Phase 0: 文档基础")

    required_files = [
        'CHARTER.md',
        'CONSTITUTION.yaml',
        'global-graph.json',
        'shared/schemas/constitution.schema.json',
        'shared/tools/validate_schema.py',
    ]

    required_dirs = [
        '.system',
        'subsystems',
        'shared',
        'human',
    ]

    all_ok = True

    for f in required_files:
        path = base_path / f
        if path.exists():
            print_status('ok', f"文件存在: {f}")
        else:
            print_status('error', f"文件缺失: {f}")
            all_ok = False

    for d in required_dirs:
        path = base_path / d
        if path.is_dir():
            print_status('ok', f"目录存在: {d}/")
        else:
            print_status('error', f"目录缺失: {d}/")
            all_ok = False

    return all_ok


def check_subsystems(base_path):
    """检查子系统状态"""
    print_header("子系统状态")

    registry_path = base_path / 'subsystems' / '_registry.json'

    if not registry_path.exists():
        print_status('warn', "子系统注册表不存在")
        return False

    with open(registry_path, 'r', encoding='utf-8') as f:
        registry = json.load(f)

    subsystems = registry.get('subsystems', [])
    if not subsystems:
        print_status('info', "暂无注册的子系统")
        return True

    status_icons = {
        'active': '🟢',
        'planned': '🟡',
        'inactive': '⚪',
        'error': '🔴'
    }

    all_ok = True
    for sub in subsystems:
        sub_id = sub.get('id', 'unknown')
        sub_name = sub.get('name', sub_id)
        status = sub.get('status', 'unknown')
        icon = status_icons.get(status, '❓')

        # 检查子系统目录
        sub_dir = base_path / 'subsystems' / sub_id
        if not sub_dir.exists():
            print_status('error', f"{icon} {sub_name} - 目录不存在")
            all_ok = False
            continue

        # 检查必需文件
        required = ['SPEC.md', 'CONTRACT.yaml', 'CAPABILITIES.yaml', 'local-graph.json']
        missing = [f for f in required if not (sub_dir / f).exists()]

        if missing:
            print_status('warn', f"{icon} {sub_name} ({status}) - 缺失: {', '.join(missing)}")
        else:
            print_status('ok', f"{icon} {sub_name} ({status}) - 完整")

    print(f"\n  总计: {len(subsystems)} 个子系统")

    return all_ok


def check_graph_lib(base_path):
    """检查知识图谱库"""
    print_header("知识图谱库")

    lib_path = base_path / '.system' / 'lib' / 'graph'

    required_modules = [
        '__init__.py',
        'parser.py',
        'index.py',
        'query.py',
        'update.py',
        'cache.py',
    ]

    all_ok = True
    for module in required_modules:
        path = lib_path / module
        if path.exists():
            print_status('ok', f"模块存在: {module}")
        else:
            print_status('error', f"模块缺失: {module}")
            all_ok = False

    return all_ok


def check_global_graph(base_path):
    """检查全局知识图谱"""
    print_header("全局知识图谱")

    graph_path = base_path / 'global-graph.json'

    if not graph_path.exists():
        print_status('error', "全局图谱不存在")
        return False

    try:
        with open(graph_path, 'r', encoding='utf-8') as f:
            graph = json.load(f)
    except Exception as e:
        print_status('error', f"图谱解析失败: {e}")
        return False

    metadata = graph.get('metadata', {})
    entities = graph.get('entities', [])
    relations = graph.get('relations', [])
    views = graph.get('views', {})

    print_status('ok', f"版本: {metadata.get('version', 'unknown')}")
    print_status('ok', f"实体数: {len(entities)}")
    print_status('ok', f"关系数: {len(relations)}")
    print_status('ok', f"视图数: {len(views)}")
    print_status('info', f"更新时间: {metadata.get('updated_at', 'unknown')}")

    # 统计实体类型
    entity_types = {}
    for e in entities:
        et = e.get('type', 'unknown')
        entity_types[et] = entity_types.get(et, 0) + 1

    print(f"\n  实体类型分布:")
    for et, count in sorted(entity_types.items(), key=lambda x: -x[1]):
        print(f"    - {et}: {count}")

    return True


def main():
    """主函数"""
    print("\n📊 Company-Ops 系统状态检查")
    print(f"   检查时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    base_path = get_base_path()
    print(f"   根目录: {base_path}")

    results = {
        'Phase 0': check_phase0(base_path),
        '子系统': check_subsystems(base_path),
        '图谱库': check_graph_lib(base_path),
        '全局图谱': check_global_graph(base_path),
    }

    print_header("总体状态")

    all_ok = all(results.values())
    for name, ok in results.items():
        status = 'ok' if ok else 'error'
        print_status(status, f"{name}: {'通过' if ok else '有问题'}")

    print("")

    if all_ok:
        print("✅ 系统状态良好！")
        sys.exit(0)
    else:
        print("❌ 系统存在问题，请检查上述错误项")
        sys.exit(1)


if __name__ == '__main__':
    main()

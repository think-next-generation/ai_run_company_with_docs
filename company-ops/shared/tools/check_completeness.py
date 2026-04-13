#!/usr/bin/env python3
"""
Completeness Checker for company-ops document system.
Checks that all required files and fields are present.
"""

import json
import yaml
import sys
from pathlib import Path
from typing import Dict, List, Tuple

# Required files by phase
PHASE_REQUIREMENTS = {
    0: {
        'files': [
            'CHARTER.md',
            'CONSTITUTION.yaml',
            'global-graph.json',
            'shared/templates/SPEC.md',
            'shared/templates/CONTRACT.yaml',
            'shared/templates/CAPABILITIES.yaml',
            'shared/templates/state/goals.md',
            'shared/templates/state/status.md',
            'shared/templates/state/metrics.yaml',
            'shared/schemas/constitution.schema.json',
            'shared/schemas/contract.schema.json',
            'shared/schemas/capabilities.schema.json',
            'shared/schemas/registry.schema.json',
            'shared/schemas/graph.schema.json',
        ],
        'directories': [
            '.system',
            '.system/config',
            '.system/lib',
            'subsystems',
            'shared',
            'shared/patterns',
            'shared/templates',
            'shared/schemas',
            'shared/tools',
            'human',
            'human/inbox',
            'human/reviews',
            'human/feedback',
        ]
    },
    1: {
        'subsystem_files': [
            'SPEC.md',
            'CONTRACT.yaml',
            'CAPABILITIES.yaml',
            'local-graph.json',
            'state/goals.md',
            'state/status.md',
            'state/metrics.yaml',
        ],
        'required_subsystems': ['tech', 'product', 'operations'],
        'registry_required': True,
    },
    2: {
        'lib_modules': [
            '.system/lib/graph/__init__.py',
            '.system/lib/graph/parser.py',
            '.system/lib/graph/index.py',
            '.system/lib/graph/query.py',
            '.system/lib/graph/update.py',
            '.system/lib/graph/cache.py',
        ]
    },
    3: {
        'lib_modules': [
            '.system/lib/negotiation/__init__.py',
            '.system/lib/negotiation/intent/classifier.py',
            '.system/lib/negotiation/intent/extractor.py',
            '.system/lib/negotiation/matching/matcher.py',
            '.system/lib/negotiation/evaluation/feasibility.py',
            '.system/lib/negotiation/response/generator.py',
            '.system/lib/negotiation/orchestration/orchestrator.py',
        ]
    }
}

class CompletenessChecker:
    """Checks completeness of the company-ops document system."""

    def __init__(self, base_path: str = '.'):
        self.base_path = Path(base_path)
        self.issues: List[Dict] = []
        self.warnings: List[Dict] = []

    def check_phase(self, phase: int) -> Tuple[bool, List[Dict], List[Dict]]:
        """
        Check completeness for a specific phase.

        Returns:
            Tuple of (is_complete, issues, warnings)
        """
        self.issues = []
        self.warnings = []

        if phase not in PHASE_REQUIREMENTS:
            print(f"No requirements defined for phase {phase}")
            return True, [], []

        requirements = PHASE_REQUIREMENTS[phase]

        # Check directories
        if 'directories' in requirements:
            for dir_path in requirements['directories']:
                full_path = self.base_path / dir_path
                if not full_path.exists():
                    self.issues.append({
                        'type': 'missing_directory',
                        'path': dir_path,
                        'message': f"Missing directory: {dir_path}"
                    })

        # Check files
        if 'files' in requirements:
            for file_path in requirements['files']:
                full_path = self.base_path / file_path
                if not full_path.exists():
                    self.issues.append({
                        'type': 'missing_file',
                        'path': file_path,
                        'message': f"Missing file: {file_path}"
                    })

        # Check subsystem files
        if 'subsystem_files' in requirements:
            required_subsystems = requirements.get('required_subsystems', [])
            subsystems_dir = self.base_path / 'subsystems'

            for subsystem_id in required_subsystems:
                subsystem_dir = subsystems_dir / subsystem_id
                if not subsystem_dir.exists():
                    self.issues.append({
                        'type': 'missing_subsystem',
                        'path': f"subsystems/{subsystem_id}",
                        'message': f"Missing subsystem: {subsystem_id}"
                    })
                    continue

                for file_name in requirements['subsystem_files']:
                    file_path = subsystem_dir / file_name
                    if not file_path.exists():
                        self.issues.append({
                            'type': 'missing_subsystem_file',
                            'path': f"subsystems/{subsystem_id}/{file_name}",
                            'message': f"Missing file in {subsystem_id}: {file_name}"
                        })

        # Check registry
        if requirements.get('registry_required'):
            registry_path = self.base_path / 'subsystems' / '_registry.json'
            if not registry_path.exists():
                self.issues.append({
                    'type': 'missing_registry',
                    'path': 'subsystems/_registry.json',
                    'message': "Missing subsystem registry"
                })
            else:
                self._check_registry_completeness(registry_path)

        # Check lib modules
        if 'lib_modules' in requirements:
            for module_path in requirements['lib_modules']:
                full_path = self.base_path / module_path
                if not full_path.exists():
                    self.issues.append({
                        'type': 'missing_module',
                        'path': module_path,
                        'message': f"Missing module: {module_path}"
                    })

        is_complete = len(self.issues) == 0
        return is_complete, self.issues, self.warnings

    def _check_registry_completeness(self, registry_path: Path):
        """Check that the registry is complete and consistent."""
        try:
            with open(registry_path, 'r', encoding='utf-8') as f:
                registry = json.load(f)

            # Check required fields
            required_fields = ['version', 'updated_at', 'subsystems']
            for field in required_fields:
                if field not in registry:
                    self.issues.append({
                        'type': 'missing_registry_field',
                        'path': 'subsystems/_registry.json',
                        'message': f"Missing required field in registry: {field}"
                    })

            # Check that all registered subsystems have directories
            if 'subsystems' in registry:
                for subsystem in registry['subsystems']:
                    subsystem_id = subsystem.get('id')
                    if subsystem_id:
                        subsystem_dir = self.base_path / 'subsystems' / subsystem_id
                        if not subsystem_dir.exists():
                            self.warnings.append({
                                'type': 'registered_subsystem_missing',
                                'path': f"subsystems/{subsystem_id}",
                                'message': f"Subsystem {subsystem_id} registered but directory not found"
                            })

        except Exception as e:
            self.issues.append({
                'type': 'registry_parse_error',
                'path': 'subsystems/_registry.json',
                'message': f"Failed to parse registry: {e}"
            })

    def check_all_phases(self) -> Dict[int, Tuple[bool, List[Dict], List[Dict]]]:
        """Check all phases."""
        results = {}
        for phase in sorted(PHASE_REQUIREMENTS.keys()):
            results[phase] = self.check_phase(phase)
        return results


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description='Check completeness of company-ops documents')
    parser.add_argument('--phase', '-p', type=int, help='Check specific phase (0-4)')
    parser.add_argument('--all', '-a', action='store_true', help='Check all phases')
    parser.add_argument('--base', '-b', type=str, default='.', help='Base path')

    args = parser.parse_args()

    checker = CompletenessChecker(args.base)

    if args.all:
        results = checker.check_all_phases()
        all_complete = True

        for phase, (is_complete, issues, warnings) in results.items():
            print(f"\n{'='*60}")
            print(f"Phase {phase}: {'✅ Complete' if is_complete else '❌ Incomplete'}")
            print('='*60)

            if issues:
                print("\nIssues:")
                for issue in issues:
                    print(f"  ❌ {issue['message']}")

            if warnings:
                print("\nWarnings:")
                for warning in warnings:
                    print(f"  ⚠️  {warning['message']}")

            if not is_complete:
                all_complete = False

        print(f"\n{'='*60}")
        print(f"Overall: {'✅ All phases complete' if all_complete else '❌ Some phases incomplete'}")
        sys.exit(0 if all_complete else 1)

    elif args.phase is not None:
        is_complete, issues, warnings = checker.check_phase(args.phase)

        print(f"\nPhase {args.phase}: {'✅ Complete' if is_complete else '❌ Incomplete'}")

        if issues:
            print("\nIssues:")
            for issue in issues:
                print(f"  ❌ {issue['message']}")

        if warnings:
            print("\nWarnings:")
            for warning in warnings:
                print(f"  ⚠️  {warning['message']}")

        sys.exit(0 if is_complete else 1)

    else:
        parser.print_help()
        sys.exit(1)


if __name__ == '__main__':
    main()

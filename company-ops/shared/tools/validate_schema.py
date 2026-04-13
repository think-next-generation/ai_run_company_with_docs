#!/usr/bin/env python3
"""
Schema Validator for company-ops document system.
Validates YAML and JSON files against their schemas.
"""

import json
import yaml
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import jsonschema
from jsonschema import validate, ValidationError, Draft7Validator

# Schema mapping: file pattern -> schema file
SCHEMA_MAP = {
    'CONSTITUTION.yaml': 'constitution.schema.json',
    'CONTRACT.yaml': 'contract.schema.json',
    'CAPABILITIES.yaml': 'capabilities.schema.json',
    '_registry.json': 'registry.schema.json',
    'global-graph.json': 'graph.schema.json',
    'local-graph.json': 'graph.schema.json',
}

class SchemaValidator:
    """Validates documents against JSON schemas."""

    def __init__(self, base_path: str = '.'):
        self.base_path = Path(base_path)
        self.schemas_dir = self.base_path / 'shared' / 'schemas'
        self.schemas: Dict[str, dict] = {}
        self._load_schemas()

    def _load_schemas(self):
        """Load all schemas from the schemas directory."""
        for schema_file in self.schemas_dir.glob('*.schema.json'):
            with open(schema_file, 'r', encoding='utf-8') as f:
                schema = json.load(f)
                self.schemas[schema_file.name] = schema
                print(f"Loaded schema: {schema_file.name}")

    def _get_schema_for_file(self, filename: str) -> Optional[dict]:
        """Get the appropriate schema for a file."""
        schema_name = SCHEMA_MAP.get(filename)
        if schema_name:
            return self.schemas.get(schema_name)
        return None

    def validate_file(self, file_path: Path) -> Tuple[bool, List[str]]:
        """
        Validate a single file against its schema.

        Returns:
            Tuple of (is_valid, list of errors)
        """
        errors = []

        # Get schema
        schema = self._get_schema_for_file(file_path.name)
        if not schema:
            errors.append(f"No schema found for file: {file_path.name}")
            return False, errors

        # Load file content
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                if file_path.suffix == '.yaml':
                    content = yaml.safe_load(f)
                else:
                    content = json.load(f)
        except Exception as e:
            errors.append(f"Failed to load file: {e}")
            return False, errors

        # Validate
        try:
            Draft7Validator(schema).validate(content)
            return True, []
        except ValidationError as e:
            errors.append(f"Validation error: {e.message}")
            errors.append(f"  Path: {'.'.join(str(p) for p in e.path)}")
            return False, errors
        except Exception as e:
            errors.append(f"Unexpected error: {e}")
            return False, errors

    def validate_directory(self, directory: Path) -> Dict[str, Tuple[bool, List[str]]]:
        """
        Validate all files in a directory recursively.

        Returns:
            Dict mapping file paths to (is_valid, errors) tuples
        """
        results = {}

        for pattern in SCHEMA_MAP.keys():
            for file_path in directory.rglob(pattern):
                results[str(file_path)] = self.validate_file(file_path)

        return results

    def validate_phase(self, phase: int) -> Dict[str, Tuple[bool, List[str]]]:
        """
        Validate all files for a specific phase.

        Args:
            phase: Phase number (0-4)
        """
        results = {}

        # Phase 0: Core documents
        if phase >= 0:
            core_files = [
                self.base_path / 'CHARTER.md',
                self.base_path / 'CONSTITUTION.yaml',
                self.base_path / 'global-graph.json',
            ]
            for file_path in core_files:
                if file_path.exists():
                    if file_path.suffix in ['.yaml', '.json']:
                        results[str(file_path)] = self.validate_file(file_path)

        # Phase 1+: Subsystem documents
        if phase >= 1:
            subsystems_dir = self.base_path / 'subsystems'
            if subsystems_dir.exists():
                for subsystem_dir in subsystems_dir.iterdir():
                    if subsystem_dir.is_dir() and not subsystem_dir.name.startswith('_'):
                        for pattern in ['CONTRACT.yaml', 'CAPABILITIES.yaml', 'local-graph.json']:
                            file_path = subsystem_dir / pattern
                            if file_path.exists():
                                results[str(file_path)] = self.validate_file(file_path)

        return results


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description='Validate company-ops documents')
    parser.add_argument('--file', '-f', type=str, help='Validate a specific file')
    parser.add_argument('--dir', '-d', type=str, help='Validate all files in directory')
    parser.add_argument('--phase', '-p', type=int, help='Validate all files for a phase (0-4)')
    parser.add_argument('--base', '-b', type=str, default='.', help='Base path (default: current directory)')

    args = parser.parse_args()

    validator = SchemaValidator(args.base)

    if args.file:
        file_path = Path(args.file)
        is_valid, errors = validator.validate_file(file_path)
        if is_valid:
            print(f"✅ {file_path}: Valid")
        else:
            print(f"❌ {file_path}: Invalid")
            for error in errors:
                print(f"   {error}")
        sys.exit(0 if is_valid else 1)

    elif args.dir:
        directory = Path(args.dir)
        results = validator.validate_directory(directory)

    elif args.phase is not None:
        results = validator.validate_phase(args.phase)

    else:
        # Default: validate everything
        results = validator.validate_directory(validator.base_path)

    # Print results
    all_valid = True
    for file_path, (is_valid, errors) in results.items():
        if is_valid:
            print(f"✅ {file_path}")
        else:
            print(f"❌ {file_path}")
            for error in errors:
                print(f"   {error}")
            all_valid = False

    print()
    total = len(results)
    passed = sum(1 for _, (v, _) in results.items() if v)
    print(f"Results: {passed}/{total} files valid")

    sys.exit(0 if all_valid else 1)


if __name__ == '__main__':
    main()

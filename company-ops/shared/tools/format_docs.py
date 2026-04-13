#!/usr/bin/env python3
"""
Document Formatter for company-ops document system.
Formats and standardizes YAML, JSON, and Markdown files.
"""

import json
import yaml
import sys
import re
from pathlib import Path
from typing import List, Tuple, Dict
from datetime import datetime


class DocumentFormatter:
    """Formats company-ops documents to standard conventions."""

    def __init__(self, base_path: str = '.'):
        self.base_path = Path(base_path)
        self.formatted: List[str] = []
        self.errors: List[Tuple[str, str]] = []

    def format_yaml(self, file_path: Path) -> bool:
        """Format a YAML file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = yaml.safe_load(f)

            # Add/update last_updated timestamp if it exists
            if isinstance(content, dict) and 'last_updated' in content:
                content['last_updated'] = datetime.now().strftime('%Y-%m-%d')

            # Format with consistent style
            formatted = yaml.dump(
                content,
                default_flow_style=False,
                sort_keys=False,
                allow_unicode=True,
                width=100,
                indent=2
            )

            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(formatted)

            self.formatted.append(str(file_path))
            return True

        except Exception as e:
            self.errors.append((str(file_path), str(e)))
            return False

    def format_json(self, file_path: Path) -> bool:
        """Format a JSON file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = json.load(f)

            # Update metadata timestamps if present
            if isinstance(content, dict):
                if 'metadata' in content and isinstance(content['metadata'], dict):
                    content['metadata']['updated_at'] = datetime.now().isoformat()
                if 'updated_at' in content:
                    content['updated_at'] = datetime.now().isoformat()

            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(content, f, indent=2, ensure_ascii=False)
                f.write('\n')  # Add trailing newline

            self.formatted.append(str(file_path))
            return True

        except Exception as e:
            self.errors.append((str(file_path), str(e)))
            return False

    def format_markdown(self, file_path: Path) -> bool:
        """Format a Markdown file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Normalize line endings
            content = content.replace('\r\n', '\n').replace('\r', '\n')

            # Ensure single newline at end of file
            content = content.rstrip() + '\n'

            # Normalize multiple blank lines to double
            content = re.sub(r'\n{3,}', '\n\n', content)

            # Ensure space after # in headers
            content = re.sub(r'^(#{1,6})([^#\s])', r'\1 \2', content, flags=re.MULTILINE)

            # Ensure space after list markers
            content = re.sub(r'^(\s*[-*+])([^#\s])', r'\1 \2', content, flags=re.MULTILINE)
            content = re.sub(r'^(\s*\d+\.)([^\s])', r'\1 \2', content, flags=re.MULTILINE)

            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)

            self.formatted.append(str(file_path))
            return True

        except Exception as e:
            self.errors.append((str(file_path), str(e)))
            return False

    def format_file(self, file_path: Path) -> Tuple[bool, str]:
        """Format a single file based on its extension."""
        suffix = file_path.suffix.lower()

        if suffix == '.yaml' or suffix == '.yml':
            success = self.format_yaml(file_path)
            return success, 'yaml'
        elif suffix == '.json':
            success = self.format_json(file_path)
            return success, 'json'
        elif suffix == '.md':
            success = self.format_markdown(file_path)
            return success, 'markdown'
        else:
            return False, 'unsupported'

    def format_directory(
        self,
        directory: Path,
        patterns: List[str] = None
    ) -> Dict[str, int]:
        """
        Format all matching files in a directory recursively.

        Returns:
            Dict with counts for each file type
        """
        if patterns is None:
            patterns = ['*.yaml', '*.yml', '*.json', '*.md']

        counts = {'yaml': 0, 'json': 0, 'markdown': 0, 'unsupported': 0, 'success': 0, 'failed': 0}

        for pattern in patterns:
            for file_path in directory.rglob(pattern):
                # Skip node_modules, .git, etc.
                if any(part.startswith('.') or part == 'node_modules' for part in file_path.parts):
                    continue

                success, file_type = self.format_file(file_path)
                counts[file_type] += 1
                if success:
                    counts['success'] += 1
                else:
                    counts['failed'] += 1

        return counts

    def format_phase(self, phase: int) -> Dict[str, int]:
        """Format all documents for a specific phase."""
        counts = {'yaml': 0, 'json': 0, 'markdown': 0, 'unsupported': 0, 'success': 0, 'failed': 0}

        # Phase 0: Core documents
        if phase >= 0:
            core_files = [
                self.base_path / 'CHARTER.md',
                self.base_path / 'CONSTITUTION.yaml',
                self.base_path / 'global-graph.json',
            ]
            for file_path in core_files:
                if file_path.exists():
                    success, file_type = self.format_file(file_path)
                    counts[file_type] += 1
                    if success:
                        counts['success'] += 1
                    else:
                        counts['failed'] += 1

            # Format templates
            templates_dir = self.base_path / 'shared' / 'templates'
            if templates_dir.exists():
                template_counts = self.format_directory(templates_dir)
                for key in counts:
                    counts[key] += template_counts[key]

        # Phase 1+: Subsystem documents
        if phase >= 1:
            subsystems_dir = self.base_path / 'subsystems'
            if subsystems_dir.exists():
                for subsystem_dir in subsystems_dir.iterdir():
                    if subsystem_dir.is_dir() and not subsystem_dir.name.startswith('_'):
                        sub_counts = self.format_directory(subsystem_dir)
                        for key in counts:
                            counts[key] += sub_counts[key]

        return counts


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description='Format company-ops documents')
    parser.add_argument('--file', '-f', type=str, help='Format a specific file')
    parser.add_argument('--dir', '-d', type=str, help='Format all files in directory')
    parser.add_argument('--phase', '-p', type=int, help='Format all files for a phase (0-4)')
    parser.add_argument('--base', '-b', type=str, default='.', help='Base path (default: current directory)')
    parser.add_argument('--check', '-c', action='store_true', help='Check formatting without modifying files')

    args = parser.parse_args()

    formatter = DocumentFormatter(args.base)

    if args.check:
        print("Check mode: files will not be modified")
        # In check mode, just report what would be done
        if args.file:
            file_path = Path(args.file)
            print(f"Would format: {file_path}")
        elif args.dir:
            directory = Path(args.dir)
            for pattern in ['*.yaml', '*.yml', '*.json', '*.md']:
                for file_path in directory.rglob(pattern):
                    if not any(part.startswith('.') or part == 'node_modules' for part in file_path.parts):
                        print(f"Would format: {file_path}")
        sys.exit(0)

    if args.file:
        file_path = Path(args.file)
        success, file_type = formatter.format_file(file_path)
        if success:
            print(f"✅ Formatted: {file_path}")
        else:
            print(f"❌ Failed: {file_path}")
            for path, error in formatter.errors:
                if path == str(file_path):
                    print(f"   Error: {error}")
        sys.exit(0 if success else 1)

    elif args.dir:
        directory = Path(args.dir)
        counts = formatter.format_directory(directory)

    elif args.phase is not None:
        counts = formatter.format_phase(args.phase)

    else:
        # Default: format everything
        counts = formatter.format_directory(formatter.base_path)

    # Print results
    print("\n📊 Formatting Results:")
    print(f"   YAML files: {counts['yaml']}")
    print(f"   JSON files: {counts['json']}")
    print(f"   Markdown files: {counts['markdown']}")
    print(f"   ✅ Successful: {counts['success']}")
    print(f"   ❌ Failed: {counts['failed']}")

    if formatter.formatted:
        print("\n✅ Formatted files:")
        for path in formatter.formatted:
            print(f"   {path}")

    if formatter.errors:
        print("\n❌ Errors:")
        for path, error in formatter.errors:
            print(f"   {path}: {error}")

    sys.exit(0 if counts['failed'] == 0 else 1)


if __name__ == '__main__':
    main()

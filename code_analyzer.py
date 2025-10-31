"""
Code Analyzer Module for Prognosis Marker Project
Analyzes codebase structure, files, and provides statistics
"""

import os
import re
from pathlib import Path
from typing import Dict, List, Tuple
from collections import defaultdict
import git


class CodeAnalyzer:
    """Analyzes code repository structure and content"""

    def __init__(self, root_path: str = "."):
        self.root_path = Path(root_path)
        self.file_extensions = {
            '.r': 'R',
            '.R': 'R',
            '.py': 'Python',
            '.yaml': 'YAML',
            '.yml': 'YAML',
            '.csv': 'Data',
            '.md': 'Markdown',
            '.toml': 'TOML',
            '.json': 'JSON',
            '.txt': 'Text'
        }
        self.ignore_dirs = {'.git', '__pycache__', 'node_modules', '.venv', 'venv', 'results'}

    def get_file_stats(self) -> Dict:
        """Get statistics about files in the repository"""
        stats = {
            'total_files': 0,
            'by_extension': defaultdict(int),
            'by_language': defaultdict(int),
            'total_lines': 0,
            'lines_by_language': defaultdict(int),
            'file_list': []
        }

        for file_path in self._walk_files():
            stats['total_files'] += 1
            ext = file_path.suffix.lower()
            stats['by_extension'][ext] += 1

            language = self.file_extensions.get(ext, 'Other')
            stats['by_language'][language] += 1

            # Count lines for text files
            if self._is_text_file(file_path):
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        lines = len(f.readlines())
                        stats['total_lines'] += lines
                        stats['lines_by_language'][language] += lines

                        stats['file_list'].append({
                            'path': str(file_path.relative_to(self.root_path)),
                            'name': file_path.name,
                            'extension': ext,
                            'language': language,
                            'lines': lines,
                            'size': file_path.stat().st_size
                        })
                except Exception as e:
                    pass

        return stats

    def get_directory_structure(self) -> Dict:
        """Get hierarchical directory structure"""
        structure = {
            'name': self.root_path.name,
            'type': 'directory',
            'path': str(self.root_path),
            'children': []
        }

        def build_tree(path: Path, node: Dict):
            try:
                items = sorted(path.iterdir(), key=lambda x: (not x.is_dir(), x.name))
                for item in items:
                    if item.name.startswith('.') and item.name != '.gitignore':
                        continue
                    if item.is_dir() and item.name in self.ignore_dirs:
                        continue

                    child = {
                        'name': item.name,
                        'type': 'directory' if item.is_dir() else 'file',
                        'path': str(item.relative_to(self.root_path)),
                        'children': []
                    }

                    if item.is_dir():
                        build_tree(item, child)
                    else:
                        child['size'] = item.stat().st_size
                        child['extension'] = item.suffix

                    node['children'].append(child)
            except PermissionError:
                pass

        build_tree(self.root_path, structure)
        return structure

    def analyze_r_file(self, file_path: str) -> Dict:
        """Analyze R source file for functions and structure"""
        functions = []
        libraries = []

        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()

                # Find function definitions
                func_pattern = r'(\w+)\s*<-\s*function\s*\('
                functions = re.findall(func_pattern, content)

                # Find library imports
                lib_pattern = r'library\s*\(\s*["\']?(\w+)["\']?\s*\)'
                libraries = re.findall(lib_pattern, content)

                # Count comments
                comment_lines = len(re.findall(r'^\s*#', content, re.MULTILINE))

                # Count total lines
                total_lines = len(content.split('\n'))

                return {
                    'functions': functions,
                    'function_count': len(functions),
                    'libraries': list(set(libraries)),
                    'library_count': len(set(libraries)),
                    'comment_lines': comment_lines,
                    'total_lines': total_lines,
                    'code_lines': total_lines - comment_lines
                }
        except Exception as e:
            return {
                'error': str(e),
                'functions': [],
                'function_count': 0,
                'libraries': [],
                'library_count': 0
            }

    def analyze_yaml_file(self, file_path: str) -> Dict:
        """Analyze YAML configuration file"""
        try:
            import yaml
            with open(file_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)

            def count_keys(d, depth=0):
                if not isinstance(d, dict):
                    return 0
                count = len(d)
                for v in d.values():
                    if isinstance(v, dict):
                        count += count_keys(v, depth + 1)
                return count

            return {
                'keys': count_keys(data),
                'top_level_keys': list(data.keys()) if isinstance(data, dict) else [],
                'structure': data
            }
        except Exception as e:
            return {'error': str(e)}

    def get_git_info(self) -> Dict:
        """Get git repository information"""
        try:
            repo = git.Repo(self.root_path)

            # Get recent commits
            commits = []
            for commit in list(repo.iter_commits('HEAD', max_count=10)):
                commits.append({
                    'hash': commit.hexsha[:7],
                    'author': commit.author.name,
                    'date': commit.committed_datetime.strftime('%Y-%m-%d %H:%M:%S'),
                    'message': commit.message.strip()
                })

            # Get current branch
            current_branch = repo.active_branch.name

            # Get all branches
            branches = [b.name for b in repo.branches]

            return {
                'current_branch': current_branch,
                'branches': branches,
                'recent_commits': commits,
                'is_dirty': repo.is_dirty()
            }
        except Exception as e:
            return {'error': str(e)}

    def search_in_files(self, pattern: str, file_types: List[str] = None) -> List[Dict]:
        """Search for pattern in files"""
        results = []

        for file_path in self._walk_files():
            if file_types and file_path.suffix not in file_types:
                continue

            if not self._is_text_file(file_path):
                continue

            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    for line_num, line in enumerate(f, 1):
                        if re.search(pattern, line, re.IGNORECASE):
                            results.append({
                                'file': str(file_path.relative_to(self.root_path)),
                                'line_number': line_num,
                                'line': line.strip(),
                                'language': self.file_extensions.get(file_path.suffix.lower(), 'Other')
                            })
            except Exception:
                pass

        return results

    def _walk_files(self):
        """Generator to walk through all files"""
        for root, dirs, files in os.walk(self.root_path):
            # Remove ignored directories
            dirs[:] = [d for d in dirs if d not in self.ignore_dirs and not d.startswith('.')]

            for file in files:
                if file.startswith('.'):
                    continue
                yield Path(root) / file

    def _is_text_file(self, file_path: Path) -> bool:
        """Check if file is a text file"""
        text_extensions = {'.r', '.R', '.py', '.yaml', '.yml', '.md', '.txt', '.toml', '.json', '.csv'}
        return file_path.suffix.lower() in text_extensions

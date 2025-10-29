"""
Dependency analysis for code repositories

Analyzes imports and builds dependency graphs within and across repositories
"""

from collections import defaultdict
from dataclasses import dataclass
from typing import Dict, List, Optional, Set

from scout.parser import ImportStatement, ParsedFile


@dataclass
class Dependency:
    """Represents a dependency between files or modules"""

    source_file: str
    target_module: str
    is_external: bool
    import_type: str  # 'import', 'from_import', 'require', etc.
    symbols: List[str]  # Specific symbols imported


@dataclass
class DependencyGraph:
    """Graph of dependencies for a repository or set of repositories"""

    dependencies: List[Dependency]
    internal_deps: Dict[str, List[str]]  # file -> list of files it depends on
    external_deps: Dict[str, Set[str]]  # file -> set of external packages
    external_packages: Set[str]  # All external packages used

    def get_dependents(self, file_path: str) -> List[str]:
        """Get files that depend on this file"""
        dependents = []
        for dep in self.dependencies:
            if not dep.is_external and dep.target_module == file_path:
                dependents.append(dep.source_file)
        return dependents

    def get_dependencies(self, file_path: str) -> List[str]:
        """Get files this file depends on"""
        return self.internal_deps.get(file_path, [])


class DependencyAnalyzer:
    """Analyzes code dependencies"""

    def __init__(self, repo_name: str):
        """
        Initialize dependency analyzer

        Args:
            repo_name: Name of the repository being analyzed
        """
        self.repo_name = repo_name
        self.file_map: Dict[str, ParsedFile] = {}  # file_path -> ParsedFile

    def add_file(self, parsed_file: ParsedFile) -> None:
        """
        Add a parsed file to the analyzer

        Args:
            parsed_file: ParsedFile object from parser
        """
        self.file_map[parsed_file.file_path] = parsed_file

    def analyze(self) -> DependencyGraph:
        """
        Analyze all added files and build dependency graph

        Returns:
            DependencyGraph object
        """
        all_dependencies = []
        internal_deps = defaultdict(list)
        external_deps = defaultdict(set)
        external_packages = set()

        for file_path, parsed_file in self.file_map.items():
            for imp in parsed_file.imports:
                # Create dependency object
                dep = Dependency(
                    source_file=file_path,
                    target_module=imp.module,
                    is_external=imp.is_external,
                    import_type=self._detect_import_type(parsed_file.language.value),
                    symbols=imp.symbols,
                )
                all_dependencies.append(dep)

                if imp.is_external:
                    # External package
                    package_name = self._extract_package_name(imp.module)
                    external_deps[file_path].add(package_name)
                    external_packages.add(package_name)
                else:
                    # Internal dependency
                    resolved_path = self._resolve_internal_import(
                        file_path, imp.module, parsed_file.language.value
                    )
                    if resolved_path:
                        internal_deps[file_path].append(resolved_path)

        return DependencyGraph(
            dependencies=all_dependencies,
            internal_deps=dict(internal_deps),
            external_deps=dict(external_deps),
            external_packages=external_packages,
        )

    def find_external_calls(self, target_package: str) -> List[Dependency]:
        """
        Find all places where an external package is imported

        Args:
            target_package: Name of the external package

        Returns:
            List of Dependency objects
        """
        graph = self.analyze()
        return [
            dep
            for dep in graph.dependencies
            if dep.is_external and target_package in dep.target_module
        ]

    def find_circular_dependencies(self) -> List[List[str]]:
        """
        Find circular dependencies in the codebase

        Returns:
            List of cycles, where each cycle is a list of file paths
        """
        graph = self.analyze()
        cycles = []
        visited = set()
        rec_stack = set()

        def dfs(node: str, path: List[str]) -> None:
            visited.add(node)
            rec_stack.add(node)
            path.append(node)

            for neighbor in graph.internal_deps.get(node, []):
                if neighbor not in visited:
                    dfs(neighbor, path[:])
                elif neighbor in rec_stack:
                    # Found a cycle
                    cycle_start = path.index(neighbor)
                    cycle = path[cycle_start:] + [neighbor]
                    cycles.append(cycle)

            rec_stack.remove(node)

        for file_path in self.file_map.keys():
            if file_path not in visited:
                dfs(file_path, [])

        return cycles

    def get_dependency_stats(self) -> Dict[str, any]:
        """
        Get statistics about dependencies

        Returns:
            Dictionary with stats
        """
        graph = self.analyze()

        total_files = len(self.file_map)
        total_deps = len(graph.dependencies)
        external_count = sum(1 for d in graph.dependencies if d.is_external)
        internal_count = total_deps - external_count

        # Find most dependent files
        dep_counts = defaultdict(int)
        for deps_list in graph.internal_deps.values():
            for dep in deps_list:
                dep_counts[dep] += 1

        most_dependent = sorted(dep_counts.items(), key=lambda x: x[1], reverse=True)[
            :5
        ]

        return {
            "total_files": total_files,
            "total_dependencies": total_deps,
            "internal_dependencies": internal_count,
            "external_dependencies": external_count,
            "external_packages": len(graph.external_packages),
            "top_external_packages": list(graph.external_packages)[:10],
            "most_dependent_files": [
                {"file": f, "dependent_count": c} for f, c in most_dependent
            ],
        }

    def _detect_import_type(self, language: str) -> str:
        """Detect the type of import statement based on language"""
        type_map = {
            "python": "import",
            "javascript": "require/import",
            "typescript": "import",
            "ruby": "require",
            "go": "import",
        }
        return type_map.get(language, "unknown")

    def _extract_package_name(self, module: str) -> str:
        """
        Extract package name from module path

        Examples:
            '@company/auth-service/lib/auth' -> '@company/auth-service'
            'express' -> 'express'
            'lodash/map' -> 'lodash'
        """
        if module.startswith("@"):
            # Scoped package like @company/package
            parts = module.split("/")
            if len(parts) >= 2:
                return f"{parts[0]}/{parts[1]}"
            return module
        else:
            # Regular package
            return module.split("/")[0]

    def _resolve_internal_import(
        self, source_file: str, import_path: str, language: str
    ) -> Optional[str]:
        """
        Resolve an internal import to a file path

        This is a simplified version - in production, would need more
        sophisticated path resolution based on module systems

        Args:
            source_file: File doing the importing
            import_path: The import path (e.g., './auth', '../utils')
            language: Programming language

        Returns:
            Resolved file path or None if can't resolve
        """
        # For now, just return the import path
        # In production, would:
        # 1. Resolve relative paths (./auth -> /path/to/auth.py)
        # 2. Handle different extensions (.js, .ts, etc.)
        # 3. Handle index files
        # 4. Handle package.json exports

        # Simple check: if it's in our file map, return it
        for file_path in self.file_map.keys():
            if import_path in file_path:
                return file_path

        return None


class CrossRepoAnalyzer:
    """Analyzes dependencies across multiple repositories"""

    def __init__(self):
        """Initialize cross-repo analyzer"""
        self.repo_analyzers: Dict[str, DependencyAnalyzer] = {}

    def add_repo(self, repo_name: str, analyzer: DependencyAnalyzer) -> None:
        """
        Add a repository analyzer

        Args:
            repo_name: Name of the repository
            analyzer: DependencyAnalyzer for the repo
        """
        self.repo_analyzers[repo_name] = analyzer

    def find_cross_repo_dependencies(self) -> List[Dict[str, str]]:
        """
        Find dependencies between repositories

        Returns:
            List of cross-repo dependencies
        """
        cross_deps = []

        for repo_name, analyzer in self.repo_analyzers.items():
            graph = analyzer.analyze()

            # Check if external packages match other repo names
            for package in graph.external_packages:
                # Check if package name matches another repo
                for other_repo in self.repo_analyzers.keys():
                    if other_repo != repo_name and package in other_repo:
                        cross_deps.append(
                            {
                                "source_repo": repo_name,
                                "target_repo": other_repo,
                                "package": package,
                            }
                        )

        return cross_deps

    def suggest_missing_repos(self, indexed_repos: Set[str]) -> List[str]:
        """
        Suggest repositories that should be added based on dependencies

        Args:
            indexed_repos: Set of already indexed repository names

        Returns:
            List of suggested repository names
        """
        all_external_packages = set()

        for analyzer in self.repo_analyzers.values():
            graph = analyzer.analyze()
            all_external_packages.update(graph.external_packages)

        # Filter out standard libraries and packages
        # In production, would have a better heuristic
        suggestions = []
        for package in all_external_packages:
            # Check if it looks like an internal package
            if package.startswith("@") and package not in indexed_repos:
                suggestions.append(package)

        return sorted(suggestions)

"""
Dependency storage and persistence

Saves and loads dependency graphs to/from JSON files
"""

import json
from pathlib import Path
from typing import Dict, List, Optional, Set


class DependencyStorage:
    """Manages persistent storage of dependency graphs"""

    def __init__(
        self,
        storage_path: Optional[str] = None,
        org_prefixes: Optional[List[str]] = None,
    ):
        """
        Initialize dependency storage

        Args:
            storage_path: Path to dependencies file. If None, uses default.
            org_prefixes: Optional list of organization prefixes to filter packages (e.g., ['@myorg/', 'myorg-'])
                         If None, all packages are stored.
        """
        if storage_path:
            self.storage_path = Path(storage_path)
        else:
            # Default to ~/.scout/dependencies.json
            self.storage_path = Path.home() / ".scout" / "dependencies.json"

        self.org_prefixes = org_prefixes or []
        self.dependencies: Dict[str, Dict] = {}
        self.load()

    def load(self) -> None:
        """Load dependencies from file"""
        if not self.storage_path.exists():
            self.dependencies = {}
            return

        try:
            with open(self.storage_path, "r") as f:
                data = json.load(f)
            self.dependencies = data.get("repos", {})
        except Exception as e:
            print(f"Warning: Failed to load dependencies from {self.storage_path}: {e}")
            self.dependencies = {}

    def save(self) -> None:
        """Save dependencies to file"""
        # Ensure directory exists
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)

        data = {"version": "1.0", "repos": self.dependencies}

        with open(self.storage_path, "w") as f:
            json.dump(data, f, indent=2)

    def save_repo_dependencies(
        self,
        repo_name: str,
        internal_deps: Dict[str, List[str]],
        external_packages: List[str],
        cross_repo_deps: List[Dict[str, str]],
    ) -> None:
        """
        Save dependencies for a repository

        Args:
            repo_name: Repository name
            internal_deps: Internal file dependencies
            external_packages: External package names
            cross_repo_deps: Cross-repository dependencies
        """
        # Filter external packages based on org prefixes if configured
        filtered_packages = (
            self._filter_org_packages(external_packages)
            if self.org_prefixes
            else external_packages
        )

        self.dependencies[repo_name] = {
            "internal_count": len(internal_deps),
            "external_packages": filtered_packages,
            "cross_repo_deps": cross_repo_deps,
        }
        self.save()

    def get_repo_dependencies(self, repo_name: str) -> Optional[Dict]:
        """
        Get dependencies for a repository

        Args:
            repo_name: Repository name

        Returns:
            Dictionary with dependency info or None
        """
        return self.dependencies.get(repo_name)

    def get_all_cross_repo_dependencies(self) -> List[Dict[str, str]]:
        """
        Get all cross-repository dependencies

        Returns:
            List of cross-repo dependencies
        """
        all_cross_deps = []
        for repo_name, deps in self.dependencies.items():
            cross_deps = deps.get("cross_repo_deps", [])
            all_cross_deps.extend(cross_deps)
        return all_cross_deps

    def get_external_packages(self, repo_name: str) -> List[str]:
        """
        Get external packages for a repository

        Args:
            repo_name: Repository name

        Returns:
            List of package names
        """
        repo_deps = self.dependencies.get(repo_name, {})
        return repo_deps.get("external_packages", [])

    def suggest_missing_repos(self, indexed_repos: Set[str]) -> List[str]:
        """
        Suggest repositories to add based on dependencies

        Args:
            indexed_repos: Set of already indexed repository names

        Returns:
            List of suggested repository names
        """
        all_packages = set()
        for repo_deps in self.dependencies.values():
            packages = repo_deps.get("external_packages", [])
            all_packages.update(packages)

        # Find packages that aren't indexed
        suggestions = []
        for package in all_packages:
            # Check if package matches any indexed repo
            is_indexed = any(self._repos_match(package, repo) for repo in indexed_repos)
            if not is_indexed:
                suggestions.append(package)

        return sorted(suggestions)

    def _filter_org_packages(self, packages: List[str]) -> List[str]:
        """
        Filter packages to only include organization-specific ones

        Args:
            packages: List of package names

        Returns:
            Filtered list matching configured org prefixes
        """
        org_packages = []
        for package in packages:
            # Check if package matches any org prefix
            package_lower = package.lower()
            for prefix in self.org_prefixes:
                prefix_lower = prefix.lower()
                if (
                    package_lower.startswith(prefix_lower)
                    or prefix_lower in package_lower
                ):
                    org_packages.append(package)
                    break
        return org_packages

    def _repos_match(self, package: str, repo_name: str) -> bool:
        """
        Check if a package name matches a repository

        Args:
            package: Package name
            repo_name: Repository name

        Returns:
            True if they match
        """
        # Normalize package name by removing org prefixes and scopes
        package_lower = package.lower()
        for prefix in self.org_prefixes:
            package_lower = package_lower.replace(prefix.lower(), "")

        # Remove common package/scope prefixes
        package_lower = (
            package_lower.replace("@", "")
            .replace("/", "")
            .replace("-", "")
            .replace("_", "")
        )
        repo_lower = repo_name.lower().replace("-", "").replace("_", "")

        return package_lower in repo_lower or repo_lower in package_lower

    def get_stats(self) -> Dict:
        """Get overall dependency statistics"""
        total_repos = len(self.dependencies)
        total_cross_deps = len(self.get_all_cross_repo_dependencies())

        all_packages = set()
        for repo_deps in self.dependencies.values():
            packages = repo_deps.get("external_packages", [])
            all_packages.update(packages)

        return {
            "total_repos_with_deps": total_repos,
            "total_cross_repo_deps": total_cross_deps,
            "total_unique_packages": len(all_packages),
            "unique_packages": sorted(all_packages),
        }

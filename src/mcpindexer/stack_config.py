"""
Stack configuration management

Manages persistent configuration for repository collections,
including repo paths, indexing status, and metadata.
"""

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional


class IndexingStatus(Enum):
    """Status of repository indexing"""

    NOT_INDEXED = "not_indexed"
    INDEXING = "indexing"
    INDEXED = "indexed"
    ERROR = "error"
    STALE = "stale"  # Needs reindexing


@dataclass
class RepoConfig:
    """Configuration for a single repository"""

    name: str
    path: str
    status: IndexingStatus = IndexingStatus.NOT_INDEXED
    last_indexed: Optional[str] = None  # ISO format timestamp
    last_commit: Optional[str] = None
    files_indexed: int = 0
    chunks_indexed: int = 0
    error_message: Optional[str] = None
    auto_reindex: bool = True  # Auto-reindex on git pull

    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization"""
        return {
            "name": self.name,
            "path": self.path,
            "status": self.status.value,
            "last_indexed": self.last_indexed,
            "last_commit": self.last_commit,
            "files_indexed": self.files_indexed,
            "chunks_indexed": self.chunks_indexed,
            "error_message": self.error_message,
            "auto_reindex": self.auto_reindex,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "RepoConfig":
        """Create from dictionary"""
        return cls(
            name=data["name"],
            path=data["path"],
            status=IndexingStatus(data.get("status", "not_indexed")),
            last_indexed=data.get("last_indexed"),
            last_commit=data.get("last_commit"),
            files_indexed=data.get("files_indexed", 0),
            chunks_indexed=data.get("chunks_indexed", 0),
            error_message=data.get("error_message"),
            auto_reindex=data.get("auto_reindex", True),
        )


class StackConfig:
    """
    Manages the user's repository stack configuration

    Provides persistence for repo collections, tracks indexing status,
    and manages configuration files.
    """

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize stack configuration

        Args:
            config_path: Path to config file. If None, uses default location.
        """
        if config_path:
            self.config_path = Path(config_path)
        else:
            # Default to ~/.mcpindexer/stack.json
            self.config_path = Path.home() / ".mcpindexer" / "stack.json"

        self.repos: Dict[str, RepoConfig] = {}
        self.load()

    def load(self) -> None:
        """Load configuration from file"""
        if not self.config_path.exists():
            # Create default config
            self.repos = {}
            return

        try:
            with open(self.config_path, "r") as f:
                data = json.load(f)

            # Load repos
            for repo_name, repo_data in data.get("repos", {}).items():
                self.repos[repo_name] = RepoConfig.from_dict(repo_data)

        except Exception as e:
            print(f"Warning: Failed to load config from {self.config_path}: {e}")
            self.repos = {}

    def save(self) -> None:
        """Save configuration to file"""
        # Ensure directory exists
        self.config_path.parent.mkdir(parents=True, exist_ok=True)

        # Convert to dict
        data = {
            "version": "1.0",
            "repos": {name: repo.to_dict() for name, repo in self.repos.items()},
        }

        # Save to file
        with open(self.config_path, "w") as f:
            json.dump(data, f, indent=2)

    def add_repo(self, name: str, path: str, auto_reindex: bool = True) -> RepoConfig:
        """
        Add a repository to the stack

        Args:
            name: Repository name
            path: Path to repository
            auto_reindex: Whether to auto-reindex on git pull

        Returns:
            RepoConfig object
        """
        repo = RepoConfig(name=name, path=path, auto_reindex=auto_reindex)
        self.repos[name] = repo
        self.save()
        return repo

    def remove_repo(self, name: str) -> bool:
        """
        Remove a repository from the stack

        Args:
            name: Repository name

        Returns:
            True if removed, False if not found
        """
        if name in self.repos:
            del self.repos[name]
            self.save()
            return True
        return False

    def update_repo_status(
        self,
        name: str,
        status: IndexingStatus,
        last_commit: Optional[str] = None,
        files_indexed: Optional[int] = None,
        chunks_indexed: Optional[int] = None,
        error_message: Optional[str] = None,
    ) -> None:
        """
        Update repository indexing status

        Args:
            name: Repository name
            status: New status
            last_commit: Git commit hash
            files_indexed: Number of files indexed
            chunks_indexed: Number of chunks indexed
            error_message: Error message if status is ERROR
        """
        if name not in self.repos:
            return

        repo = self.repos[name]
        repo.status = status

        if status == IndexingStatus.INDEXED:
            repo.last_indexed = datetime.now(timezone.utc).isoformat()

        if last_commit is not None:
            repo.last_commit = last_commit

        if files_indexed is not None:
            repo.files_indexed = files_indexed

        if chunks_indexed is not None:
            repo.chunks_indexed = chunks_indexed

        if error_message is not None:
            repo.error_message = error_message

        self.save()

    def get_repo(self, name: str) -> Optional[RepoConfig]:
        """Get repository configuration"""
        return self.repos.get(name)

    def list_repos(
        self, status_filter: Optional[IndexingStatus] = None
    ) -> List[RepoConfig]:
        """
        List all repositories

        Args:
            status_filter: Optional filter by status

        Returns:
            List of RepoConfig objects
        """
        repos = list(self.repos.values())

        if status_filter:
            repos = [r for r in repos if r.status == status_filter]

        return repos

    def needs_reindex(self, name: str, current_commit: str) -> bool:
        """
        Check if a repository needs reindexing

        Args:
            name: Repository name
            current_commit: Current git commit hash

        Returns:
            True if needs reindexing
        """
        repo = self.get_repo(name)
        if not repo:
            return True

        # Need reindex if never indexed
        if repo.status == IndexingStatus.NOT_INDEXED:
            return True

        # Need reindex if marked as stale or error
        if repo.status in (IndexingStatus.STALE, IndexingStatus.ERROR):
            return True

        # Need reindex if commit changed
        if repo.last_commit and repo.last_commit != current_commit:
            return True

        return False

    def mark_stale(self, name: str) -> None:
        """Mark a repository as needing reindexing"""
        if name in self.repos:
            self.repos[name].status = IndexingStatus.STALE
            self.save()

    def get_stats(self) -> Dict:
        """Get overall stack statistics"""
        total = len(self.repos)
        by_status = {}

        for status in IndexingStatus:
            count = sum(1 for r in self.repos.values() if r.status == status)
            by_status[status.value] = count

        total_files = sum(r.files_indexed for r in self.repos.values())
        total_chunks = sum(r.chunks_indexed for r in self.repos.values())

        return {
            "total_repos": total,
            "by_status": by_status,
            "total_files_indexed": total_files,
            "total_chunks_indexed": total_chunks,
        }

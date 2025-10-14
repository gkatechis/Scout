"""
Tests for stack configuration system
"""
import pytest
import tempfile
import shutil
import json
from pathlib import Path
from mcpindexer.stack_config import StackConfig, RepoConfig, IndexingStatus


@pytest.fixture
def temp_config_dir():
    """Create temporary directory for config"""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir, ignore_errors=True)


class TestRepoConfig:
    """Tests for RepoConfig class"""

    def test_repo_config_initialization(self):
        """Test repo config initializes with defaults"""
        repo = RepoConfig(name="test-repo", path="/path/to/repo")

        assert repo.name == "test-repo"
        assert repo.path == "/path/to/repo"
        assert repo.status == IndexingStatus.NOT_INDEXED
        assert repo.last_indexed is None
        assert repo.files_indexed == 0
        assert repo.chunks_indexed == 0

    def test_repo_config_to_dict(self):
        """Test converting repo config to dict"""
        repo = RepoConfig(name="test-repo", path="/path/to/repo")
        data = repo.to_dict()

        assert data["name"] == "test-repo"
        assert data["path"] == "/path/to/repo"
        assert data["status"] == "not_indexed"
        assert "last_indexed" in data

    def test_repo_config_from_dict(self):
        """Test creating repo config from dict"""
        data = {
            "name": "test-repo",
            "path": "/path/to/repo",
            "status": "indexed",
            "files_indexed": 100,
            "chunks_indexed": 500
        }

        repo = RepoConfig.from_dict(data)

        assert repo.name == "test-repo"
        assert repo.path == "/path/to/repo"
        assert repo.status == IndexingStatus.INDEXED
        assert repo.files_indexed == 100
        assert repo.chunks_indexed == 500


class TestStackConfig:
    """Tests for StackConfig class"""

    def test_stack_config_initialization(self, temp_config_dir):
        """Test stack config initializes"""
        config_path = temp_config_dir / "stack.json"
        config = StackConfig(str(config_path))

        assert config.config_path == config_path
        assert len(config.repos) == 0

    def test_add_repo(self, temp_config_dir):
        """Test adding a repository"""
        config_path = temp_config_dir / "stack.json"
        config = StackConfig(str(config_path))

        repo = config.add_repo("test-repo", "/path/to/repo")

        assert repo.name == "test-repo"
        assert repo.path == "/path/to/repo"
        assert "test-repo" in config.repos

    def test_remove_repo(self, temp_config_dir):
        """Test removing a repository"""
        config_path = temp_config_dir / "stack.json"
        config = StackConfig(str(config_path))

        config.add_repo("test-repo", "/path/to/repo")
        result = config.remove_repo("test-repo")

        assert result is True
        assert "test-repo" not in config.repos

    def test_remove_nonexistent_repo(self, temp_config_dir):
        """Test removing a repo that doesn't exist"""
        config_path = temp_config_dir / "stack.json"
        config = StackConfig(str(config_path))

        result = config.remove_repo("nonexistent")

        assert result is False

    def test_update_repo_status(self, temp_config_dir):
        """Test updating repository status"""
        config_path = temp_config_dir / "stack.json"
        config = StackConfig(str(config_path))

        config.add_repo("test-repo", "/path/to/repo")
        config.update_repo_status(
            "test-repo",
            IndexingStatus.INDEXED,
            last_commit="abc123",
            files_indexed=100,
            chunks_indexed=500
        )

        repo = config.get_repo("test-repo")
        assert repo.status == IndexingStatus.INDEXED
        assert repo.last_commit == "abc123"
        assert repo.files_indexed == 100
        assert repo.chunks_indexed == 500
        assert repo.last_indexed is not None

    def test_get_repo(self, temp_config_dir):
        """Test getting a repository"""
        config_path = temp_config_dir / "stack.json"
        config = StackConfig(str(config_path))

        config.add_repo("test-repo", "/path/to/repo")
        repo = config.get_repo("test-repo")

        assert repo is not None
        assert repo.name == "test-repo"

    def test_get_nonexistent_repo(self, temp_config_dir):
        """Test getting a repo that doesn't exist"""
        config_path = temp_config_dir / "stack.json"
        config = StackConfig(str(config_path))

        repo = config.get_repo("nonexistent")

        assert repo is None

    def test_list_repos(self, temp_config_dir):
        """Test listing all repositories"""
        config_path = temp_config_dir / "stack.json"
        config = StackConfig(str(config_path))

        config.add_repo("repo1", "/path/to/repo1")
        config.add_repo("repo2", "/path/to/repo2")

        repos = config.list_repos()

        assert len(repos) == 2
        repo_names = [r.name for r in repos]
        assert "repo1" in repo_names
        assert "repo2" in repo_names

    def test_list_repos_with_filter(self, temp_config_dir):
        """Test listing repos with status filter"""
        config_path = temp_config_dir / "stack.json"
        config = StackConfig(str(config_path))

        config.add_repo("repo1", "/path/to/repo1")
        config.add_repo("repo2", "/path/to/repo2")
        config.update_repo_status("repo1", IndexingStatus.INDEXED)

        indexed_repos = config.list_repos(status_filter=IndexingStatus.INDEXED)

        assert len(indexed_repos) == 1
        assert indexed_repos[0].name == "repo1"

    def test_needs_reindex(self, temp_config_dir):
        """Test checking if repo needs reindexing"""
        config_path = temp_config_dir / "stack.json"
        config = StackConfig(str(config_path))

        config.add_repo("test-repo", "/path/to/repo")

        # Should need reindex (never indexed)
        assert config.needs_reindex("test-repo", "abc123") is True

        # Mark as indexed
        config.update_repo_status(
            "test-repo",
            IndexingStatus.INDEXED,
            last_commit="abc123"
        )

        # Should not need reindex (same commit)
        assert config.needs_reindex("test-repo", "abc123") is False

        # Should need reindex (different commit)
        assert config.needs_reindex("test-repo", "def456") is True

    def test_mark_stale(self, temp_config_dir):
        """Test marking a repo as stale"""
        config_path = temp_config_dir / "stack.json"
        config = StackConfig(str(config_path))

        config.add_repo("test-repo", "/path/to/repo")
        config.update_repo_status("test-repo", IndexingStatus.INDEXED)

        config.mark_stale("test-repo")

        repo = config.get_repo("test-repo")
        assert repo.status == IndexingStatus.STALE

    def test_get_stats(self, temp_config_dir):
        """Test getting stack statistics"""
        config_path = temp_config_dir / "stack.json"
        config = StackConfig(str(config_path))

        config.add_repo("repo1", "/path/to/repo1")
        config.add_repo("repo2", "/path/to/repo2")
        config.update_repo_status("repo1", IndexingStatus.INDEXED, files_indexed=100, chunks_indexed=500)

        stats = config.get_stats()

        assert stats["total_repos"] == 2
        assert stats["by_status"]["indexed"] == 1
        assert stats["by_status"]["not_indexed"] == 1
        assert stats["total_files_indexed"] == 100
        assert stats["total_chunks_indexed"] == 500

    def test_persistence(self, temp_config_dir):
        """Test that config persists across instances"""
        config_path = temp_config_dir / "stack.json"

        # Create config and add repo
        config1 = StackConfig(str(config_path))
        config1.add_repo("test-repo", "/path/to/repo")

        # Create new instance and check repo is loaded
        config2 = StackConfig(str(config_path))
        repo = config2.get_repo("test-repo")

        assert repo is not None
        assert repo.name == "test-repo"
        assert repo.path == "/path/to/repo"

    def test_save_creates_directory(self, temp_config_dir):
        """Test that save creates config directory if needed"""
        config_path = temp_config_dir / "subdir" / "stack.json"
        config = StackConfig(str(config_path))

        config.add_repo("test-repo", "/path/to/repo")

        # Check directory was created
        assert config_path.parent.exists()
        assert config_path.exists()

    def test_config_file_format(self, temp_config_dir):
        """Test that config file has correct format"""
        config_path = temp_config_dir / "stack.json"
        config = StackConfig(str(config_path))

        config.add_repo("test-repo", "/path/to/repo")

        # Read file directly
        with open(config_path, 'r') as f:
            data = json.load(f)

        assert "version" in data
        assert "repos" in data
        assert "test-repo" in data["repos"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

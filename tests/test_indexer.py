"""
Tests for main repository indexer
"""

import shutil
import tempfile
from pathlib import Path

import pytest

from mcpindexer.embeddings import EmbeddingStore
from mcpindexer.indexer import IndexingResult, MultiRepoIndexer, RepoIndexer


@pytest.fixture
def temp_repo():
    """Create a temporary repository with sample files"""
    temp_dir = tempfile.mkdtemp()
    repo_path = Path(temp_dir) / "test_repo"
    repo_path.mkdir()

    # Create some sample files
    (repo_path / "auth.py").write_text(
        """
import bcrypt

def authenticate(username, password):
    return bcrypt.checkpw(password, get_hash(username))
"""
    )

    (repo_path / "user.py").write_text(
        """
class User:
    def __init__(self, name):
        self.name = name
"""
    )

    (repo_path / "api.js").write_text(
        """
function login(req, res) {
    res.json({ success: true });
}
"""
    )

    yield repo_path

    # Cleanup
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def temp_db():
    """Create temporary database"""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def embedding_store(temp_db):
    """Create embedding store"""
    store = EmbeddingStore(db_path=temp_db, collection_name="test")
    yield store
    store.reset()


class TestRepoIndexer:
    """Tests for RepoIndexer class"""

    def test_indexer_initialization(self, temp_repo, embedding_store):
        """Test indexer initializes correctly"""
        indexer = RepoIndexer(
            repo_path=str(temp_repo),
            repo_name="test-repo",
            embedding_store=embedding_store,
        )

        assert indexer.repo_name == "test-repo"
        assert indexer.repo_path == temp_repo
        assert indexer.parser is not None
        assert indexer.chunker is not None

    def test_index_repository(self, temp_repo, embedding_store):
        """Test indexing a repository"""
        indexer = RepoIndexer(
            repo_path=str(temp_repo),
            repo_name="test-repo",
            embedding_store=embedding_store,
        )

        result = indexer.index()

        assert isinstance(result, IndexingResult)
        assert result.repo_name == "test-repo"
        assert result.files_processed > 0
        assert result.chunks_created > 0
        assert result.chunks_indexed > 0

    def test_index_with_progress_callback(self, temp_repo, embedding_store):
        """Test indexing with progress callback"""
        indexer = RepoIndexer(
            repo_path=str(temp_repo),
            repo_name="test-repo",
            embedding_store=embedding_store,
        )

        progress_calls = []

        def progress_callback(files, chunks):
            progress_calls.append((files, chunks))

        result = indexer.index(progress_callback=progress_callback)

        assert result.files_processed > 0
        # Progress callback may or may not be called depending on file count

    def test_index_single_file(self, temp_repo, embedding_store):
        """Test indexing a single file"""
        indexer = RepoIndexer(
            repo_path=str(temp_repo),
            repo_name="test-repo",
            embedding_store=embedding_store,
        )

        file_path = str(temp_repo / "auth.py")
        chunks = indexer.index_file(file_path)

        assert len(chunks) > 0

    def test_get_stats(self, temp_repo, embedding_store):
        """Test getting indexer statistics"""
        indexer = RepoIndexer(
            repo_path=str(temp_repo),
            repo_name="test-repo",
            embedding_store=embedding_store,
        )

        # Index first
        indexer.index()

        stats = indexer.get_stats()

        assert "repo_name" in stats
        assert "chunks_indexed" in stats
        assert "files_indexed" in stats
        assert stats["repo_name"] == "test-repo"
        assert stats["chunks_indexed"] > 0

    def test_reindex_force(self, temp_repo, embedding_store):
        """Test force reindexing"""
        indexer = RepoIndexer(
            repo_path=str(temp_repo),
            repo_name="test-repo",
            embedding_store=embedding_store,
        )

        # Initial index
        result1 = indexer.index()
        chunks1 = result1.chunks_indexed

        # Force reindex
        result2 = indexer.reindex(force=True)

        # Should have similar number of chunks
        assert result2.chunks_indexed > 0
        assert abs(result2.chunks_indexed - chunks1) <= 1  # Allow small variance

    def test_scan_repo(self, temp_repo, embedding_store):
        """Test repository scanning"""
        indexer = RepoIndexer(
            repo_path=str(temp_repo),
            repo_name="test-repo",
            embedding_store=embedding_store,
        )

        files = list(indexer._scan_repo())

        # Should find our test files
        assert len(files) == 3  # auth.py, user.py, api.js

        # Check extensions
        extensions = {f.suffix for f in files}
        assert ".py" in extensions
        assert ".js" in extensions

    def test_file_filtering(self, temp_repo, embedding_store):
        """Test indexing with file filter"""
        indexer = RepoIndexer(
            repo_path=str(temp_repo),
            repo_name="test-repo",
            embedding_store=embedding_store,
        )

        # Only index Python files
        def python_only(path):
            return path.suffix == ".py"

        result = indexer.index(file_filter=python_only)

        # Should only process Python files
        assert result.files_processed == 2  # auth.py and user.py

    def test_indexing_result_attributes(self, temp_repo, embedding_store):
        """Test IndexingResult has all required attributes"""
        indexer = RepoIndexer(
            repo_path=str(temp_repo),
            repo_name="test-repo",
            embedding_store=embedding_store,
        )

        result = indexer.index()

        assert hasattr(result, "repo_name")
        assert hasattr(result, "files_processed")
        assert hasattr(result, "files_skipped")
        assert hasattr(result, "chunks_created")
        assert hasattr(result, "chunks_indexed")
        assert hasattr(result, "git_commit")
        assert hasattr(result, "errors")


class TestMultiRepoIndexer:
    """Tests for MultiRepoIndexer class"""

    def test_multi_indexer_initialization(self, embedding_store):
        """Test multi-repo indexer initializes"""
        indexer = MultiRepoIndexer(embedding_store=embedding_store)

        assert len(indexer.repo_indexers) == 0

    def test_add_repo(self, temp_repo, embedding_store):
        """Test adding a repository"""
        indexer = MultiRepoIndexer(embedding_store=embedding_store)

        result = indexer.add_repo(
            repo_path=str(temp_repo), repo_name="test-repo", auto_index=True
        )

        assert isinstance(result, IndexingResult)
        assert result.files_processed > 0
        assert "test-repo" in indexer.repo_indexers

    def test_add_repo_no_auto_index(self, temp_repo, embedding_store):
        """Test adding repo without auto-indexing"""
        indexer = MultiRepoIndexer(embedding_store=embedding_store)

        result = indexer.add_repo(
            repo_path=str(temp_repo), repo_name="test-repo", auto_index=False
        )

        assert result.files_processed == 0
        assert "test-repo" in indexer.repo_indexers

    def test_remove_repo(self, temp_repo, embedding_store):
        """Test removing a repository"""
        indexer = MultiRepoIndexer(embedding_store=embedding_store)

        # Add repo
        indexer.add_repo(
            repo_path=str(temp_repo), repo_name="test-repo", auto_index=True
        )

        # Remove it
        deleted_count = indexer.remove_repo("test-repo")

        assert deleted_count > 0
        assert "test-repo" not in indexer.repo_indexers

    def test_list_repos(self, temp_repo, embedding_store):
        """Test listing repositories"""
        indexer = MultiRepoIndexer(embedding_store=embedding_store)

        indexer.add_repo(
            repo_path=str(temp_repo), repo_name="test-repo", auto_index=True
        )

        repos = indexer.list_repos()

        assert "test-repo" in repos

    def test_get_repo_stats(self, temp_repo, embedding_store):
        """Test getting stats for a repository"""
        indexer = MultiRepoIndexer(embedding_store=embedding_store)

        indexer.add_repo(
            repo_path=str(temp_repo), repo_name="test-repo", auto_index=True
        )

        stats = indexer.get_repo_stats("test-repo")

        assert stats is not None
        assert stats["repo_name"] == "test-repo"

    def test_multiple_repos(self, temp_repo, embedding_store):
        """Test managing multiple repositories"""
        indexer = MultiRepoIndexer(embedding_store=embedding_store)

        # Add multiple repos (using same path for simplicity)
        indexer.add_repo(str(temp_repo), "repo1", auto_index=True)
        indexer.add_repo(str(temp_repo), "repo2", auto_index=True)

        repos = indexer.list_repos()

        assert "repo1" in repos
        assert "repo2" in repos

    def test_cross_repo_dependencies(self, temp_repo, embedding_store):
        """Test getting cross-repo dependencies"""
        indexer = MultiRepoIndexer(embedding_store=embedding_store)

        indexer.add_repo(str(temp_repo), "repo1", auto_index=True)
        indexer.add_repo(str(temp_repo), "repo2", auto_index=True)

        # Get cross-repo dependencies
        cross_deps = indexer.get_cross_repo_dependencies()

        # Should return a list (may be empty for our test data)
        assert isinstance(cross_deps, list)

    def test_suggest_missing_repos(self, temp_repo, embedding_store):
        """Test suggesting missing repositories"""
        indexer = MultiRepoIndexer(embedding_store=embedding_store)

        indexer.add_repo(str(temp_repo), "repo1", auto_index=True)

        # Get suggestions
        suggestions = indexer.suggest_missing_repos()

        # Should return a list (may be empty for our test data)
        assert isinstance(suggestions, list)

    def test_cross_repo_analyzer_integration(self, temp_repo, embedding_store):
        """Test that CrossRepoAnalyzer is properly integrated"""
        indexer = MultiRepoIndexer(embedding_store=embedding_store)

        # Add repos
        indexer.add_repo(str(temp_repo), "repo1", auto_index=True)
        indexer.add_repo(str(temp_repo), "repo2", auto_index=True)

        # Check that repos are in cross analyzer
        assert "repo1" in indexer.cross_repo_analyzer.repo_analyzers
        assert "repo2" in indexer.cross_repo_analyzer.repo_analyzers

        # Remove a repo
        indexer.remove_repo("repo1")

        # Check it's removed from cross analyzer
        assert "repo1" not in indexer.cross_repo_analyzer.repo_analyzers
        assert "repo2" in indexer.cross_repo_analyzer.repo_analyzers


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

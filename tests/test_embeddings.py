"""
Tests for embedding generation and vector storage
"""

import shutil
import tempfile
from pathlib import Path

import pytest

from mcpindexer.chunker import CodeChunk
from mcpindexer.embeddings import EmbeddingStore, SearchResult


@pytest.fixture
def temp_db_path():
    """Create temporary database path"""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    # Cleanup
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def embedding_store(temp_db_path):
    """Create embedding store with temporary database"""
    store = EmbeddingStore(db_path=temp_db_path, collection_name="test_collection")
    yield store
    # Cleanup
    store.reset()


@pytest.fixture
def sample_chunks():
    """Create sample code chunks for testing"""
    return [
        CodeChunk(
            chunk_id="test-repo:chunk:1",
            file_path="auth.py",
            repo_name="test-repo",
            language="python",
            chunk_type="function",
            code_text="def authenticate_user(username, password):\n    return check_credentials(username, password)",
            start_line=10,
            end_line=11,
            symbol_name="authenticate_user",
            parent_class=None,
            imports=["bcrypt", "jwt"],
            context_text="File: auth.py | Function: authenticate_user\n\ndef authenticate_user(username, password):\n    return check_credentials(username, password)",
            token_count=50,
        ),
        CodeChunk(
            chunk_id="test-repo:chunk:2",
            file_path="user.py",
            repo_name="test-repo",
            language="python",
            chunk_type="class",
            code_text="class User:\n    def __init__(self, name):\n        self.name = name",
            start_line=5,
            end_line=7,
            symbol_name="User",
            parent_class=None,
            imports=["dataclasses"],
            context_text="File: user.py | Class: User\n\nclass User:\n    def __init__(self, name):\n        self.name = name",
            token_count=40,
        ),
        CodeChunk(
            chunk_id="other-repo:chunk:1",
            file_path="login.js",
            repo_name="other-repo",
            language="javascript",
            chunk_type="function",
            code_text="function login(username, password) {\n    return authenticateUser(username, password);\n}",
            start_line=1,
            end_line=3,
            symbol_name="login",
            parent_class=None,
            imports=["auth"],
            context_text="File: login.js | Function: login\n\nfunction login(username, password) {\n    return authenticateUser(username, password);\n}",
            token_count=45,
        ),
    ]


class TestEmbeddingStore:
    """Tests for EmbeddingStore class"""

    def test_store_initialization(self, embedding_store):
        """Test embedding store initializes correctly"""
        assert embedding_store.collection is not None
        assert embedding_store.model is not None
        assert embedding_store.collection_name == "test_collection"

    def test_add_chunks(self, embedding_store, sample_chunks):
        """Test adding chunks to the store"""
        embedding_store.add_chunks(sample_chunks)

        # Verify chunks were added by checking collection size
        results = embedding_store.collection.get()
        assert len(results["ids"]) == 3

    def test_add_empty_chunks(self, embedding_store):
        """Test adding empty list of chunks"""
        embedding_store.add_chunks([])
        results = embedding_store.collection.get()
        assert len(results["ids"]) == 0

    def test_semantic_search(self, embedding_store, sample_chunks):
        """Test semantic search functionality"""
        embedding_store.add_chunks(sample_chunks)

        # Search for authentication-related code
        results = embedding_store.semantic_search("user authentication", n_results=5)

        assert len(results) > 0
        assert all(isinstance(r, SearchResult) for r in results)

        # Should find the authenticate_user function
        auth_results = [r for r in results if "authenticate" in r.code_text.lower()]
        assert len(auth_results) > 0

    def test_semantic_search_with_repo_filter(self, embedding_store, sample_chunks):
        """Test semantic search with repository filter"""
        embedding_store.add_chunks(sample_chunks)

        # Search only in test-repo
        results = embedding_store.semantic_search(
            "authentication", n_results=10, repo_filter=["test-repo"]
        )

        assert len(results) > 0
        assert all(r.repo_name == "test-repo" for r in results)

    def test_semantic_search_with_language_filter(self, embedding_store, sample_chunks):
        """Test semantic search with language filter"""
        embedding_store.add_chunks(sample_chunks)

        # Search only Python code
        results = embedding_store.semantic_search(
            "user", n_results=10, language_filter="python"
        )

        assert len(results) > 0
        assert all(r.metadata["language"] == "python" for r in results)

    def test_find_by_symbol(self, embedding_store, sample_chunks):
        """Test finding code by exact symbol name"""
        embedding_store.add_chunks(sample_chunks)

        results = embedding_store.find_by_symbol("authenticate_user")

        assert len(results) == 1
        assert results[0].symbol_name == "authenticate_user"
        assert "authenticate_user" in results[0].code_text

    def test_find_by_symbol_with_repo_filter(self, embedding_store, sample_chunks):
        """Test finding symbol with repository filter"""
        embedding_store.add_chunks(sample_chunks)

        results = embedding_store.find_by_symbol("login", repo_filter=["other-repo"])

        assert len(results) == 1
        assert results[0].repo_name == "other-repo"

    def test_find_related_by_file(self, embedding_store, sample_chunks):
        """Test finding related code by file"""
        embedding_store.add_chunks(sample_chunks)

        results = embedding_store.find_related_by_file(
            file_path="auth.py", repo_name="test-repo", n_results=5
        )

        # Should find related code, excluding the same file
        assert all(r.file_path != "auth.py" for r in results)

    def test_list_repos(self, embedding_store, sample_chunks):
        """Test listing all repositories"""
        embedding_store.add_chunks(sample_chunks)

        repos = embedding_store.list_repos()

        assert "test-repo" in repos
        assert "other-repo" in repos
        assert len(repos) == 2

    def test_get_repo_stats(self, embedding_store, sample_chunks):
        """Test getting repository statistics"""
        embedding_store.add_chunks(sample_chunks)

        stats = embedding_store.get_repo_stats("test-repo")

        assert stats["repo_name"] == "test-repo"
        assert stats["chunk_count"] == 2
        assert "auth.py" in stats["files"]
        assert "user.py" in stats["files"]
        assert "python" in stats["languages"]

    def test_get_repo_stats_nonexistent(self, embedding_store):
        """Test getting stats for nonexistent repo"""
        stats = embedding_store.get_repo_stats("nonexistent-repo")

        assert stats["repo_name"] == "nonexistent-repo"
        assert stats["chunk_count"] == 0
        assert len(stats["files"]) == 0

    def test_delete_repo(self, embedding_store, sample_chunks):
        """Test deleting a repository"""
        embedding_store.add_chunks(sample_chunks)

        deleted_count = embedding_store.delete_repo("test-repo")

        assert deleted_count == 2  # Two chunks from test-repo

        # Verify only other-repo remains
        remaining = embedding_store.collection.get()
        assert len(remaining["ids"]) == 1
        assert remaining["metadatas"][0]["repo_name"] == "other-repo"

    def test_delete_nonexistent_repo(self, embedding_store):
        """Test deleting nonexistent repository"""
        deleted_count = embedding_store.delete_repo("nonexistent")
        assert deleted_count == 0

    def test_reset(self, embedding_store, sample_chunks):
        """Test resetting the collection"""
        embedding_store.add_chunks(sample_chunks)

        # Verify chunks exist
        results = embedding_store.collection.get()
        assert len(results["ids"]) == 3

        # Reset
        embedding_store.reset()

        # Verify collection is empty
        results = embedding_store.collection.get()
        assert len(results["ids"]) == 0

    def test_search_result_attributes(self, embedding_store, sample_chunks):
        """Test SearchResult has all required attributes"""
        embedding_store.add_chunks(sample_chunks)

        results = embedding_store.semantic_search("test", n_results=1)

        if results:
            result = results[0]
            assert hasattr(result, "chunk_id")
            assert hasattr(result, "file_path")
            assert hasattr(result, "repo_name")
            assert hasattr(result, "symbol_name")
            assert hasattr(result, "code_text")
            assert hasattr(result, "score")
            assert hasattr(result, "metadata")

    def test_persistence(self, temp_db_path, sample_chunks):
        """Test that data persists across store instances"""
        # Create store and add chunks
        store1 = EmbeddingStore(db_path=temp_db_path, collection_name="persist_test")
        store1.add_chunks(sample_chunks)

        # Close and recreate store
        del store1

        store2 = EmbeddingStore(db_path=temp_db_path, collection_name="persist_test")

        # Data should still be there
        results = store2.collection.get()
        assert len(results["ids"]) == 3

        # Cleanup
        store2.reset()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

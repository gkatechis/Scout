"""
Tests for embedding generation and vector storage
"""

import os
import shutil
import tempfile

import pytest

from mcpindexer.chunker import CodeChunk
from mcpindexer.embeddings import EmbeddingStore, SearchResult
from mcpindexer.keyword_search import tokenize_code


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

    def test_list_repos_with_large_chunk_count(self, embedding_store):
        """Test listing repositories when chunk count exceeds 10,000"""
        from mcpindexer.chunker import CodeChunk

        # Create 15 repositories with ~800 chunks each to exceed 10,000 total
        # Add in batches to respect ChromaDB's batch size limit
        num_repos = 15
        chunks_per_repo = 800
        batch_size = 5000

        for repo_idx in range(num_repos):
            repo_name = f"large-repo-{repo_idx}"
            chunks = []
            for chunk_idx in range(chunks_per_repo):
                chunks.append(
                    CodeChunk(
                        chunk_id=f"{repo_name}:chunk:{chunk_idx}",
                        file_path=f"file_{chunk_idx % 10}.py",
                        repo_name=repo_name,
                        language="python",
                        chunk_type="function",
                        code_text=f"def function_{chunk_idx}(): pass",
                        start_line=chunk_idx * 10,
                        end_line=chunk_idx * 10 + 5,
                        symbol_name=f"function_{chunk_idx}",
                        parent_class=None,
                        imports=[],
                        context_text=f"def function_{chunk_idx}(): pass",
                        token_count=10,
                    )
                )
                # Add in batches to respect ChromaDB limits
                if len(chunks) >= batch_size:
                    embedding_store.add_chunks(chunks)
                    chunks = []

            # Add remaining chunks for this repo
            if chunks:
                embedding_store.add_chunks(chunks)

        # Verify total chunk count exceeds 10,000
        total_chunks = embedding_store.collection.count()
        assert total_chunks > 10000, f"Test requires >10k chunks, got {total_chunks}"

        # List repos should still find all repositories
        repos = embedding_store.list_repos()

        assert len(repos) == num_repos
        for repo_idx in range(num_repos):
            assert f"large-repo-{repo_idx}" in repos

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

    def test_delete_file(self, embedding_store, sample_chunks):
        """Test deleting chunks for a specific file"""
        embedding_store.add_chunks(sample_chunks)

        # Delete auth.py file
        deleted_count = embedding_store.delete_file("test-repo", "auth.py")

        assert deleted_count == 1  # One chunk from auth.py

        # Verify only auth.py chunks were deleted
        remaining = embedding_store.collection.get(where={"repo_name": "test-repo"})
        assert len(remaining["ids"]) == 1  # Only user.py remaining
        remaining_files = {meta["file_path"] for meta in remaining["metadatas"]}
        assert "auth.py" not in remaining_files
        assert "user.py" in remaining_files

    def test_delete_file_nonexistent(self, embedding_store):
        """Test deleting nonexistent file"""
        deleted_count = embedding_store.delete_file("test-repo", "nonexistent.py")
        assert deleted_count == 0

    def test_delete_file_with_multiple_chunks(self, embedding_store):
        """Test deleting file with multiple chunks"""
        from mcpindexer.chunker import CodeChunk

        # Create multiple chunks for same file
        chunks = [
            CodeChunk(
                chunk_id=f"test:file:chunk{i}",
                file_path="multi_chunk.py",
                repo_name="test-repo",
                language="python",
                chunk_type="function",
                code_text=f"def function_{i}(): pass",
                start_line=i * 10,
                end_line=i * 10 + 5,
                symbol_name=f"function_{i}",
                parent_class=None,
                imports=[],
                context_text=f"def function_{i}(): pass",
                token_count=10,
            )
            for i in range(5)
        ]

        embedding_store.add_chunks(chunks)

        # Delete all chunks for this file
        deleted_count = embedding_store.delete_file("test-repo", "multi_chunk.py")

        assert deleted_count == 5
        # Verify all chunks deleted
        results = embedding_store.collection.get(where={"file_path": "multi_chunk.py"})
        assert len(results["ids"]) == 0

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

    def test_model_selection_env_var(self, temp_db_path):
        """Test that MCP_INDEXER_MODEL environment variable is respected"""
        # Set environment variable
        os.environ["MCP_INDEXER_MODEL"] = "sentence-transformers/all-MiniLM-L6-v2"

        try:
            store = EmbeddingStore(db_path=temp_db_path, collection_name="model_test")
            assert store.model_name == "sentence-transformers/all-MiniLM-L6-v2"

            # Cleanup
            store.reset()
        finally:
            # Clean up environment variable
            if "MCP_INDEXER_MODEL" in os.environ:
                del os.environ["MCP_INDEXER_MODEL"]

    def test_model_selection_parameter_override(self, temp_db_path):
        """Test that explicit model_name parameter overrides environment variable"""
        os.environ["MCP_INDEXER_MODEL"] = "sentence-transformers/all-MiniLM-L6-v2"

        try:
            store = EmbeddingStore(
                db_path=temp_db_path,
                collection_name="override_test",
                model_name="sentence-transformers/all-mpnet-base-v2",
            )
            # Parameter should override env var
            assert store.model_name == "sentence-transformers/all-mpnet-base-v2"

            # Cleanup
            store.reset()
        finally:
            if "MCP_INDEXER_MODEL" in os.environ:
                del os.environ["MCP_INDEXER_MODEL"]

    def test_default_model_selection(self, temp_db_path):
        """Test that default model is used when no override specified"""
        # Clear env var if set
        if "MCP_INDEXER_MODEL" in os.environ:
            del os.environ["MCP_INDEXER_MODEL"]

        store = EmbeddingStore(db_path=temp_db_path, collection_name="default_test")
        # Should use the new default
        assert (
            store.model_name == "sentence-transformers/multi-qa-mpnet-base-dot-v1"
        )

        # Cleanup
        store.reset()

    def test_keyword_search(self, embedding_store, sample_chunks):
        """Test keyword search functionality"""
        embedding_store.add_chunks(sample_chunks)

        # Search for exact keyword
        results = embedding_store.keyword_search("authenticate_user", n_results=5)

        assert len(results) > 0
        assert all(isinstance(r, SearchResult) for r in results)

        # Should find chunks with the keyword
        auth_results = [r for r in results if "authenticate" in r.code_text.lower()]
        assert len(auth_results) > 0

    def test_keyword_search_exact_match(self, embedding_store, sample_chunks):
        """Test keyword search finds exact matches"""
        embedding_store.add_chunks(sample_chunks)

        # Search for a specific function name that appears in chunks
        results = embedding_store.keyword_search("login")

        assert len(results) > 0
        # Should find the login function
        assert any("login" in r.code_text.lower() for r in results)

    def test_keyword_search_with_filters(self, embedding_store, sample_chunks):
        """Test keyword search with repo and language filters"""
        embedding_store.add_chunks(sample_chunks)

        # Search with repo filter
        results = embedding_store.keyword_search(
            "user", n_results=10, repo_filter=["test-repo"]
        )

        assert all(r.repo_name == "test-repo" for r in results)

        # Search with language filter
        results = embedding_store.keyword_search(
            "function", n_results=10, language_filter="javascript"
        )

        assert all(r.metadata["language"] == "javascript" for r in results)

    def test_hybrid_search(self, embedding_store, sample_chunks):
        """Test hybrid search combining semantic and keyword"""
        embedding_store.add_chunks(sample_chunks)

        # Hybrid search should work for both natural language and keywords
        results = embedding_store.hybrid_search("user authentication", n_results=5)

        assert len(results) > 0
        assert all(isinstance(r, SearchResult) for r in results)

    def test_hybrid_search_alpha_semantic(self, embedding_store, sample_chunks):
        """Test hybrid search with alpha=1.0 (pure semantic)"""
        embedding_store.add_chunks(sample_chunks)

        # With alpha=1.0, should use only semantic search
        results = embedding_store.hybrid_search(
            "authentication", n_results=5, alpha=1.0
        )

        assert len(results) > 0

    def test_hybrid_search_alpha_keyword(self, embedding_store, sample_chunks):
        """Test hybrid search with alpha=0.0 (pure keyword)"""
        embedding_store.add_chunks(sample_chunks)

        # With alpha=0.0, should use only keyword search
        # Use a term that appears in the chunks
        results = embedding_store.hybrid_search("authenticate", n_results=5, alpha=0.0)

        assert len(results) > 0

    def test_hybrid_search_alpha_balanced(self, embedding_store, sample_chunks):
        """Test hybrid search with alpha=0.5 (balanced)"""
        embedding_store.add_chunks(sample_chunks)

        # With alpha=0.5, should combine both methods
        results = embedding_store.hybrid_search(
            "authenticate user", n_results=5, alpha=0.5
        )

        assert len(results) > 0

    def test_hybrid_search_with_filters(self, embedding_store, sample_chunks):
        """Test hybrid search with repo and language filters"""
        embedding_store.add_chunks(sample_chunks)

        # Test with repo filter
        results = embedding_store.hybrid_search(
            "authentication", n_results=10, repo_filter=["test-repo"]
        )

        assert len(results) > 0
        assert all(r.repo_name == "test-repo" for r in results)

        # Test with language filter
        results = embedding_store.hybrid_search(
            "function", n_results=10, language_filter="python"
        )

        assert all(r.metadata["language"] == "python" for r in results)

    def test_keyword_index_maintained_on_delete_repo(
        self, embedding_store, sample_chunks
    ):
        """Test that keyword index is cleaned up when repo is deleted"""
        embedding_store.add_chunks(sample_chunks)

        # Verify keyword search works before deletion
        results_before = embedding_store.keyword_search("authenticate_user")
        assert len(results_before) > 0

        # Delete repo
        embedding_store.delete_repo("test-repo")

        # Keyword search should not find deleted chunks
        results_after = embedding_store.keyword_search("authenticate_user")
        # Should either be empty or not contain test-repo chunks
        for result in results_after:
            assert result.repo_name != "test-repo"

    def test_keyword_index_maintained_on_delete_file(
        self, embedding_store, sample_chunks
    ):
        """Test that keyword index is cleaned up when file is deleted"""
        embedding_store.add_chunks(sample_chunks)

        # Delete specific file
        embedding_store.delete_file("test-repo", "auth.py")

        # Keyword search should not find deleted file
        results = embedding_store.keyword_search("authenticate_user")

        # Should not find chunks from deleted file
        auth_file_results = [r for r in results if r.file_path == "auth.py"]
        assert len(auth_file_results) == 0

    def test_keyword_index_maintained_on_reset(self, embedding_store, sample_chunks):
        """Test that keyword index is cleared on reset"""
        embedding_store.add_chunks(sample_chunks)

        # Verify keyword search works before reset
        # Use a term that definitely appears in chunks
        results_before = embedding_store.keyword_search("authenticate")
        assert len(results_before) > 0

        # Reset
        embedding_store.reset()

        # Keyword search should return no results
        results_after = embedding_store.keyword_search("user")
        assert len(results_after) == 0

    def test_reciprocal_rank_fusion(self, embedding_store, sample_chunks):
        """Test RRF merging of search results"""
        embedding_store.add_chunks(sample_chunks)

        # Get results from both methods
        semantic_results = embedding_store.semantic_search("authentication", n_results=3)
        keyword_results = embedding_store.keyword_search("authentication", n_results=3)

        # Use RRF to merge
        merged = embedding_store._reciprocal_rank_fusion(
            [semantic_results, keyword_results], k=60
        )

        # Should return merged results
        assert len(merged) > 0
        # All results should have RRF scores
        assert all(hasattr(r, "score") for r in merged)
        # Results should be sorted by score descending
        scores = [r.score for r in merged]
        assert scores == sorted(scores, reverse=True)


class TestCodeTokenization:
    """Tests for code-aware tokenization"""

    def test_tokenize_simple_words(self):
        """Test tokenization of simple words"""
        tokens = tokenize_code("hello world")
        assert "hello" in tokens
        assert "world" in tokens

    def test_tokenize_snake_case(self):
        """Test snake_case splitting"""
        tokens = tokenize_code("authenticate_user")
        assert "authenticate" in tokens
        assert "user" in tokens
        assert "authenticate_user" in tokens  # Original preserved

    def test_tokenize_multiple_underscores(self):
        """Test multiple underscore splitting"""
        tokens = tokenize_code("get_user_from_database")
        assert "get" in tokens
        assert "user" in tokens
        assert "from" in tokens
        assert "database" in tokens
        assert "get_user_from_database" in tokens

    def test_tokenize_camel_case(self):
        """Test CamelCase splitting"""
        tokens = tokenize_code("getUserName")
        assert "get" in tokens
        assert "user" in tokens
        assert "name" in tokens
        assert "getusername" in tokens  # Lowercased original

    def test_tokenize_pascal_case(self):
        """Test PascalCase splitting"""
        tokens = tokenize_code("AuthService")
        assert "auth" in tokens
        assert "service" in tokens
        assert "authservice" in tokens

    def test_tokenize_with_parentheses(self):
        """Test tokenization with function call syntax"""
        tokens = tokenize_code("hash_password(")
        assert "hash" in tokens
        assert "password" in tokens
        assert "hash_password" in tokens

    def test_tokenize_with_dots(self):
        """Test tokenization with dot notation"""
        tokens = tokenize_code("user.authenticate()")
        assert "user" in tokens
        assert "authenticate" in tokens

    def test_tokenize_with_brackets(self):
        """Test tokenization with brackets"""
        tokens = tokenize_code("array[index]")
        assert "array" in tokens
        assert "index" in tokens

    def test_tokenize_mixed_cases(self):
        """Test mixed snake_case and CamelCase"""
        tokens = tokenize_code("getUserName password_hash")
        assert "get" in tokens
        assert "user" in tokens
        assert "name" in tokens
        assert "password" in tokens
        assert "hash" in tokens

    def test_tokenize_code_with_special_chars(self):
        """Test tokenization with various special characters"""
        tokens = tokenize_code("self.hash_password(user.password)")
        assert "self" in tokens
        assert "hash" in tokens
        assert "password" in tokens
        assert "user" in tokens

    def test_tokenize_preserves_lowercase(self):
        """Test that all tokens are lowercase"""
        tokens = tokenize_code("AuthService GetUserName")
        for token in tokens:
            assert token == token.lower()

    def test_tokenize_empty_string(self):
        """Test tokenization of empty string"""
        tokens = tokenize_code("")
        assert len(tokens) == 0

    def test_tokenize_whitespace_only(self):
        """Test tokenization of whitespace only"""
        tokens = tokenize_code("   \t  \n  ")
        assert len(tokens) == 0

    def test_tokenize_returns_sorted_list(self):
        """Test that tokens are returned in sorted order"""
        tokens = tokenize_code("zebra apple banana")
        assert tokens == sorted(tokens)

    def test_tokenize_removes_duplicates(self):
        """Test that duplicate tokens are removed"""
        tokens = tokenize_code("user user user")
        assert tokens.count("user") == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

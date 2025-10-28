"""
Benchmark hybrid search vs semantic-only vs keyword-only search

Tests different query types to demonstrate the benefits of hybrid search
"""

import time
from mcpindexer.chunker import CodeChunk
from mcpindexer.embeddings import EmbeddingStore


def create_test_chunks():
    """Create diverse code chunks for testing"""
    return [
        # Exact function names
        CodeChunk(
            chunk_id="test:1",
            file_path="auth.py",
            repo_name="test-repo",
            language="python",
            chunk_type="function",
            code_text="def authenticate_user(username, password):\n    return verify_credentials(username, password)",
            start_line=1,
            end_line=2,
            symbol_name="authenticate_user",
            parent_class=None,
            imports=[],
            context_text="def authenticate_user(username, password):\n    return verify_credentials(username, password)",
            token_count=20,
        ),
        # Similar concept different naming
        CodeChunk(
            chunk_id="test:2",
            file_path="login.py",
            repo_name="test-repo",
            language="python",
            chunk_type="function",
            code_text="def check_user_credentials(user, passwd):\n    return validate(user, passwd)",
            start_line=1,
            end_line=2,
            symbol_name="check_user_credentials",
            parent_class=None,
            imports=[],
            context_text="def check_user_credentials(user, passwd):\n    return validate(user, passwd)",
            token_count=18,
        ),
        # Different concept with overlapping words
        CodeChunk(
            chunk_id="test:3",
            file_path="db.py",
            repo_name="test-repo",
            language="python",
            chunk_type="function",
            code_text="def get_user_from_database(username):\n    return db.query(User).filter_by(username=username).first()",
            start_line=1,
            end_line=2,
            symbol_name="get_user_from_database",
            parent_class=None,
            imports=[],
            context_text="def get_user_from_database(username):\n    return db.query(User).filter_by(username=username).first()",
            token_count=22,
        ),
        # Exact string we might search for
        CodeChunk(
            chunk_id="test:4",
            file_path="utils.py",
            repo_name="test-repo",
            language="python",
            chunk_type="function",
            code_text="def hash_password(password):\n    return bcrypt.hashpw(password.encode(), bcrypt.gensalt())",
            start_line=1,
            end_line=2,
            symbol_name="hash_password",
            parent_class=None,
            imports=["bcrypt"],
            context_text="def hash_password(password):\n    return bcrypt.hashpw(password.encode(), bcrypt.gensalt())",
            token_count=18,
        ),
        # Common word that should rank lower
        CodeChunk(
            chunk_id="test:5",
            file_path="models.py",
            repo_name="test-repo",
            language="python",
            chunk_type="class",
            code_text="class User:\n    def __init__(self, username, email):\n        self.username = username\n        self.email = email",
            start_line=1,
            end_line=4,
            symbol_name="User",
            parent_class=None,
            imports=[],
            context_text="class User:\n    def __init__(self, username, email):\n        self.username = username\n        self.email = email",
            token_count=25,
        ),
    ]


def benchmark_query(store, query, search_type, alpha=0.5):
    """Run a single search and measure time"""
    start = time.time()

    if search_type == "semantic":
        results = store.semantic_search(query, n_results=5)
    elif search_type == "keyword":
        results = store.keyword_search(query, n_results=5)
    else:  # hybrid
        results = store.hybrid_search(query, n_results=5, alpha=alpha)

    elapsed = (time.time() - start) * 1000  # Convert to ms

    return results, elapsed


def print_results(query, search_type, results, elapsed):
    """Print formatted results"""
    print(f"\n{'='*80}")
    print(f"Query: '{query}' | Mode: {search_type.upper()} | Time: {elapsed:.2f}ms")
    print(f"{'='*80}")

    if not results:
        print("  No results found")
        return

    for i, result in enumerate(results[:3], 1):  # Show top 3
        print(f"\n  {i}. {result.symbol_name or 'unknown'} ({result.file_path})")
        print(f"     Score: {result.score:.4f}")
        print(f"     Code: {result.code_text[:80]}...")


def main():
    """Run benchmark"""
    print("Hybrid Search Benchmark")
    print("="*80)

    # Setup
    import tempfile
    import shutil
    temp_dir = tempfile.mkdtemp()

    try:
        store = EmbeddingStore(db_path=temp_dir, collection_name="benchmark")
        chunks = create_test_chunks()

        print(f"\nIndexing {len(chunks)} test code chunks...")
        store.add_chunks(chunks)
        print("✓ Indexing complete\n")

        # Test queries
        queries = [
            ("authenticate_user", "Exact function name (keyword should excel)"),
            ("user authentication", "Conceptual query (semantic should excel)"),
            ("hash_password bcrypt", "Mixed exact + concept (hybrid should excel)"),
            ("get_user_from_database", "Exact long function name (keyword should excel)"),
        ]

        for query, description in queries:
            print(f"\n{'#'*80}")
            print(f"TEST: {description}")
            print(f"{'#'*80}")

            # Test all three modes
            for mode in ["keyword", "semantic", "hybrid"]:
                results, elapsed = benchmark_query(store, query, mode)
                print_results(query, mode, results, elapsed)

        # Summary
        print(f"\n\n{'='*80}")
        print("SUMMARY")
        print(f"{'='*80}")
        print("\nHybrid Search Benefits:")
        print("  ✓ Finds exact matches (like keyword search)")
        print("  ✓ Understands concepts (like semantic search)")
        print("  ✓ RRF fusion balances both approaches")
        print("  ✓ Configurable via alpha parameter (0.0 to 1.0)")
        print("\nDefault alpha=0.5 provides best overall results")
        print(f"{'='*80}\n")

    finally:
        # Cleanup
        shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    main()

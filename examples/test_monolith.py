#!/usr/bin/env python3
"""
Test script for monolith repository indexing

Tests the indexer with larger repositories and cross-repo scenarios.
"""
import os
import sys
import time
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from mcpindexer.indexer import MultiRepoIndexer
from mcpindexer.embeddings import EmbeddingStore


def test_monolith_indexing():
    """Test indexing multiple large repositories"""
    print("=" * 80)
    print("MCP Indexer - Monolith Testing")
    print("=" * 80)

    # Initialize
    db_path = "./mcp_index_data_monolith_test"
    embedding_store = EmbeddingStore(db_path=db_path, collection_name="monolith_test")
    embedding_store.reset()  # Clean start

    indexer = MultiRepoIndexer(embedding_store=embedding_store)

    # Repos to test
    zendesk_apps_base = Path.home() / "Code" / "zendesk" / "apps"

    repos_to_index = [
        ("zendesk_app_framework", zendesk_apps_base / "zendesk_app_framework"),
        ("zendesk_app_framework_sdk", zendesk_apps_base / "zendesk_app_framework_sdk"),
        ("zendesk_apps_support", zendesk_apps_base / "zendesk_apps_support"),
    ]

    # Index each repo
    total_files = 0
    total_chunks = 0
    timings = []

    for repo_name, repo_path in repos_to_index:
        if not repo_path.exists():
            print(f"\n⚠ Skipping {repo_name} (not found at {repo_path})")
            continue

        print(f"\n{'=' * 80}")
        print(f"Indexing: {repo_name}")
        print(f"Path: {repo_path}")
        print(f"{'=' * 80}")

        start_time = time.time()

        try:
            result = indexer.add_repo(
                repo_path=str(repo_path),
                repo_name=repo_name,
                auto_index=True
            )

            elapsed = time.time() - start_time
            timings.append((repo_name, elapsed))

            print(f"\n✓ Successfully indexed {repo_name}")
            print(f"  Files processed: {result.files_processed}")
            print(f"  Files skipped: {result.files_skipped}")
            print(f"  Chunks created: {result.chunks_created}")
            print(f"  Chunks indexed: {result.chunks_indexed}")
            print(f"  Git commit: {result.git_commit[:8] if result.git_commit else 'N/A'}")
            print(f"  Time: {elapsed:.2f}s")

            if result.errors:
                print(f"  Errors: {len(result.errors)}")
                for error in result.errors[:3]:
                    print(f"    - {error}")

            total_files += result.files_processed
            total_chunks += result.chunks_indexed

        except Exception as e:
            print(f"\n✗ Error indexing {repo_name}: {e}")

    # Test cross-repo dependency detection
    print(f"\n{'=' * 80}")
    print("Cross-Repo Dependency Analysis")
    print(f"{'=' * 80}")

    cross_deps = indexer.get_cross_repo_dependencies()
    if cross_deps:
        print(f"\nFound {len(cross_deps)} cross-repo dependencies:")
        for dep in cross_deps[:10]:  # Show first 10
            print(f"  {dep['source_repo']} → {dep['target_repo']} (via {dep['package']})")
    else:
        print("\nNo cross-repo dependencies detected")

    # Test missing repo suggestions
    suggestions = indexer.suggest_missing_repos()
    if suggestions:
        print(f"\nSuggested missing repos ({len(suggestions)}):")
        for suggestion in suggestions[:10]:  # Show first 10
            print(f"  • {suggestion}")
    else:
        print("\nNo missing repos detected")

    # Test semantic search across all repos
    print(f"\n{'=' * 80}")
    print("Testing Semantic Search")
    print(f"{'=' * 80}")

    queries = [
        "event handler",
        "API request",
        "configuration",
    ]

    for query in queries:
        print(f"\nQuery: '{query}'")
        results = embedding_store.semantic_search(query=query, n_results=5)

        if results:
            for i, result in enumerate(results, 1):
                print(f"  {i}. {result.file_path} (repo: {result.repo_name}, score: {result.score:.4f})")
                if result.symbol_name:
                    print(f"     Symbol: {result.symbol_name}")
        else:
            print("  No results")

    # Summary
    print(f"\n{'=' * 80}")
    print("Summary")
    print(f"{'=' * 80}")
    print(f"\nTotal repositories indexed: {len(timings)}")
    print(f"Total files processed: {total_files}")
    print(f"Total chunks indexed: {total_chunks}")
    print(f"\nTiming breakdown:")
    for repo_name, elapsed in timings:
        print(f"  {repo_name}: {elapsed:.2f}s")

    if timings:
        total_time = sum(t for _, t in timings)
        avg_time = total_time / len(timings)
        print(f"\nTotal time: {total_time:.2f}s")
        print(f"Average time per repo: {avg_time:.2f}s")

        if total_files > 0:
            print(f"Average speed: {total_files / total_time:.2f} files/sec")

    # Stack status
    print(f"\n{'=' * 80}")
    print("Stack Status")
    print(f"{'=' * 80}")
    stats = indexer.get_stack_status()
    print(f"\nTotal repos: {stats['total_repos']}")
    print(f"Total files indexed: {stats['total_files_indexed']}")
    print(f"Total chunks indexed: {stats['total_chunks_indexed']}")
    print(f"\nStatus breakdown:")
    for status, count in stats['by_status'].items():
        if count > 0:
            print(f"  {status}: {count}")

    print(f"\n{'=' * 80}")
    print("✓ Monolith testing complete!")
    print(f"{'=' * 80}\n")


if __name__ == "__main__":
    test_monolith_indexing()

#!/usr/bin/env python3
"""
Reindex all repos to capture dependencies
"""
import os
import sys
import time
from pathlib import Path

# Note: Requires mcpindexer to be installed (pip install -e .)

from mcpindexer.indexer import MultiRepoIndexer
from mcpindexer.embeddings import EmbeddingStore
from mcpindexer.stack_config import StackConfig


def main():
    print("=" * 80)
    print("Reindexing All Repositories with Dependency Tracking")
    print("=" * 80)

    # Initialize
    db_path = os.getenv("MCP_INDEXER_DB_PATH", os.path.expanduser("~/.mcpindexer/db"))
    embedding_store = EmbeddingStore(db_path=db_path, collection_name="mcp_code_index")
    indexer = MultiRepoIndexer(embedding_store=embedding_store)

    # Load existing repos from config
    config = StackConfig()
    repos_to_index = []

    from mcpindexer.stack_config import IndexingStatus
    for repo_name, repo_config in config.repos.items():
        if repo_config.status == IndexingStatus.INDEXED:
            repos_to_index.append((repo_name, repo_config.path))

    if not repos_to_index:
        print("\n✗ No indexed repos found")
        return

    print(f"\nFound {len(repos_to_index)} repos to reindex:\n")
    for name, path in repos_to_index:
        print(f"  • {name}")
    print()

    response = input(f"This will reindex all {len(repos_to_index)} repos. Continue? (y/n): ")
    if response.lower() != 'y':
        print("Cancelled")
        return

    # Reindex each repo
    total_start = time.time()
    total_files = 0
    total_chunks = 0
    successful = 0
    failed = []

    for i, (repo_name, repo_path) in enumerate(repos_to_index, 1):
        print(f"\n[{i}/{len(repos_to_index)}] Reindexing: {repo_name}")
        print(f"Path: {repo_path}")

        start_time = time.time()

        try:
            # Remove existing
            print("  Removing old index...")
            indexer.remove_repo(repo_name)

            # Reindex
            print("  Indexing with dependency tracking...")
            result = indexer.add_repo(
                repo_path=repo_path,
                repo_name=repo_name,
                auto_index=True
            )

            elapsed = time.time() - start_time

            print(f"  ✓ Indexed in {elapsed:.2f}s")
            print(f"    Files: {result.files_processed}, Chunks: {result.chunks_indexed}")

            # Check if dependencies were saved
            deps = indexer.dependency_storage.get_repo_dependencies(repo_name)
            if deps:
                external_count = len(deps.get('external_packages', []))
                cross_count = len(deps.get('cross_repo_deps', []))
                print(f"    Dependencies: {external_count} external, {cross_count} cross-repo")

            if result.errors:
                print(f"    Warnings: {len(result.errors)} errors")

            total_files += result.files_processed
            total_chunks += result.chunks_indexed
            successful += 1

        except Exception as e:
            elapsed = time.time() - start_time
            print(f"  ✗ Failed after {elapsed:.2f}s: {e}")
            failed.append((repo_name, str(e)))

    # Summary
    total_elapsed = time.time() - total_start
    print("\n" + "=" * 80)
    print("Summary")
    print("=" * 80)
    print(f"\nTotal time: {total_elapsed:.2f}s ({total_elapsed/60:.1f} minutes)")
    print(f"Successfully reindexed: {successful}/{len(repos_to_index)} repositories")
    print(f"Total files processed: {total_files}")
    print(f"Total chunks indexed: {total_chunks}")

    if failed:
        print(f"\nFailed repositories ({len(failed)}):")
        for name, error in failed:
            print(f"  • {name}: {error}")

    # Show dependency stats
    print("\n" + "=" * 80)
    print("Dependency Statistics")
    print("=" * 80)

    dep_stats = indexer.dependency_storage.get_stats()
    print(f"\nRepos with dependencies tracked: {dep_stats['total_repos_with_deps']}")
    print(f"Cross-repo dependencies found: {dep_stats['total_cross_repo_deps']}")
    print(f"Unique packages: {dep_stats['total_unique_packages']}")

    if dep_stats['unique_packages']:
        print("\nPackages found:")
        for pkg in dep_stats['unique_packages'][:20]:
            print(f"  • {pkg}")
        if len(dep_stats['unique_packages']) > 20:
            print(f"  ... and {len(dep_stats['unique_packages']) - 20} more")

    # Show cross-repo dependencies
    cross_deps = indexer.get_cross_repo_dependencies()
    if cross_deps:
        print("\n" + "=" * 80)
        print("Cross-Repository Dependencies")
        print("=" * 80)
        print(f"\nFound {len(cross_deps)} cross-repo dependencies:\n")
        for dep in cross_deps:
            print(f"  {dep['source_repo']} → {dep['target_repo']}")
            print(f"    via: {dep['package']}")
    else:
        print("\nNo cross-repo dependencies detected")

    print("\n✓ Reindexing complete!")
    print()


if __name__ == "__main__":
    main()

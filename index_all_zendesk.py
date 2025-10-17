#!/usr/bin/env python3
"""
Index all Zendesk repositories
"""
import os
import sys
import time
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from mcpindexer.indexer import MultiRepoIndexer
from mcpindexer.embeddings import EmbeddingStore


def main():
    print("=" * 80)
    print("Indexing All Zendesk Repositories")
    print("=" * 80)

    # Initialize
    db_path = os.getenv("MCP_INDEXER_DB_PATH", "/Users/gkatechis/.mcpindexer/db")
    embedding_store = EmbeddingStore(db_path=db_path, collection_name="mcp_code_index")
    indexer = MultiRepoIndexer(embedding_store=embedding_store)

    # Find all git repos
    zendesk_base = Path.home() / "Code" / "zendesk"

    repos_to_index = []
    for git_dir in zendesk_base.rglob(".git"):
        if git_dir.is_dir():
            repo_path = git_dir.parent
            repo_name = repo_path.name

            # Skip if already indexed
            existing_repos = indexer.list_repos()
            if repo_name not in existing_repos:
                repos_to_index.append((repo_name, repo_path))

    if not repos_to_index:
        print("\n✓ All repositories are already indexed!")
        print("\nUse 'python3 -m mcpindexer status' to see current status")
        return

    print(f"\nFound {len(repos_to_index)} new repositories to index:")
    for name, path in repos_to_index:
        print(f"  • {name}")
    print()

    # Index each repo
    total_files = 0
    total_chunks = 0
    successful = 0
    failed = []

    for i, (repo_name, repo_path) in enumerate(repos_to_index, 1):
        print(f"\n[{i}/{len(repos_to_index)}] Indexing: {repo_name}")
        print(f"Path: {repo_path}")

        start_time = time.time()

        try:
            result = indexer.add_repo(
                repo_path=str(repo_path),
                repo_name=repo_name,
                auto_index=True
            )

            elapsed = time.time() - start_time

            print(f"✓ Indexed in {elapsed:.2f}s")
            print(f"  Files: {result.files_processed}, Chunks: {result.chunks_indexed}")

            if result.errors:
                print(f"  Warnings: {len(result.errors)} errors")

            total_files += result.files_processed
            total_chunks += result.chunks_indexed
            successful += 1

        except Exception as e:
            elapsed = time.time() - start_time
            print(f"✗ Failed after {elapsed:.2f}s: {e}")
            failed.append((repo_name, str(e)))

    # Summary
    print("\n" + "=" * 80)
    print("Summary")
    print("=" * 80)
    print(f"\nSuccessfully indexed: {successful}/{len(repos_to_index)} repositories")
    print(f"Total files processed: {total_files}")
    print(f"Total chunks indexed: {total_chunks}")

    if failed:
        print(f"\nFailed repositories ({len(failed)}):")
        for name, error in failed:
            print(f"  • {name}: {error}")

    # Show final stack status
    print("\n" + "=" * 80)
    print("Final Stack Status")
    print("=" * 80)
    stats = indexer.get_stack_status()
    print(f"\nTotal repos: {stats['total_repos']}")
    print(f"Total files: {stats['total_files_indexed']}")
    print(f"Total chunks: {stats['total_chunks_indexed']}")

    print("\n✓ Indexing complete!")
    print("\nYou can now use these tools in Claude Code:")
    print("  - semantic_search")
    print("  - find_definition")
    print("  - get_cross_repo_dependencies")
    print("  - suggest_missing_repos")
    print()


if __name__ == "__main__":
    main()

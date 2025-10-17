#!/usr/bin/env python3
"""
Reindex the Zendesk monolith with fixed batching
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
    print("Reindexing Zendesk Monolith")
    print("=" * 80)

    # Initialize
    db_path = os.getenv("MCP_INDEXER_DB_PATH", "/Users/gkatechis/.mcpindexer/db")
    embedding_store = EmbeddingStore(db_path=db_path, collection_name="mcp_code_index")
    indexer = MultiRepoIndexer(embedding_store=embedding_store)

    repo_name = "zendesk"
    repo_path = "/Users/gkatechis/Code/zendesk/zendesk"

    print(f"\nRepo: {repo_name}")
    print(f"Path: {repo_path}")
    print("\nRemoving existing index...")

    # Remove existing index
    chunks_deleted = indexer.remove_repo(repo_name)
    print(f"✓ Deleted {chunks_deleted} chunks")

    print("\nReindexing with batched chunk addition...")
    print("This may take several minutes for a large repo...")
    print()

    start_time = time.time()

    try:
        result = indexer.add_repo(
            repo_path=repo_path,
            repo_name=repo_name,
            auto_index=True
        )

        elapsed = time.time() - start_time

        print("\n" + "=" * 80)
        print("Success!")
        print("=" * 80)
        print(f"\nIndexed in {elapsed:.2f}s ({elapsed/60:.1f} minutes)")
        print(f"Files processed: {result.files_processed}")
        print(f"Chunks created: {result.chunks_created}")
        print(f"Chunks indexed: {result.chunks_indexed}")

        if result.errors:
            print(f"\nWarnings ({len(result.errors)} errors):")
            for error in result.errors[:5]:  # Show first 5
                print(f"  • {error}")
            if len(result.errors) > 5:
                print(f"  ... and {len(result.errors) - 5} more")

    except Exception as e:
        elapsed = time.time() - start_time
        print(f"\n✗ Failed after {elapsed:.2f}s: {e}")
        raise

    # Show final status
    print("\n" + "=" * 80)
    print("Final Stack Status")
    print("=" * 80)
    stats = indexer.get_stack_status()
    print(f"\nTotal repos: {stats['total_repos']}")
    print(f"Total files: {stats['total_files_indexed']}")
    print(f"Total chunks: {stats['total_chunks_indexed']}")
    print()


if __name__ == "__main__":
    main()

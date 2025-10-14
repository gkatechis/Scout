#!/usr/bin/env python3
"""
Test the indexer with real Zendesk repos
"""
import sys
from pathlib import Path
import tempfile
import shutil

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from mcpindexer.parser import CodeParser
from mcpindexer.chunker import CodeChunker
from mcpindexer.embeddings import EmbeddingStore


def scan_repo(repo_path: Path, repo_name: str, parser: CodeParser, chunker: CodeChunker):
    """Scan a repository and return chunks"""
    all_chunks = []
    files_processed = 0
    files_skipped = 0

    # File extensions we support
    extensions = {'.py', '.js', '.mjs', '.cjs', '.ts', '.tsx', '.rb', '.go'}

    print(f"\nScanning {repo_name}...")

    for file_path in repo_path.rglob('*'):
        # Skip directories and non-code files
        if not file_path.is_file():
            continue

        if file_path.suffix not in extensions:
            continue

        # Skip large vendor/node_modules directories
        if any(part in file_path.parts for part in ['node_modules', 'vendor', 'dist', 'build']):
            continue

        try:
            # Parse the file
            parsed = parser.parse_file(str(file_path))
            if not parsed:
                files_skipped += 1
                continue

            # Chunk it
            chunks = chunker.chunk_file(parsed)
            all_chunks.extend(chunks)
            files_processed += 1

            if files_processed % 10 == 0:
                print(f"  Processed {files_processed} files, {len(all_chunks)} chunks so far...")

        except Exception as e:
            files_skipped += 1
            if files_processed < 5:  # Show first few errors
                print(f"  Skipped {file_path.name}: {str(e)[:50]}")

    print(f"\n✓ Processed {files_processed} files")
    print(f"  Skipped {files_skipped} files")
    print(f"  Created {len(all_chunks)} chunks")

    return all_chunks


def main():
    # Configuration
    REPOS_BASE = Path.home() / "Code" / "zendesk" / "apps"
    REPO_NAME = "zendesk_app_framework"
    REPO_PATH = REPOS_BASE / REPO_NAME

    if not REPO_PATH.exists():
        print(f"Error: Repository not found at {REPO_PATH}")
        return

    print("=" * 70)
    print("  MCP Indexer - Real Repository Test")
    print("=" * 70)
    print(f"\nRepository: {REPO_NAME}")
    print(f"Path: {REPO_PATH}")

    # Create temporary database
    temp_dir = tempfile.mkdtemp()
    print(f"Database: {temp_dir}")

    try:
        # Initialize components
        print("\n" + "=" * 70)
        print("  Initializing Components")
        print("=" * 70)

        parser = CodeParser()
        chunker = CodeChunker(repo_name=REPO_NAME)
        store = EmbeddingStore(db_path=temp_dir, collection_name="zendesk_test")
        print("✓ Parser, Chunker, and EmbeddingStore initialized")

        # Scan and index the repository
        print("\n" + "=" * 70)
        print("  Scanning Repository")
        print("=" * 70)

        chunks = scan_repo(REPO_PATH, REPO_NAME, parser, chunker)

        if not chunks:
            print("No chunks created. Exiting.")
            return

        # Index chunks
        print("\n" + "=" * 70)
        print("  Indexing Code")
        print("=" * 70)
        print(f"Generating embeddings for {len(chunks)} chunks...")
        print("(This may take a minute or two...)")

        store.add_chunks(chunks)
        print(f"✓ Indexed {len(chunks)} chunks")

        # Get stats
        stats = store.get_repo_stats(REPO_NAME)
        print(f"\nRepository Statistics:")
        print(f"  Total chunks: {stats['chunk_count']}")
        print(f"  Files indexed: {len(stats['files'])}")
        print(f"  Languages: {', '.join(stats['languages'])}")
        print(f"  Sample files:")
        for f in stats['files'][:5]:
            print(f"    - {f}")
        if len(stats['files']) > 5:
            print(f"    ... and {len(stats['files']) - 5} more")

        # Interactive search
        print("\n" + "=" * 70)
        print("  Interactive Search")
        print("=" * 70)
        print("\nTry some searches! (or 'quit' to exit)\n")

        sample_queries = [
            "app initialization and setup",
            "event handling",
            "API requests and responses",
            "iframe communication",
        ]

        print("Sample queries:")
        for i, q in enumerate(sample_queries, 1):
            print(f"  {i}. {q}")
        print()

        while True:
            try:
                query = input("Search query: ").strip()

                if query.lower() in ['quit', 'exit', 'q']:
                    break

                if not query:
                    continue

                # Check if it's a number (sample query)
                if query.isdigit():
                    idx = int(query) - 1
                    if 0 <= idx < len(sample_queries):
                        query = sample_queries[idx]
                        print(f"Using: {query}")
                    else:
                        print("Invalid sample number")
                        continue

                # Perform search
                results = store.semantic_search(query, n_results=5)

                if not results:
                    print("No results found.\n")
                    continue

                print(f"\nFound {len(results)} results:\n")

                for i, result in enumerate(results, 1):
                    print(f"{i}. {result.file_path}")
                    if result.symbol_name:
                        print(f"   Symbol: {result.symbol_name}")
                    print(f"   Score: {result.score:.4f}")
                    print(f"   Lines: {result.metadata.get('start_line', '?')}-{result.metadata.get('end_line', '?')}")

                    # Show code preview
                    preview = result.code_text[:150].replace('\n', ' ')
                    if len(result.code_text) > 150:
                        preview += "..."
                    print(f"   Preview: {preview}")
                    print()

            except KeyboardInterrupt:
                print("\n\nExiting...")
                break
            except Exception as e:
                print(f"Error: {e}\n")

    finally:
        # Cleanup
        print("\nCleaning up...")
        shutil.rmtree(temp_dir, ignore_errors=True)
        print("Done!")


if __name__ == "__main__":
    main()

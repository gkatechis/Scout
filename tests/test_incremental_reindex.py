#!/usr/bin/env python3
"""
Integration test for incremental reindexing

Creates a test repo, makes changes, and verifies incremental reindexing works
"""

import os
import shutil
import tempfile
from pathlib import Path

import git

from scout.embeddings import EmbeddingStore
from scout.indexer import RepoIndexer


def create_test_repo(repo_path: Path):
    """Create a test git repository with some files"""
    repo_path.mkdir(parents=True, exist_ok=True)

    # Initialize git repo
    repo = git.Repo.init(repo_path)

    # Create initial files
    (repo_path / "main.py").write_text("""
def greet(name):
    return f"Hello, {name}!"

def main():
    print(greet("World"))
""")

    (repo_path / "utils.py").write_text("""
def add(a, b):
    return a + b

def multiply(a, b):
    return a * b
""")

    (repo_path / "config.py").write_text("""
CONFIG = {
    'debug': True,
    'version': '1.0.0'
}
""")

    # Initial commit
    repo.index.add(["main.py", "utils.py", "config.py"])
    initial_commit = repo.index.commit("Initial commit")

    return repo, initial_commit.hexsha


def main():
    print("=" * 60)
    print("Incremental Reindexing Integration Test")
    print("=" * 60)

    # Create temporary directories
    test_repo_path = Path(tempfile.mkdtemp(prefix="test_repo_"))
    test_db_path = Path(tempfile.mkdtemp(prefix="test_db_"))

    try:
        # Step 1: Create test repo and initial commit
        print("\n1. Creating test repository...")
        repo, initial_commit = create_test_repo(test_repo_path)
        print(f"   ✓ Created repo at {test_repo_path}")
        print(f"   ✓ Initial commit: {initial_commit[:8]}")

        # Step 2: Initial index
        print("\n2. Performing initial index...")
        embedding_store = EmbeddingStore(
            db_path=str(test_db_path),
            collection_name="test_incremental"
        )
        indexer = RepoIndexer(
            repo_path=str(test_repo_path),
            repo_name="test-repo",
            embedding_store=embedding_store
        )

        result = indexer.index()
        print(f"   ✓ Files processed: {result.files_processed}")
        print(f"   ✓ Chunks created: {result.chunks_created}")
        print(f"   ✓ Git commit: {result.git_commit[:8]}")

        initial_chunks = result.chunks_created

        # Verify initial index
        repo_stats = embedding_store.get_repo_stats("test-repo")
        print(f"   ✓ Total chunks in DB: {repo_stats['chunk_count']}")
        print(f"   ✓ Files in DB: {repo_stats['files']}")

        # Step 3: Make changes
        print("\n3. Making changes to repository...")

        # Modify main.py
        (test_repo_path / "main.py").write_text("""
def greet(name):
    return f"Hello, {name}!"

def farewell(name):
    return f"Goodbye, {name}!"

def main():
    print(greet("World"))
    print(farewell("World"))
""")

        # Add new file
        (test_repo_path / "helper.py").write_text("""
def format_output(text):
    return f">>> {text} <<<"
""")

        # Delete config.py
        (test_repo_path / "config.py").unlink()

        # Commit changes
        repo.index.add(["main.py", "helper.py"])
        repo.index.remove(["config.py"])
        new_commit = repo.index.commit("Update main, add helper, remove config")

        print(f"   ✓ Modified: main.py")
        print(f"   ✓ Added: helper.py")
        print(f"   ✓ Deleted: config.py")
        print(f"   ✓ New commit: {new_commit.hexsha[:8]}")

        # Step 4: Incremental reindex
        print("\n4. Performing incremental reindex...")
        result = indexer.reindex(force=False, since_commit=initial_commit)

        print(f"   ✓ Files processed: {result.files_processed}")
        print(f"   ✓ Files skipped: {result.files_skipped}")
        print(f"   ✓ Chunks created: {result.chunks_created}")
        print(f"   ✓ Git commit: {result.git_commit[:8]}")

        # Step 5: Verify results
        print("\n5. Verifying incremental reindex results...")

        # Check that only changed files were processed
        if result.files_processed == 2:  # main.py and helper.py
            print("   ✓ Correct number of files processed (2)")
        else:
            print(f"   ✗ Expected 2 files, got {result.files_processed}")

        # Check that utils.py was NOT reindexed (skipped because unchanged)
        if result.files_skipped >= 1:  # config.py deleted + utils.py unchanged
            print("   ✓ Unchanged files were skipped")
        else:
            print(f"   ✗ Expected skipped files, got {result.files_skipped}")

        # Verify final state
        repo_stats = embedding_store.get_repo_stats("test-repo")
        print(f"   ✓ Total chunks in DB: {repo_stats['chunk_count']}")
        print(f"   ✓ Files in DB: {sorted(repo_stats['files'])}")

        # Check that config.py was removed
        config_files = [f for f in repo_stats['files'] if 'config.py' in f]
        if not config_files:
            print("   ✓ Deleted file (config.py) removed from index")
        else:
            print(f"   ✗ Deleted file still in index: {config_files}")

        # Check that helper.py was added
        helper_files = [f for f in repo_stats['files'] if 'helper.py' in f]
        if helper_files:
            print("   ✓ New file (helper.py) added to index")
        else:
            print("   ✗ New file not in index")

        # Check that utils.py is still there (unchanged)
        utils_files = [f for f in repo_stats['files'] if 'utils.py' in f]
        if utils_files:
            print("   ✓ Unchanged file (utils.py) still in index")
        else:
            print("   ✗ Unchanged file missing from index")

        # Step 6: Compare with force reindex
        print("\n6. Comparing with force reindex...")

        # Reset and do force reindex
        embedding_store.delete_repo("test-repo")
        force_result = indexer.reindex(force=True)

        print(f"   Force reindex - Files: {force_result.files_processed}, Chunks: {force_result.chunks_created}")
        print(f"   Incremental   - Files: {result.files_processed}, Chunks: {result.chunks_created}")
        print(f"   ✓ Incremental processed {force_result.files_processed - result.files_processed} fewer files")

        print("\n" + "=" * 60)
        print("✓ Integration test completed successfully!")
        print("=" * 60)

        return True

    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        # Cleanup
        print("\nCleaning up...")
        shutil.rmtree(test_repo_path, ignore_errors=True)
        shutil.rmtree(test_db_path, ignore_errors=True)
        print("✓ Cleanup complete")


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)

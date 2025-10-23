"""
CLI for MCP Indexer

Provides commands for managing the repository stack and triggering reindexing.
"""
import os
import sys
import argparse
import subprocess
import re
from pathlib import Path
from mcpindexer.indexer import MultiRepoIndexer, RepoIndexer
from mcpindexer.embeddings import EmbeddingStore
from mcpindexer.stack_config import StackConfig, IndexingStatus


def get_indexer():
    """Get or create the multi-repo indexer"""
    db_path = os.getenv("MCP_INDEXER_DB_PATH", "./mcp_index_data")
    embedding_store = EmbeddingStore(
        db_path=db_path,
        collection_name="mcp_code_index"
    )
    return MultiRepoIndexer(embedding_store=embedding_store)


def cmd_add(args):
    """Add a repository to the index (local path or GitHub URL)"""
    source = args.source
    name = args.name
    clone_dir = args.clone_dir or os.path.expanduser("~/Code")

    # Determine if source is a URL or local path
    is_url = source.startswith(('http://', 'https://', 'git@', 'git://'))

    if is_url:
        # Extract repo name from URL if not provided
        if not name:
            # Extract from URL: https://github.com/user/repo.git -> repo
            match = re.search(r'/([^/]+?)(\.git)?$', source)
            if match:
                name = match.group(1)
            else:
                print("Error: Could not extract repo name from URL. Please provide --name")
                return 1

        # Clone the repository
        repo_path = Path(clone_dir) / name

        if repo_path.exists():
            print(f"Error: Directory already exists: {repo_path}")
            print("Use a different --name or remove the existing directory")
            return 1

        print(f"Cloning {source} to {repo_path}...")
        try:
            subprocess.run(['git', 'clone', source, str(repo_path)], check=True)
            print(f"✓ Cloned successfully")
        except subprocess.CalledProcessError as e:
            print(f"Error: Failed to clone repository: {e}")
            return 1
    else:
        # Local path
        repo_path = Path(source).resolve()

        if not repo_path.exists():
            print(f"Error: Path does not exist: {repo_path}")
            return 1

        if not (repo_path / ".git").exists():
            print(f"Warning: Not a git repository: {repo_path}")
            print("Proceeding anyway...")

        # Extract repo name from path if not provided
        if not name:
            name = repo_path.name

    # Index the repository
    print(f"\nIndexing repository '{name}' at {repo_path}...")

    indexer = get_indexer()

    try:
        indexer.add_repo(
            repo_path=str(repo_path),
            repo_name=name,
            auto_index=True
        )

        # Get stats from stack config
        repo_config = indexer.stack_config.get_repo(name)
        if repo_config:
            print(f"✓ Successfully indexed '{name}'")
            print(f"  Files: {repo_config.files_indexed}")
            print(f"  Chunks: {repo_config.chunks_indexed}")
        else:
            print(f"✓ Successfully added '{name}'")

        return 0

    except Exception as e:
        print(f"Error: Failed to index repository: {e}")
        return 1


def cmd_check_updates(args):
    """Check for repos that need reindexing"""
    indexer = get_indexer()

    needs_update = []

    for repo_name, repo_indexer in indexer.repo_indexers.items():
        # Get current commit
        current_commit = repo_indexer._get_git_commit()

        if indexer.stack_config.needs_reindex(repo_name, current_commit or ""):
            repo_config = indexer.stack_config.get_repo(repo_name)
            needs_update.append({
                "name": repo_name,
                "path": repo_config.path if repo_config else "?",
                "old_commit": repo_config.last_commit if repo_config else None,
                "new_commit": current_commit
            })

    if not needs_update:
        print("All repositories are up to date.")
        return 0

    print(f"Found {len(needs_update)} repository(ies) needing reindex:\n")
    for repo in needs_update:
        print(f"  • {repo['name']}")
        print(f"    Path: {repo['path']}")
        print(f"    Old commit: {repo['old_commit'] or 'never indexed'}")
        print(f"    New commit: {repo['new_commit']}\n")

    return len(needs_update)


def cmd_reindex_changed(args):
    """Reindex repositories that have changed"""
    indexer = get_indexer()

    reindexed = []
    errors = []

    for repo_name, repo_indexer in indexer.repo_indexers.items():
        # Get current commit
        current_commit = repo_indexer._get_git_commit()

        if indexer.stack_config.needs_reindex(repo_name, current_commit or ""):
            print(f"Reindexing {repo_name}...")

            try:
                # Update status to indexing
                indexer.stack_config.update_repo_status(repo_name, IndexingStatus.INDEXING)

                # Reindex
                result = repo_indexer.reindex(force=True)

                # Update status
                indexer.stack_config.update_repo_status(
                    repo_name,
                    IndexingStatus.INDEXED,
                    last_commit=result.git_commit,
                    files_indexed=result.files_processed,
                    chunks_indexed=result.chunks_indexed
                )

                reindexed.append({
                    "name": repo_name,
                    "files": result.files_processed,
                    "chunks": result.chunks_indexed
                })

                print(f"  ✓ Indexed {result.files_processed} files, {result.chunks_indexed} chunks\n")

            except Exception as e:
                errors.append({"name": repo_name, "error": str(e)})

                # Update status to error
                indexer.stack_config.update_repo_status(
                    repo_name,
                    IndexingStatus.ERROR,
                    error_message=str(e)
                )

                print(f"  ✗ Error: {str(e)}\n")

    # Print summary
    if reindexed:
        print(f"\nSuccessfully reindexed {len(reindexed)} repository(ies)")

    if errors:
        print(f"\nFailed to reindex {len(errors)} repository(ies)")
        return 1

    if not reindexed and not errors:
        print("All repositories are up to date.")

    return 0


def cmd_install_hook(args):
    """Install git post-merge hook in a repository"""
    repo_path = Path(args.repo_path).resolve()

    if not repo_path.exists():
        print(f"Error: Repository path does not exist: {repo_path}")
        return 1

    git_dir = repo_path / ".git"
    if not git_dir.exists():
        print(f"Error: Not a git repository: {repo_path}")
        return 1

    hooks_dir = git_dir / "hooks"
    hooks_dir.mkdir(exist_ok=True)

    hook_path = hooks_dir / "post-merge"

    # Check if hook already exists
    if hook_path.exists() and not args.force:
        print(f"Error: Hook already exists at {hook_path}")
        print("Use --force to overwrite")
        return 1

    # Create hook script
    hook_script = """#!/bin/sh
# MCP Indexer post-merge hook
# Automatically reindex when pulling changes

echo "Checking for indexing updates..."
python3 -m mcpindexer.cli reindex-changed

exit 0
"""

    hook_path.write_text(hook_script)
    hook_path.chmod(0o755)  # Make executable

    print(f"✓ Installed post-merge hook at {hook_path}")
    print(f"\nThe repository will now automatically reindex after git pull.")

    return 0


def cmd_status(args):
    """Show stack status"""
    indexer = get_indexer()
    stats = indexer.get_stack_status()

    print("Repository Stack Status:\n")
    print(f"  Total Repositories: {stats['total_repos']}")
    print(f"  Total Files Indexed: {stats['total_files_indexed']}")
    print(f"  Total Chunks Indexed: {stats['total_chunks_indexed']}\n")

    print("  Status Breakdown:")
    for status, count in stats['by_status'].items():
        if count > 0:
            print(f"    {status}: {count}")

    return 0


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="MCP Indexer CLI - Manage repository indexing"
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # add command
    parser_add = subparsers.add_parser(
        "add",
        help="Add a repository to index (local path or GitHub URL)"
    )
    parser_add.add_argument("source", help="GitHub URL or local path to repository")
    parser_add.add_argument("--name", help="Name for the repository (auto-detected if not provided)")
    parser_add.add_argument("--clone-dir", help="Directory to clone into (default: ~/Code)")
    parser_add.set_defaults(func=cmd_add)

    # check-updates command
    parser_check = subparsers.add_parser(
        "check-updates",
        help="Check which repositories need reindexing"
    )
    parser_check.set_defaults(func=cmd_check_updates)

    # reindex-changed command
    parser_reindex = subparsers.add_parser(
        "reindex-changed",
        help="Reindex repositories that have changed"
    )
    parser_reindex.set_defaults(func=cmd_reindex_changed)

    # install-hook command
    parser_hook = subparsers.add_parser(
        "install-hook",
        help="Install git post-merge hook in a repository"
    )
    parser_hook.add_argument("repo_path", help="Path to git repository")
    parser_hook.add_argument("--force", action="store_true", help="Overwrite existing hook")
    parser_hook.set_defaults(func=cmd_install_hook)

    # status command
    parser_status = subparsers.add_parser(
        "status",
        help="Show stack status"
    )
    parser_status.set_defaults(func=cmd_status)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())

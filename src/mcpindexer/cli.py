"""
CLI for MCP Indexer

Provides commands for managing the repository stack and triggering reindexing.
"""

import argparse
import logging
import os
import re
import subprocess
import sys
from pathlib import Path

from mcpindexer.embeddings import EmbeddingStore
from mcpindexer.indexer import MultiRepoIndexer, RepoIndexer
from mcpindexer.stack_config import IndexingStatus, StackConfig

# Global logger
logger = logging.getLogger(__name__)


def setup_logging(verbose=False, debug=False):
    """Configure logging based on verbosity flags"""
    if debug:
        level = logging.DEBUG
        log_format = "%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s"
    elif verbose:
        level = logging.INFO
        log_format = "%(asctime)s - %(levelname)s - %(message)s"
    else:
        level = logging.WARNING
        log_format = "%(levelname)s - %(message)s"

    # Configure root logger
    logging.basicConfig(
        level=level, format=log_format, handlers=[logging.StreamHandler(sys.stderr)]
    )

    # Also log to file if debug mode
    if debug:
        log_dir = os.path.expanduser("~/.mcpindexer/logs")
        os.makedirs(log_dir, exist_ok=True)
        log_file = os.path.join(log_dir, "mcpindexer.log")
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(logging.Formatter(log_format))
        logging.getLogger().addHandler(file_handler)
        logger.debug(f"Debug logging enabled. Logs: {log_file}")


def get_indexer():
    """Get or create the multi-repo indexer"""
    db_path = os.getenv("MCP_INDEXER_DB_PATH", os.path.expanduser("~/.mcpindexer/db"))
    embedding_store = EmbeddingStore(db_path=db_path, collection_name="mcp_code_index")
    return MultiRepoIndexer(embedding_store=embedding_store)


def cmd_add(args):
    """Add a repository to the index (local path or GitHub URL)"""
    source = args.source
    name = args.name
    clone_dir = args.clone_dir or os.path.expanduser("~/Code")

    logger.info(f"Adding repository from source: {source}")
    logger.debug(f"Clone directory: {clone_dir}, Name: {name}")

    # Determine if source is a URL or local path
    is_url = source.startswith(("http://", "https://", "git@", "git://"))
    logger.debug(f"Source is URL: {is_url}")

    if is_url:
        # Extract repo name from URL if not provided
        if not name:
            # Extract from URL: https://github.com/user/repo.git -> repo
            match = re.search(r"/([^/]+?)(\.git)?$", source)
            if match:
                name = match.group(1)
                logger.info(f"Extracted repo name from URL: {name}")
            else:
                logger.error("Could not extract repo name from URL")
                print(
                    "Error: Could not extract repo name from URL. Please provide --name"
                )
                print("\nExample:")
                print(f"  mcpindexer add {source} --name my-repo-name")
                return 1

        # Clone the repository
        repo_path = Path(clone_dir) / name
        logger.debug(f"Target clone path: {repo_path}")

        if repo_path.exists():
            logger.error(f"Directory already exists: {repo_path}")
            print(f"Error: Directory already exists: {repo_path}")
            print("Use a different --name or remove the existing directory")
            return 1

        print(f"Cloning {source} to {repo_path}...")
        logger.info(f"Starting git clone: {source} -> {repo_path}")
        try:
            subprocess.run(["git", "clone", source, str(repo_path)], check=True)
            print(f"✓ Cloned successfully")
            logger.info("Git clone completed successfully")
        except subprocess.CalledProcessError as e:
            # Cleanup partial clone if it exists
            if repo_path.exists():
                import shutil

                try:
                    shutil.rmtree(repo_path)
                    print(f"Cleaned up partial clone at {repo_path}")
                except Exception as cleanup_error:
                    print(f"Warning: Could not cleanup {repo_path}: {cleanup_error}")

            print(f"Error: Failed to clone repository: {e}")
            print("\nTroubleshooting:")
            print("  - Verify the URL is correct and accessible")
            print("  - Check your network connection")
            print("  - Ensure git is installed: git --version")
            print("  - For private repos: check SSH keys or credentials")
            print("  - Try cloning manually: git clone <url>")
            return 1
    else:
        # Local path
        repo_path = Path(source).resolve()
        logger.info(f"Using local repository path: {repo_path}")

        if not repo_path.exists():
            logger.error(f"Path does not exist: {repo_path}")
            print(f"Error: Path does not exist: {repo_path}")
            print("\nSuggestions:")
            print(f"  - Check the path is correct: ls {repo_path.parent}")
            print("  - Use absolute path or ensure relative path is correct")
            print(f"  - Current directory: {Path.cwd()}")
            return 1

        if not (repo_path / ".git").exists():
            logger.warning(f"Not a git repository: {repo_path}")
            print(f"Warning: Not a git repository: {repo_path}")
            print("Proceeding anyway...")

        # Extract repo name from path if not provided
        if not name:
            name = repo_path.name
            logger.info(f"Extracted repo name from path: {name}")

    # Index the repository
    print(f"\nIndexing repository '{name}' at {repo_path}...")
    logger.info(f"Starting indexing for '{name}' at {repo_path}")

    indexer = get_indexer()

    try:
        logger.debug("Calling indexer.add_repo()")
        indexer.add_repo(repo_path=str(repo_path), repo_name=name, auto_index=True)
        logger.info(f"Indexing completed successfully for '{name}'")

        # Get stats from stack config
        repo_config = indexer.stack_config.get_repo(name)
        if repo_config:
            logger.debug(
                f"Stats: {repo_config.files_indexed} files, {repo_config.chunks_indexed} chunks"
            )
            print(f"✓ Successfully indexed '{name}'")
            print(f"  Files: {repo_config.files_indexed}")
            print(f"  Chunks: {repo_config.chunks_indexed}")
        else:
            print(f"✓ Successfully added '{name}'")

        return 0

    except Exception as e:
        logger.error(f"Failed to index repository: {e}", exc_info=True)
        print(f"Error: Failed to index repository: {e}")
        print("\nTroubleshooting:")
        print("  - Ensure repository path exists and is readable")
        print("  - Check disk space (indexing creates embeddings)")
        print("  - For git repos: verify git is installed")
        print("  - Try: mcpindexer check  # Verify installation")
        print("  - Check logs for more details: ~/.mcpindexer/logs/mcpindexer.log")
        print("  - Run with --debug flag for detailed logging")
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
            needs_update.append(
                {
                    "name": repo_name,
                    "path": repo_config.path if repo_config else "?",
                    "old_commit": repo_config.last_commit if repo_config else None,
                    "new_commit": current_commit,
                }
            )

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
                indexer.stack_config.update_repo_status(
                    repo_name, IndexingStatus.INDEXING
                )

                # Reindex
                result = repo_indexer.reindex(force=True)

                # Update status
                indexer.stack_config.update_repo_status(
                    repo_name,
                    IndexingStatus.INDEXED,
                    last_commit=result.git_commit,
                    files_indexed=result.files_processed,
                    chunks_indexed=result.chunks_indexed,
                )

                reindexed.append(
                    {
                        "name": repo_name,
                        "files": result.files_processed,
                        "chunks": result.chunks_indexed,
                    }
                )

                print(
                    f"  ✓ Indexed {result.files_processed} files, {result.chunks_indexed} chunks\n"
                )

            except Exception as e:
                errors.append({"name": repo_name, "error": str(e)})

                # Update status to error
                indexer.stack_config.update_repo_status(
                    repo_name, IndexingStatus.ERROR, error_message=str(e)
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
    print(f"  Total Chunks Indexed: {stats['total_chunks_indexed']}")
    print(f"  Database: {indexer.embedding_store.db_path}\n")

    print("  Status Breakdown:")
    for status, count in stats["by_status"].items():
        if count > 0:
            print(f"    {status}: {count}")

    # Check for stuck indexing
    stuck_repos = []
    for repo in indexer.stack_config.list_repos():
        if repo.status == IndexingStatus.INDEXING:
            stuck_repos.append(repo)

    if stuck_repos:
        print("\n  ⚠ Warning: Repos stuck in 'indexing' status:")
        for repo in stuck_repos:
            print(f"    - {repo.name}")
        print("\n  These may have been interrupted. To recover:")
        print("    mcpindexer recover")

    return 0


def cmd_recover(args):
    """Recover from interrupted indexing"""
    indexer = get_indexer()

    # Find repos stuck in INDEXING status
    stuck_repos = []
    for repo in indexer.stack_config.list_repos():
        if repo.status == IndexingStatus.INDEXING:
            stuck_repos.append(repo)

    if not stuck_repos:
        print("No repositories need recovery.")
        print("All repositories are in a stable state.")
        return 0

    print(f"Found {len(stuck_repos)} repository(ies) with interrupted indexing:\n")

    for repo in stuck_repos:
        print(f"  • {repo.name}")
        print(f"    Path: {repo.path}")
        print(f"    Last indexed: {repo.last_indexed or 'never'}")
        print()

    if not args.force:
        response = input(
            "Attempt to recover by re-indexing these repos? (y/n): "
        ).lower()
        if response != "y":
            print("\nCancelled. To force recovery without prompt:")
            print("  mcpindexer recover --force")
            return 0

    print("\nRecovering repositories...\n")

    recovered = 0
    failed = 0

    for repo in stuck_repos:
        print(f"Recovering {repo.name}...")

        try:
            repo_indexer = indexer.repo_indexers.get(repo.name)
            if not repo_indexer:
                print(f"  ✗ Repository not found in indexer")
                failed += 1
                continue

            # Reindex from scratch
            result = repo_indexer.reindex(force=True)

            # Update status
            indexer.stack_config.update_repo_status(
                repo.name,
                IndexingStatus.INDEXED,
                last_commit=result.git_commit,
                files_indexed=result.files_processed,
                chunks_indexed=result.chunks_indexed,
            )

            print(
                f"  ✓ Recovered: {result.files_processed} files, {result.chunks_indexed} chunks\n"
            )
            recovered += 1

        except Exception as e:
            print(f"  ✗ Failed: {str(e)}\n")
            indexer.stack_config.update_repo_status(
                repo.name, IndexingStatus.ERROR, error_message=str(e)
            )
            failed += 1

    # Summary
    print("Recovery complete:")
    print(f"  ✓ Recovered: {recovered}")
    if failed > 0:
        print(f"  ✗ Failed: {failed}")
        return 1

    return 0


def cmd_init(args):
    """Interactive setup wizard for first-time users"""
    print("======================================")
    print("  mcpIndexer Interactive Setup")
    print("======================================\n")

    # Step 1: Verify installation
    print("Step 1: Verifying installation...\n")

    try:
        from mcpindexer.embeddings import EmbeddingStore
        from mcpindexer.indexer import MultiRepoIndexer

        print("✓ mcpIndexer is installed correctly\n")
    except ImportError as e:
        print(f"✗ Installation error: {e}")
        print("Please run setup.sh first or install with: pip install -e .")
        return 1

    # Step 2: Check for existing repos
    indexer = get_indexer()
    repos = indexer.stack_config.list_repos()

    if repos:
        print(f"✓ Found {len(repos)} existing repository(ies):\n")
        for repo in repos:
            print(f"  - {repo.name} ({repo.path})")
        print()

        response = input("Would you like to add another repository? (y/n): ").lower()
        if response != "y":
            print("\nGreat! You're all set. Run 'mcpindexer status' to see your repos.")
            return 0
        print()
    else:
        print("No repositories indexed yet. Let's add your first one!\n")

    # Step 3: Add a repository
    print("Step 2: Add a repository\n")
    print("You can add:")
    print("  1. A local repository (provide a path)")
    print("  2. A GitHub repository (provide a URL)")
    print("  3. Skip for now")
    print()

    choice = input("Enter choice (1/2/3): ").strip()

    if choice == "3":
        print("\nNo problem! You can add repositories later with:")
        print("  mcpindexer add /path/to/repo")
        print("  mcpindexer add https://github.com/user/repo")
        return 0

    repo_source = None
    repo_name = None

    if choice == "1":
        repo_source = input("\nEnter the path to your local repository: ").strip()
        if not repo_source:
            print("No path provided. Exiting.")
            return 1
    elif choice == "2":
        repo_source = input("\nEnter the GitHub URL: ").strip()
        if not repo_source:
            print("No URL provided. Exiting.")
            return 1
    else:
        print("Invalid choice. Exiting.")
        return 1

    repo_name = input(
        "Enter a name for this repository (or press Enter for auto-detect): "
    ).strip()

    # Add the repository using the existing cmd_add logic
    print(f"\nIndexing repository...")

    # Create mock args for cmd_add
    class Args:
        pass

    add_args = Args()
    add_args.source = repo_source
    add_args.name = repo_name if repo_name else None
    add_args.clone_dir = None

    result = cmd_add(add_args)

    if result != 0:
        print("\nFailed to add repository. Please try manually with:")
        print(f"  mcpindexer add {repo_source}")
        return 1

    # Step 4: Demo search (optional)
    print("\n======================================")
    print("Step 3: Try a search (optional)")
    print("======================================\n")

    response = input("Would you like to try a semantic search? (y/n): ").lower()

    if response == "y":
        query = input("\nEnter a search query (e.g., 'authentication logic'): ").strip()

        if query:
            print(f"\nSearching for: '{query}'...\n")

            try:
                results = indexer.embedding_store.semantic_search(query, n_results=3)

                if results:
                    print(f"Found {len(results)} results:\n")
                    for i, result in enumerate(results, 1):
                        print(f"{i}. {result.file_path}")
                        print(f"   Symbol: {result.symbol_name}")
                        print(f"   Score: {result.score:.4f}")
                        print()
                else:
                    print(
                        "No results found. Try a different query or add more repositories."
                    )
            except Exception as e:
                print(f"Search error: {e}")

    # Step 5: Show next steps
    print("\n======================================")
    print("  Setup Complete!")
    print("======================================\n")
    print("Next steps:\n")
    print("1. Check your stack status:")
    print("   mcpindexer status\n")
    print("2. Add more repositories:")
    print("   mcpindexer add /path/to/repo\n")
    print("3. Search your code:")
    print("   Use the MCP tools with your AI assistant\n")
    print("4. Set up git hooks for auto-reindexing:")
    print("   mcpindexer install-hook /path/to/repo\n")
    print("For more help: mcpindexer --help")
    print()

    return 0


def cmd_check(args):
    """Verify mcpIndexer installation"""
    print("mcpIndexer Installation Check\n")

    all_ok = True

    # Check Python version
    py_version = sys.version_info
    if py_version >= (3, 10):
        print(f"✓ Python {py_version.major}.{py_version.minor}.{py_version.micro}")
    else:
        print(
            f"✗ Python {py_version.major}.{py_version.minor}.{py_version.micro} (3.10+ required)"
        )
        all_ok = False

    # Check core dependencies
    try:
        import chromadb

        print("✓ ChromaDB available")
    except ImportError:
        print("✗ ChromaDB not found - run: pip install chromadb>=0.4.22")
        all_ok = False

    try:
        import sentence_transformers

        print("✓ sentence-transformers available")
    except ImportError:
        print(
            "✗ sentence-transformers not found - run: pip install sentence-transformers>=2.2.2"
        )
        all_ok = False

    try:
        from mcpindexer.embeddings import EmbeddingStore
        from mcpindexer.indexer import MultiRepoIndexer

        print("✓ mcpindexer modules available")
    except ImportError as e:
        print(f"✗ mcpindexer not properly installed: {e}")
        print("  Try: pip install -e .")
        all_ok = False

    # Check database directory
    db_path = os.getenv("MCP_INDEXER_DB_PATH", "~/.mcpindexer/db")
    db_path_expanded = os.path.expanduser(db_path)
    if os.path.exists(db_path_expanded):
        print(f"✓ Database directory: {db_path_expanded}")
    else:
        print(f"⚠ Database directory does not exist (will be created on first use)")
        print(f"  Location: {db_path_expanded}")

    # Check stack config
    stack_path = os.path.expanduser("~/.mcpindexer/stack.json")
    if os.path.exists(stack_path):
        try:
            config = StackConfig()
            repos = config.list_repos()
            print(f"✓ Stack config: {len(repos)} repo(s) configured")
        except Exception as e:
            print(f"⚠ Stack config exists but could not be read: {e}")
    else:
        print("⚠ No repositories indexed yet")
        print("  Run: mcpindexer add /path/to/repo")

    print()
    if all_ok:
        print("✓ Installation verified! Ready to use.")
        print("\nNext steps:")
        print("  mcpindexer add /path/to/repo    # Index your first repository")
        print("  mcpindexer status                 # Check indexing status")
        return 0
    else:
        print("✗ Installation incomplete. Please fix the errors above.")
        return 1


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="MCP Indexer CLI - Manage repository indexing"
    )
    parser.add_argument("--version", action="version", version="mcpindexer 0.1.0")
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose output (INFO level logging)",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug output (DEBUG level logging, logs to file)",
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # init command
    parser_init = subparsers.add_parser(
        "init", help="Interactive setup wizard for first-time users"
    )
    parser_init.set_defaults(func=cmd_init)

    # add command
    parser_add = subparsers.add_parser(
        "add", help="Add a repository to index (local path or GitHub URL)"
    )
    parser_add.add_argument("source", help="GitHub URL or local path to repository")
    parser_add.add_argument(
        "--name", help="Name for the repository (auto-detected if not provided)"
    )
    parser_add.add_argument(
        "--clone-dir", help="Directory to clone into (default: ~/Code)"
    )
    parser_add.set_defaults(func=cmd_add)

    # check-updates command
    parser_check = subparsers.add_parser(
        "check-updates", help="Check which repositories need reindexing"
    )
    parser_check.set_defaults(func=cmd_check_updates)

    # reindex-changed command
    parser_reindex = subparsers.add_parser(
        "reindex-changed", help="Reindex repositories that have changed"
    )
    parser_reindex.set_defaults(func=cmd_reindex_changed)

    # install-hook command
    parser_hook = subparsers.add_parser(
        "install-hook", help="Install git post-merge hook in a repository"
    )
    parser_hook.add_argument("repo_path", help="Path to git repository")
    parser_hook.add_argument(
        "--force", action="store_true", help="Overwrite existing hook"
    )
    parser_hook.set_defaults(func=cmd_install_hook)

    # status command
    parser_status = subparsers.add_parser("status", help="Show stack status")
    parser_status.set_defaults(func=cmd_status)

    # recover command
    parser_recover = subparsers.add_parser(
        "recover", help="Recover from interrupted indexing"
    )
    parser_recover.add_argument(
        "--force", action="store_true", help="Skip confirmation prompt"
    )
    parser_recover.set_defaults(func=cmd_recover)

    # check command
    parser_check = subparsers.add_parser(
        "check", help="Verify installation and configuration"
    )
    parser_check.set_defaults(func=cmd_check)

    args = parser.parse_args()

    # Setup logging based on verbosity flags
    setup_logging(verbose=args.verbose, debug=args.debug)

    logger.debug(f"CLI invoked with command: {args.command}")
    logger.debug(f"Arguments: {vars(args)}")

    if not args.command:
        parser.print_help()
        return 1

    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())

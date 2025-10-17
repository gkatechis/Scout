"""
Main indexer orchestration

Coordinates parsing, chunking, embedding, and storage
Tracks git state for incremental updates
"""
from pathlib import Path
from typing import List, Optional, Dict, Set
from dataclasses import dataclass
import git
from mcpindexer.parser import CodeParser
from mcpindexer.chunker import CodeChunker, CodeChunk
from mcpindexer.embeddings import EmbeddingStore
from mcpindexer.dependency_analyzer import DependencyAnalyzer, CrossRepoAnalyzer
from mcpindexer.stack_config import StackConfig, IndexingStatus
from mcpindexer.dependency_storage import DependencyStorage


@dataclass
class IndexingResult:
    """Result of indexing operation"""
    repo_name: str
    files_processed: int
    files_skipped: int
    chunks_created: int
    chunks_indexed: int
    git_commit: Optional[str]
    errors: List[str]


class RepoIndexer:
    """
    Main indexer for a code repository

    Orchestrates the full indexing pipeline:
    parse → chunk → analyze → embed → store
    """

    SUPPORTED_EXTENSIONS = {'.py', '.js', '.mjs', '.cjs', '.ts', '.tsx', '.rb', '.go'}
    SKIP_DIRECTORIES = {'node_modules', 'vendor', 'dist', 'build', '.git', '__pycache__', 'venv', 'env'}

    def __init__(
        self,
        repo_path: str,
        repo_name: str,
        embedding_store: EmbeddingStore
    ):
        """
        Initialize repository indexer

        Args:
            repo_path: Path to the repository
            repo_name: Name identifier for the repository
            embedding_store: EmbeddingStore instance for persistence
        """
        self.repo_path = Path(repo_path)
        self.repo_name = repo_name
        self.embedding_store = embedding_store

        # Initialize components
        self.parser = CodeParser()
        self.chunker = CodeChunker(repo_name=repo_name)
        self.dependency_analyzer = DependencyAnalyzer(repo_name=repo_name)

        # Track git state
        self.git_repo = None
        try:
            self.git_repo = git.Repo(repo_path)
        except:
            pass  # Not a git repo, that's okay

    def index(
        self,
        file_filter: Optional[callable] = None,
        progress_callback: Optional[callable] = None,
        batch_size: int = 1000
    ) -> IndexingResult:
        """
        Index the entire repository

        Args:
            file_filter: Optional function to filter files (path -> bool)
            progress_callback: Optional callback for progress updates
            batch_size: Number of chunks to batch before adding to store

        Returns:
            IndexingResult with statistics
        """
        files_processed = 0
        files_skipped = 0
        errors = []
        all_chunks = []
        chunks_indexed = 0
        total_chunks_created = 0

        # Get current git commit
        git_commit = self._get_git_commit()

        # Scan repository
        for file_path in self._scan_repo():
            # Apply filter if provided
            if file_filter and not file_filter(file_path):
                continue

            try:
                # Parse file
                parsed = self.parser.parse_file(str(file_path))
                if not parsed:
                    files_skipped += 1
                    continue

                # Add to dependency analyzer
                self.dependency_analyzer.add_file(parsed)

                # Chunk code
                chunks = self.chunker.chunk_file(parsed)
                all_chunks.extend(chunks)
                total_chunks_created += len(chunks)

                files_processed += 1

                # Add chunks in batches to avoid memory exhaustion
                if len(all_chunks) >= batch_size:
                    try:
                        self.embedding_store.add_chunks(all_chunks)
                        chunks_indexed += len(all_chunks)
                        all_chunks = []  # Clear batch
                    except Exception as e:
                        errors.append(f"Embedding batch error: {str(e)}")
                        all_chunks = []  # Clear batch even on error

                # Progress callback
                if progress_callback and files_processed % 10 == 0:
                    progress_callback(files_processed, chunks_indexed + len(all_chunks))

            except Exception as e:
                files_skipped += 1
                errors.append(f"{file_path}: {str(e)}")

        # Add remaining chunks
        if all_chunks:
            try:
                self.embedding_store.add_chunks(all_chunks)
                chunks_indexed += len(all_chunks)
            except Exception as e:
                errors.append(f"Embedding final batch error: {str(e)}")

        return IndexingResult(
            repo_name=self.repo_name,
            files_processed=files_processed,
            files_skipped=files_skipped,
            chunks_created=total_chunks_created,
            chunks_indexed=chunks_indexed,
            git_commit=git_commit,
            errors=errors
        )

    def index_file(self, file_path: str) -> List[CodeChunk]:
        """
        Index a single file

        Args:
            file_path: Path to the file

        Returns:
            List of created chunks
        """
        parsed = self.parser.parse_file(file_path)
        if not parsed:
            return []

        chunks = self.chunker.chunk_file(parsed)
        if chunks:
            self.embedding_store.add_chunks(chunks)

        return chunks

    def reindex(
        self,
        force: bool = False,
        progress_callback: Optional[callable] = None
    ) -> IndexingResult:
        """
        Reindex the repository

        Args:
            force: If True, reindex all files. If False, only changed files.
            progress_callback: Optional progress callback

        Returns:
            IndexingResult
        """
        if force:
            # Delete existing chunks and reindex everything
            self.embedding_store.delete_repo(self.repo_name)
            return self.index(progress_callback=progress_callback)
        else:
            # Incremental reindex (only changed files)
            # TODO: Implement git diff-based incremental indexing
            return self.index(progress_callback=progress_callback)

    def get_stats(self) -> Dict:
        """
        Get indexing statistics

        Returns:
            Dictionary with statistics
        """
        # Get repo stats from embedding store
        repo_stats = self.embedding_store.get_repo_stats(self.repo_name)

        # Get dependency stats
        dep_stats = self.dependency_analyzer.get_dependency_stats()

        # Get git info
        git_commit = self._get_git_commit()
        git_branch = self._get_git_branch()

        return {
            "repo_name": self.repo_name,
            "repo_path": str(self.repo_path),
            "git_commit": git_commit,
            "git_branch": git_branch,
            "chunks_indexed": repo_stats['chunk_count'],
            "files_indexed": len(repo_stats['files']),
            "languages": repo_stats['languages'],
            "dependencies": dep_stats
        }

    def _scan_repo(self):
        """
        Scan repository for code files

        Yields:
            Path objects for supported code files
        """
        for file_path in self.repo_path.rglob('*'):
            # Skip if not a file
            if not file_path.is_file():
                continue

            # Skip if wrong extension
            if file_path.suffix not in self.SUPPORTED_EXTENSIONS:
                continue

            # Skip excluded directories
            if any(skip_dir in file_path.parts for skip_dir in self.SKIP_DIRECTORIES):
                continue

            yield file_path

    def _get_git_commit(self) -> Optional[str]:
        """Get current git commit hash"""
        if not self.git_repo:
            return None

        try:
            return self.git_repo.head.commit.hexsha
        except:
            return None

    def _get_git_branch(self) -> Optional[str]:
        """Get current git branch"""
        if not self.git_repo:
            return None

        try:
            return self.git_repo.active_branch.name
        except:
            return None

    def get_changed_files(self, since_commit: str) -> List[str]:
        """
        Get files changed since a given commit

        Args:
            since_commit: Git commit hash

        Returns:
            List of changed file paths
        """
        if not self.git_repo:
            return []

        try:
            # Get diff between commits
            commit = self.git_repo.commit(since_commit)
            current = self.git_repo.head.commit

            diffs = current.diff(commit)
            changed_files = []

            for diff in diffs:
                # Get file path
                if diff.a_path:
                    changed_files.append(diff.a_path)
                if diff.b_path and diff.b_path != diff.a_path:
                    changed_files.append(diff.b_path)

            return changed_files
        except:
            return []


class MultiRepoIndexer:
    """
    Manages indexing across multiple repositories
    """

    def __init__(self, embedding_store: EmbeddingStore, config_path: Optional[str] = None):
        """
        Initialize multi-repo indexer

        Args:
            embedding_store: Shared EmbeddingStore instance
            config_path: Optional path to stack configuration file
        """
        self.embedding_store = embedding_store
        self.repo_indexers: Dict[str, RepoIndexer] = {}
        self.cross_repo_analyzer = CrossRepoAnalyzer()
        self.stack_config = StackConfig(config_path)
        self.dependency_storage = DependencyStorage()

    def add_repo(
        self,
        repo_path: str,
        repo_name: str,
        auto_index: bool = True
    ) -> IndexingResult:
        """
        Add a repository to the stack

        Args:
            repo_path: Path to the repository
            repo_name: Name identifier
            auto_index: If True, index immediately

        Returns:
            IndexingResult if auto_index=True, else empty result
        """
        # Add to stack config
        self.stack_config.add_repo(repo_name, repo_path, auto_reindex=True)

        indexer = RepoIndexer(
            repo_path=repo_path,
            repo_name=repo_name,
            embedding_store=self.embedding_store
        )

        self.repo_indexers[repo_name] = indexer

        # Add to cross-repo analyzer
        self.cross_repo_analyzer.add_repo(repo_name, indexer.dependency_analyzer)

        if auto_index:
            # Update status to indexing
            self.stack_config.update_repo_status(repo_name, IndexingStatus.INDEXING)

            try:
                result = indexer.index()

                # Analyze and save dependencies
                dep_graph = indexer.dependency_analyzer.analyze()
                cross_deps = self._find_cross_repo_deps_for_repo(
                    repo_name,
                    dep_graph.external_packages
                )
                self.dependency_storage.save_repo_dependencies(
                    repo_name=repo_name,
                    internal_deps=dep_graph.internal_deps,
                    external_packages=list(dep_graph.external_packages),
                    cross_repo_deps=cross_deps
                )

                # Update status to indexed
                self.stack_config.update_repo_status(
                    repo_name,
                    IndexingStatus.INDEXED,
                    last_commit=result.git_commit,
                    files_indexed=result.files_processed,
                    chunks_indexed=result.chunks_indexed
                )

                return result
            except Exception as e:
                # Update status to error
                self.stack_config.update_repo_status(
                    repo_name,
                    IndexingStatus.ERROR,
                    error_message=str(e)
                )
                raise
        else:
            return IndexingResult(
                repo_name=repo_name,
                files_processed=0,
                files_skipped=0,
                chunks_created=0,
                chunks_indexed=0,
                git_commit=None,
                errors=[]
            )

    def remove_repo(self, repo_name: str) -> int:
        """
        Remove a repository from the stack

        Args:
            repo_name: Repository name

        Returns:
            Number of chunks deleted
        """
        if repo_name in self.repo_indexers:
            del self.repo_indexers[repo_name]

        # Remove from cross-repo analyzer
        if repo_name in self.cross_repo_analyzer.repo_analyzers:
            del self.cross_repo_analyzer.repo_analyzers[repo_name]

        # Remove from config
        self.stack_config.remove_repo(repo_name)

        return self.embedding_store.delete_repo(repo_name)

    def list_repos(self) -> List[str]:
        """List all indexed repositories"""
        return self.embedding_store.list_repos()

    def get_repo_stats(self, repo_name: str) -> Optional[Dict]:
        """
        Get statistics for a repository

        Args:
            repo_name: Repository name

        Returns:
            Stats dictionary or None if not found
        """
        if repo_name in self.repo_indexers:
            return self.repo_indexers[repo_name].get_stats()
        else:
            # Try to get from embedding store
            return self.embedding_store.get_repo_stats(repo_name)

    def reindex_all(self, force: bool = False) -> List[IndexingResult]:
        """
        Reindex all repositories

        Args:
            force: If True, force full reindex

        Returns:
            List of IndexingResult for each repo
        """
        results = []
        for repo_name, indexer in self.repo_indexers.items():
            result = indexer.reindex(force=force)
            results.append(result)

        return results

    def get_cross_repo_dependencies(self) -> List[Dict[str, str]]:
        """
        Get dependencies between repositories

        Returns:
            List of cross-repo dependencies
        """
        return self.dependency_storage.get_all_cross_repo_dependencies()

    def suggest_missing_repos(self) -> List[str]:
        """
        Suggest repositories that should be added based on dependencies

        Returns:
            List of suggested repository names
        """
        indexed_repos = set(self.list_repos())
        return self.dependency_storage.suggest_missing_repos(indexed_repos)

    def _find_cross_repo_deps_for_repo(
        self,
        repo_name: str,
        external_packages: Set[str]
    ) -> List[Dict[str, str]]:
        """
        Find cross-repository dependencies for a single repo

        Args:
            repo_name: Source repository name
            external_packages: External packages used by this repo

        Returns:
            List of cross-repo dependencies
        """
        cross_deps = []
        all_repos = set(self.list_repos())

        for package in external_packages:
            # Check if package matches any other indexed repo
            for other_repo in all_repos:
                if other_repo != repo_name and self._package_matches_repo(package, other_repo):
                    cross_deps.append({
                        "source_repo": repo_name,
                        "target_repo": other_repo,
                        "package": package
                    })

        return cross_deps

    def _package_matches_repo(self, package: str, repo_name: str) -> bool:
        """
        Check if a package name matches a repository

        Args:
            package: Package name
            repo_name: Repository name

        Returns:
            True if they match
        """
        # Normalize names
        package_lower = package.lower().replace('@zendesk/', '').replace('zendesk-', '').replace('_', '-')
        repo_lower = repo_name.lower().replace('zendesk-', '').replace('zendesk_', '').replace('_', '-')

        # Check for matches
        return package_lower in repo_lower or repo_lower in package_lower

    def get_stack_status(self) -> Dict:
        """
        Get overall stack status and statistics

        Returns:
            Dictionary with stack status
        """
        return self.stack_config.get_stats()

    def get_repo_config(self, repo_name: str) -> Optional[Dict]:
        """
        Get configuration for a specific repository

        Args:
            repo_name: Repository name

        Returns:
            Configuration dict or None if not found
        """
        repo_config = self.stack_config.get_repo(repo_name)
        if repo_config:
            return repo_config.to_dict()
        return None

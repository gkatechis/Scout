"""
BM25 keyword search for code

Provides exact keyword matching using BM25 algorithm
Complements semantic search for hybrid search capability
"""

from typing import TYPE_CHECKING, Dict, List, Optional

from rank_bm25 import BM25Okapi

from mcpindexer.chunker import CodeChunk

if TYPE_CHECKING:
    from mcpindexer.embeddings import SearchResult


class KeywordSearchIndex:
    """
    BM25-based keyword search index for code chunks
    """

    def __init__(self):
        """Initialize keyword search index"""
        self.bm25: Optional[BM25Okapi] = None
        self.chunks: List[CodeChunk] = []
        self.chunk_map: Dict[str, CodeChunk] = {}  # chunk_id -> chunk

    def index_chunks(self, chunks: List[CodeChunk]) -> None:
        """
        Add code chunks to the keyword index

        Args:
            chunks: List of CodeChunk objects to index
        """
        if not chunks:
            return

        # Add chunks to internal storage
        self.chunks.extend(chunks)
        for chunk in chunks:
            self.chunk_map[chunk.chunk_id] = chunk

        # Tokenize all documents (use context_text like semantic search)
        corpus = [chunk.context_text for chunk in self.chunks]
        tokenized_corpus = [doc.lower().split() for doc in corpus]

        # Create BM25 index
        self.bm25 = BM25Okapi(tokenized_corpus)

    def search(
        self,
        query: str,
        n_results: int = 10,
        repo_filter: Optional[List[str]] = None,
        language_filter: Optional[str] = None,
    ) -> List["SearchResult"]:
        """
        Search for code using keyword matching

        Args:
            query: Keyword search query
            n_results: Maximum number of results
            repo_filter: Optional list of repo names to filter
            language_filter: Optional language to filter

        Returns:
            List of SearchResult objects sorted by BM25 score
        """
        # Import here to avoid circular dependency
        from mcpindexer.embeddings import SearchResult

        if not self.bm25 or not self.chunks:
            return []

        # Tokenize query
        tokenized_query = query.lower().split()

        # Get BM25 scores for all documents
        scores = self.bm25.get_scores(tokenized_query)

        # Create (score, chunk, index) tuples
        results = []
        for idx, (score, chunk) in enumerate(zip(scores, self.chunks)):
            # Apply filters
            if repo_filter and chunk.repo_name not in repo_filter:
                continue
            if language_filter and chunk.language != language_filter:
                continue

            # Only include results with non-zero scores
            if score > 0:
                results.append((score, chunk, idx))

        # Sort by score descending
        results.sort(key=lambda x: x[0], reverse=True)

        # Take top n_results
        results = results[:n_results]

        # Convert to SearchResult objects
        search_results = []
        for score, chunk, idx in results:
            search_results.append(
                SearchResult(
                    chunk_id=chunk.chunk_id,
                    file_path=chunk.file_path,
                    repo_name=chunk.repo_name,
                    symbol_name=chunk.symbol_name,
                    code_text=chunk.context_text,
                    score=float(score),
                    metadata={
                        "file_path": chunk.file_path,
                        "repo_name": chunk.repo_name,
                        "language": chunk.language,
                        "chunk_type": chunk.chunk_type,
                        "symbol_name": chunk.symbol_name or "",
                        "parent_class": chunk.parent_class or "",
                        "start_line": chunk.start_line,
                        "end_line": chunk.end_line,
                        "token_count": chunk.token_count,
                        "imports": ",".join(chunk.imports) if chunk.imports else "",
                    },
                )
            )

        return search_results

    def delete_repo(self, repo_name: str) -> int:
        """
        Delete all chunks for a repository

        Args:
            repo_name: Repository to delete

        Returns:
            Number of chunks deleted
        """
        # Filter out chunks from this repo
        original_count = len(self.chunks)
        self.chunks = [c for c in self.chunks if c.repo_name != repo_name]

        # Update chunk map
        self.chunk_map = {
            cid: chunk
            for cid, chunk in self.chunk_map.items()
            if chunk.repo_name != repo_name
        }

        # Rebuild index
        if self.chunks:
            corpus = [chunk.context_text for chunk in self.chunks]
            tokenized_corpus = [doc.lower().split() for doc in corpus]
            self.bm25 = BM25Okapi(tokenized_corpus)
        else:
            self.bm25 = None

        return original_count - len(self.chunks)

    def delete_file(self, repo_name: str, file_path: str) -> int:
        """
        Delete all chunks for a specific file

        Args:
            repo_name: Repository name
            file_path: File path

        Returns:
            Number of chunks deleted
        """
        # Filter out chunks from this file
        original_count = len(self.chunks)
        self.chunks = [
            c
            for c in self.chunks
            if not (c.repo_name == repo_name and c.file_path == file_path)
        ]

        # Update chunk map
        self.chunk_map = {
            cid: chunk
            for cid, chunk in self.chunk_map.items()
            if not (chunk.repo_name == repo_name and chunk.file_path == file_path)
        }

        # Rebuild index
        if self.chunks:
            corpus = [chunk.context_text for chunk in self.chunks]
            tokenized_corpus = [doc.lower().split() for doc in corpus]
            self.bm25 = BM25Okapi(tokenized_corpus)
        else:
            self.bm25 = None

        return original_count - len(self.chunks)

    def reset(self) -> None:
        """Clear the entire index"""
        self.bm25 = None
        self.chunks = []
        self.chunk_map = {}

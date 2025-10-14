"""
Embedding generation and vector storage using ChromaDB

Uses sentence-transformers for code-specific embeddings
Stores in ChromaDB with metadata for filtering
"""
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
from mcpindexer.chunker import CodeChunk


@dataclass
class SearchResult:
    """Result from semantic search"""
    chunk_id: str
    file_path: str
    repo_name: str
    symbol_name: Optional[str]
    code_text: str
    score: float  # Similarity score
    metadata: Dict[str, Any]


class EmbeddingStore:
    """
    Manages code embeddings and vector search using ChromaDB
    """

    # Default embedding model (code-specific)
    DEFAULT_MODEL = "sentence-transformers/all-MiniLM-L6-v2"  # Fast, general purpose
    # For production, consider: "jinaai/jina-embeddings-v2-base-code"

    def __init__(
        self,
        db_path: str = "./chroma_data",
        collection_name: str = "code_embeddings",
        model_name: Optional[str] = None
    ):
        """
        Initialize embedding store

        Args:
            db_path: Path to ChromaDB storage directory
            collection_name: Name of the collection
            model_name: Optional embedding model name
        """
        self.db_path = db_path
        self.collection_name = collection_name
        self.model_name = model_name or self.DEFAULT_MODEL

        # Initialize ChromaDB client
        self.client = chromadb.PersistentClient(
            path=db_path,
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )

        # Load embedding model
        self.model = SentenceTransformer(self.model_name)

        # Get or create collection
        try:
            self.collection = self.client.get_collection(name=collection_name)
        except Exception:
            # Collection doesn't exist, create it
            self.collection = self.client.create_collection(
                name=collection_name,
                metadata={"description": "Code embeddings for semantic search"}
            )

    def add_chunks(self, chunks: List[CodeChunk]) -> None:
        """
        Add code chunks to the vector store

        Args:
            chunks: List of CodeChunk objects to embed and store
        """
        if not chunks:
            return

        # Prepare data for ChromaDB
        ids = [chunk.chunk_id for chunk in chunks]
        documents = [chunk.context_text for chunk in chunks]  # Use context-enhanced text
        metadatas = [
            {
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
            }
            for chunk in chunks
        ]

        # Generate embeddings
        embeddings = self.model.encode(
            documents,
            convert_to_numpy=True,
            show_progress_bar=False
        ).tolist()

        # Add to collection
        self.collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas
        )

    def semantic_search(
        self,
        query: str,
        n_results: int = 10,
        repo_filter: Optional[List[str]] = None,
        language_filter: Optional[str] = None
    ) -> List[SearchResult]:
        """
        Perform semantic search on code

        Args:
            query: Natural language query
            n_results: Maximum number of results
            repo_filter: Optional list of repo names to filter
            language_filter: Optional language to filter (e.g., "python")

        Returns:
            List of SearchResult objects
        """
        # Generate query embedding
        query_embedding = self.model.encode(
            [query],
            convert_to_numpy=True,
            show_progress_bar=False
        ).tolist()[0]

        # Build where filter
        where_filter = {}
        if repo_filter:
            where_filter["repo_name"] = {"$in": repo_filter}
        if language_filter:
            where_filter["language"] = language_filter

        # Query ChromaDB
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where=where_filter if where_filter else None
        )

        # Format results
        search_results = []
        for i in range(len(results['ids'][0])):
            metadata = results['metadatas'][0][i]
            search_results.append(SearchResult(
                chunk_id=results['ids'][0][i],
                file_path=metadata['file_path'],
                repo_name=metadata['repo_name'],
                symbol_name=metadata.get('symbol_name') or None,
                code_text=results['documents'][0][i],
                score=results['distances'][0][i] if 'distances' in results else 0.0,
                metadata=metadata
            ))

        return search_results

    def find_by_symbol(
        self,
        symbol_name: str,
        repo_filter: Optional[List[str]] = None
    ) -> List[SearchResult]:
        """
        Find code by exact symbol name

        Args:
            symbol_name: The symbol to search for
            repo_filter: Optional list of repo names to filter

        Returns:
            List of SearchResult objects
        """
        # Build where filter with $and if multiple conditions
        if repo_filter:
            where_filter = {
                "$and": [
                    {"symbol_name": symbol_name},
                    {"repo_name": {"$in": repo_filter}}
                ]
            }
        else:
            where_filter = {"symbol_name": symbol_name}

        results = self.collection.get(
            where=where_filter,
            limit=100
        )

        # Format results
        search_results = []
        for i in range(len(results['ids'])):
            metadata = results['metadatas'][i]
            search_results.append(SearchResult(
                chunk_id=results['ids'][i],
                file_path=metadata['file_path'],
                repo_name=metadata['repo_name'],
                symbol_name=metadata.get('symbol_name') or None,
                code_text=results['documents'][i],
                score=1.0,  # Exact match
                metadata=metadata
            ))

        return search_results

    def find_related_by_file(
        self,
        file_path: str,
        repo_name: str,
        n_results: int = 10
    ) -> List[SearchResult]:
        """
        Find code related to a given file (using vector similarity)

        Args:
            file_path: Path to the file
            repo_name: Repository name
            n_results: Number of results to return

        Returns:
            List of SearchResult objects
        """
        # Get all chunks from the file
        file_chunks = self.collection.get(
            where={
                "$and": [
                    {"file_path": file_path},
                    {"repo_name": repo_name}
                ]
            }
        )

        if not file_chunks['ids']:
            return []

        # Use first chunk's embedding to find similar code
        # In production, might want to average embeddings or use other strategies
        first_doc = file_chunks['documents'][0]
        embedding = self.model.encode(
            [first_doc],
            convert_to_numpy=True,
            show_progress_bar=False
        ).tolist()[0]

        # Find similar chunks (excluding same file)
        results = self.collection.query(
            query_embeddings=[embedding],
            n_results=n_results + 20,  # Get extra to filter out same file
            where={
                "repo_name": repo_name  # Same repo only for now
            }
        )

        # Filter out results from the same file
        search_results = []
        for i in range(len(results['ids'][0])):
            metadata = results['metadatas'][0][i]
            if metadata['file_path'] != file_path:
                search_results.append(SearchResult(
                    chunk_id=results['ids'][0][i],
                    file_path=metadata['file_path'],
                    repo_name=metadata['repo_name'],
                    symbol_name=metadata.get('symbol_name') or None,
                    code_text=results['documents'][0][i],
                    score=results['distances'][0][i] if 'distances' in results else 0.0,
                    metadata=metadata
                ))

                if len(search_results) >= n_results:
                    break

        return search_results

    def list_repos(self) -> List[str]:
        """List all indexed repositories"""
        # Get all unique repo names from metadata
        # Note: ChromaDB doesn't have a direct way to get distinct values,
        # so we need to fetch some samples and aggregate
        results = self.collection.get(limit=10000)  # Adjust limit as needed

        repos = set()
        for metadata in results['metadatas']:
            repos.add(metadata['repo_name'])

        return sorted(list(repos))

    def get_repo_stats(self, repo_name: str) -> Dict[str, Any]:
        """Get statistics for a repository"""
        results = self.collection.get(
            where={"repo_name": repo_name}
        )

        if not results['ids']:
            return {
                "repo_name": repo_name,
                "chunk_count": 0,
                "files": [],
                "languages": []
            }

        # Aggregate stats
        files = set()
        languages = set()

        for metadata in results['metadatas']:
            files.add(metadata['file_path'])
            languages.add(metadata['language'])

        return {
            "repo_name": repo_name,
            "chunk_count": len(results['ids']),
            "files": sorted(list(files)),
            "languages": sorted(list(languages))
        }

    def delete_repo(self, repo_name: str) -> int:
        """
        Delete all chunks for a repository

        Args:
            repo_name: Repository to delete

        Returns:
            Number of chunks deleted
        """
        # Get all IDs for the repo
        results = self.collection.get(
            where={"repo_name": repo_name}
        )

        if results['ids']:
            self.collection.delete(ids=results['ids'])
            return len(results['ids'])

        return 0

    def reset(self) -> None:
        """Reset the entire collection (for testing)"""
        self.client.delete_collection(name=self.collection_name)
        self.collection = self.client.create_collection(
            name=self.collection_name,
            metadata={"description": "Code embeddings for semantic search"}
        )

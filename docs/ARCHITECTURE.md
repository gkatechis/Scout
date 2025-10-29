# Architecture

This document describes the internal architecture of Scout.

## Components

### 1. Parser (`parser.py`)
Tree-sitter based multi-language AST parsing. Extracts symbols, functions, classes, and imports from source files.

**Supported Languages**: Python, JavaScript, TypeScript, Ruby, Go

### 2. Chunker (`chunker.py`)
Intelligent code chunking that respects AST boundaries. Splits code into semantic units while:
- Preserving context (imports, class definitions)
- Maintaining reasonable token sizes for embeddings
- Tracking line numbers and parent symbols

### 3. Embeddings (`embeddings.py`)
ChromaDB + sentence-transformers for semantic search. Manages:
- Embedding generation from code chunks
- Vector storage and retrieval
- Metadata tracking (file paths, symbols, languages)

### 4. Indexer (`indexer.py`)
Orchestrates the indexing pipeline: parsing → chunking → embedding → storage. Provides:
- Single repository indexing (`RepoIndexer`)
- Multi-repository management (`MultiRepoIndexer`)
- Incremental updates based on git commits

### 5. Dependency Analyzer (`dependency_analyzer.py`)
Tracks imports and dependencies within and across repositories:
- Extracts import statements
- Maps internal vs external dependencies
- Identifies cross-repository dependencies
- Suggests missing repositories to add

### 6. Stack Config (`stack_config.py`)
Persistent configuration management stored at `~/.mcpindexer/stack.json`:
- Repository metadata (name, path, status)
- Git commit tracking for incremental updates
- Auto-reindex settings

### 7. MCP Server (`server.py`)
Exposes 13 tools via Model Context Protocol:
- Semantic search and Q&A
- Symbol lookup (definitions and references)
- Repository management
- Cross-repo dependency analysis

### 8. CLI (`cli.py`)
Command-line interface for:
- Interactive setup wizard
- Repository management
- Status monitoring
- Git hook installation

## Indexing Pipeline

```
Code File
    ↓
Parser (Tree-sitter AST)
    ↓
Chunker (Semantic Units)
    ↓
Embeddings (sentence-transformers)
    ↓
ChromaDB Store
```

### Pipeline Details

1. **Parsing**: Tree-sitter parses source files into Abstract Syntax Trees (ASTs)
2. **Symbol Extraction**: Extracts functions, classes, methods, and import statements
3. **Chunking**: Groups code into semantic units (functions, classes, modules)
4. **Context Preservation**: Includes imports and parent class context in chunks
5. **Embedding Generation**: sentence-transformers creates vector embeddings
6. **Storage**: ChromaDB stores embeddings with metadata for fast retrieval

## Data Flow

### Indexing a Repository

```
User: mcpindexer add /path/to/repo
    ↓
CLI validates path and creates RepoIndexer
    ↓
Scanner walks file tree (filters by language)
    ↓
For each file:
    Parser → Chunker → Embeddings
    ↓
Store chunks in ChromaDB
    ↓
Update stack.json with metadata
```

### Semantic Search Query

```
User: "authentication logic"
    ↓
MCP Server receives query
    ↓
EmbeddingStore generates query embedding
    ↓
ChromaDB performs vector similarity search
    ↓
Results ranked by cosine similarity
    ↓
Returns code chunks with metadata
```

## Performance

Based on testing with real-world repositories:

| Metric | Value |
|--------|-------|
| **Indexing Speed** | ~56 files/sec |
| **Small Repo** (162 files) | 302 chunks in 1.86s |
| **Multi-Repo** (3 repos, 255 files) | 595 chunks in 4.58s |
| **Search Latency** | ~100-200ms per query |

### Performance Characteristics

**Indexing**:
- CPU-bound during parsing and chunking
- I/O-bound during embedding generation
- Memory usage scales with repo size (~1-2GB for large monoliths)

**Searching**:
- Sub-second for most queries
- Scales logarithmically with corpus size (ChromaDB vector index)
- GPU acceleration available for embedding generation

## Storage

### ChromaDB Collection Schema

Each code chunk is stored with:
- **id**: Unique identifier (`repo_name:file_path:chunk_index`)
- **embedding**: 384-dimensional vector (sentence-transformers)
- **metadata**:
  - `file_path`: Relative path within repository
  - `repo_name`: Repository identifier
  - `language`: Source language (python, javascript, etc.)
  - `start_line`, `end_line`: Line number range
  - `symbol_name`: Function/class name (if applicable)
  - `symbol_type`: function, class, method, etc.
  - `parent_symbol`: Parent class for methods

### Stack Configuration (`~/.mcpindexer/stack.json`)

```json
{
  "repos": {
    "repo-name": {
      "path": "/absolute/path/to/repo",
      "name": "repo-name",
      "status": "indexed",
      "indexed_at": "2024-01-15T10:30:00",
      "last_commit": "abc123...",
      "files_indexed": 162,
      "chunks_indexed": 302,
      "auto_reindex": true
    }
  }
}
```

## Incremental Updates

Scout tracks git commits to enable incremental reindexing:

1. **Commit Tracking**: Stores last indexed commit hash in stack.json
2. **Change Detection**: Compares current HEAD with stored commit
3. **Selective Reindex**: Only reindexes if commits have changed
4. **Git Hooks**: Optional post-merge hook for automatic reindexing

## Dependency Analysis

### Internal Dependencies
Tracks imports within a repository to understand module relationships.

### External Dependencies
Identifies imported packages (e.g., `requests`, `lodash`) to understand external dependencies.

### Cross-Repository Dependencies
Detects when one indexed repository imports from another indexed repository, enabling:
- Dependency graph visualization
- Missing repository suggestions
- Impact analysis for changes

## Extension Points

### Adding Language Support

To add a new language:
1. Install tree-sitter grammar: `pip install tree-sitter-<language>`
2. Add language to `parser.py` LANGUAGE_MAP
3. Implement symbol extraction for language's AST structure
4. Add file extension mapping

### Custom Chunking Strategies

Override `CodeChunker` methods:
- `chunk_by_function()`: Per-function chunking
- `chunk_by_class()`: Per-class chunking
- `chunk_by_symbols()`: Custom symbol-based chunking

### Alternative Embedding Models

Replace sentence-transformers in `embeddings.py`:
- OpenAI embeddings (requires API key)
- Local LLM embeddings (ollama, llama.cpp)
- Custom fine-tuned models

## Security Considerations

- **Code Privacy**: All embeddings stored locally, no external API calls
- **File Access**: Respects .gitignore patterns by default
- **Credentials**: No credentials stored or transmitted
- **Sandboxing**: Parser runs in same process (no sandboxing currently)

## Future Improvements

See open issues for planned enhancements:
- Language Server Protocol (LSP) integration
- IDE plugins (VS Code, JetBrains)
- Distributed indexing for large organizations
- Advanced query syntax (boolean operators, filters)
- Code change impact analysis

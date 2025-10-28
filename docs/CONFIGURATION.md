# Configuration Guide

## Environment Variables

### MCP_INDEXER_DB_PATH

Controls where mcpIndexer stores its database and embeddings.

**Default**: `~/.mcpindexer/db`

**Usage**:
```bash
export MCP_INDEXER_DB_PATH=/custom/path/to/db
```

**What it affects**:
- ChromaDB database location
- Embedding storage
- Persistent index data

### MCP_INDEXER_MODEL

Controls which sentence-transformer model is used for generating code embeddings.

**Default**: `sentence-transformers/multi-qa-mpnet-base-dot-v1`

**Usage**:
```bash
export MCP_INDEXER_MODEL=sentence-transformers/all-MiniLM-L6-v2
```

**What it affects**:
- Quality of semantic search results
- Indexing speed
- Query speed
- Memory usage

**Benchmarked models** (all achieve 100% accuracy on code search):
- `sentence-transformers/multi-qa-mpnet-base-dot-v1` (default) - **Fastest overall** (0.07s indexing, 11ms queries)
- `sentence-transformers/all-MiniLM-L6-v2` - Good balance (0.15s indexing, 27ms queries)
- `sentence-transformers/msmarco-bert-base-dot-v5` - Search-optimized (0.15s indexing, 30ms queries)
- `sentence-transformers/all-mpnet-base-v2` - Highest quality but slow (1.4s indexing, 287ms queries)

**Note**: Changing models requires reindexing all repositories, as embeddings are not compatible across models

### MCP_INDEXER_DEVICE

Controls which device (CPU or GPU) is used for generating embeddings.

**Default**: Auto-detected (prefers GPU if available: CUDA > MPS > CPU)

**Usage**:
```bash
export MCP_INDEXER_DEVICE=cuda    # Use NVIDIA GPU
export MCP_INDEXER_DEVICE=mps     # Use Apple Silicon GPU
export MCP_INDEXER_DEVICE=cpu     # Force CPU usage
```

**What it affects**:
- Embedding generation speed
- Indexing speed
- Query speed
- Memory location (RAM vs VRAM)

**Performance benefits**:
- **CPU**: Baseline performance (170-750 queries/sec)
- **GPU (CUDA/MPS)**: 10-50x faster (4,000-18,000 queries/sec)
- **Impact**: Large repos that take 10 minutes can index in 12-60 seconds with GPU

**GPU Requirements**:
- **CUDA**: NVIDIA GPU with CUDA support + CUDA toolkit installed
- **MPS**: Apple Silicon (M1/M2/M3) + macOS 12.3+
- **Memory**: GPU should have 2-4GB VRAM for typical models

**Auto-detection behavior**:
1. Checks if CUDA is available (NVIDIA GPU)
2. Falls back to MPS if available (Apple Silicon)
3. Falls back to CPU if no GPU detected

**Note**: GPU acceleration requires PyTorch with GPU support. Install with:
```bash
# For CUDA (NVIDIA):
pip install torch --index-url https://download.pytorch.org/whl/cu118

# For MPS (Apple Silicon):
pip install torch  # MPS support included by default on macOS
```

### MCP_INDEXER_EMBEDDING_BATCH_SIZE

Controls how many documents are encoded at once during embedding generation.

**Default**: 256

**Usage**:
```bash
export MCP_INDEXER_EMBEDDING_BATCH_SIZE=512   # Larger batches (more GPU memory)
export MCP_INDEXER_EMBEDDING_BATCH_SIZE=128   # Smaller batches (less GPU memory)
```

**What it affects**:
- GPU memory usage during indexing
- Embedding generation efficiency
- Trade-off between memory and speed

**Recommendations**:
- **GPU with 4GB+ VRAM**: 512
- **GPU with 2-4GB VRAM**: 256 (default)
- **GPU with <2GB VRAM or CPU**: 128

### MCP_INDEXER_DB_BATCH_SIZE

Controls how many chunks to accumulate before writing to ChromaDB.

**Default**: 5000

**Usage**:
```bash
export MCP_INDEXER_DB_BATCH_SIZE=10000   # Larger batches (better throughput)
export MCP_INDEXER_DB_BATCH_SIZE=2500    # Smaller batches (less memory)
```

**What it affects**:
- Memory usage during indexing
- Database write efficiency
- Indexing throughput

**Recommendations**:
- **High memory (16GB+ RAM)**: 10000
- **Normal memory (8-16GB RAM)**: 5000 (default)
- **Low memory (<8GB RAM)**: 2500

**Performance impact**: Larger batches provide 10-30% better throughput due to fewer database writes.

**Example configurations**:

```bash
# Use default location (recommended)
export MCP_INDEXER_DB_PATH=~/.mcpindexer/db

# Use project-specific location
export MCP_INDEXER_DB_PATH=./project_indexes

# Use shared team location
export MCP_INDEXER_DB_PATH=/shared/team/code_indexes
```

### PYTHONPATH

**NOT required** if you used `pip install -e .` (recommended).

**Only needed if**:
- You did NOT use `pip install -e .`
- You installed with `pip install -r requirements.txt` instead

**Usage**:
```bash
export PYTHONPATH=/absolute/path/to/mcpIndexer/src
```

**What it does**:
- Allows Python to find the `mcpindexer` module when not installed as a package
- Must point to the `src/` directory

## MCP Configuration

### .mcp.json

Used by MCP clients (like Claude Code) to connect to the mcpIndexer server.

**Location**: Project root or Claude Code configuration directory

**Example**:
```json
{
  "mcpServers": {
    "mcpindexer": {
      "command": "/absolute/path/to/mcpIndexer/venv/bin/python3",
      "args": [
        "/absolute/path/to/mcpIndexer/src/mcpindexer/server.py"
      ],
      "env": {
        "MCP_INDEXER_DB_PATH": "~/.mcpindexer/db"
      }
    }
  }
}
```

**Configuration fields**:
- `command`: Python interpreter from virtual environment (recommended)
- `args`: Path to the MCP server script
- `env.MCP_INDEXER_DB_PATH`: Database location

**Note**: PYTHONPATH is not needed if you used `pip install -e .` during setup. If you used `pip install -r requirements.txt` instead, add `"PYTHONPATH": "/absolute/path/to/mcpIndexer/src"` to the `env` section.

## Stack Configuration

### ~/.mcpindexer/stack.json

Automatically created and maintained by mcpIndexer. Tracks indexed repositories.

**Example**:
```json
{
  "version": "1.0",
  "repos": {
    "my-repo": {
      "name": "my-repo",
      "path": "/absolute/path/to/repo",
      "status": "indexed",
      "last_indexed": "2025-10-17T12:34:56.789Z",
      "last_commit": "abc123def456...",
      "files_indexed": 162,
      "chunks_indexed": 302,
      "auto_reindex": true
    }
  }
}
```

**Fields**:
- `name`: Repository identifier
- `path`: Absolute path to repository
- `status`: `indexed`, `indexing`, `error`, or `pending`
- `last_indexed`: ISO timestamp of last indexing
- `last_commit`: Git commit hash when last indexed
- `files_indexed`: Number of files processed
- `chunks_indexed`: Number of code chunks created
- `auto_reindex`: Whether to auto-reindex on git pull

**Manual editing**: Generally not recommended, but safe if you follow the schema.

## Dependency Storage

### ~/.mcpindexer/dependencies.json

Stores cross-repository dependency information.

**Example**:
```json
{
  "version": "1.0",
  "repos": {
    "my-repo": {
      "internal_count": 45,
      "external_packages": ["express", "react"],
      "cross_repo_deps": [
        {
          "source_repo": "my-repo",
          "target_repo": "shared-lib",
          "package": "@myorg/shared-lib"
        }
      ]
    }
  }
}
```

**Automatically maintained**: Updated each time a repository is indexed.

## Organization-Specific Configuration

### Filtering Packages by Organization

You can configure mcpIndexer to only track packages from your organization:

```python
from mcpindexer.dependency_storage import DependencyStorage

# Configure organization prefixes
storage = DependencyStorage(
    org_prefixes=['@myorg/', 'myorg-', 'myorg_']
)

# Now only packages matching these prefixes will be tracked
```

This is useful for:
- Focusing on internal dependencies
- Reducing noise from external packages
- Tracking monorepo dependencies

**Default behavior**: If no prefixes are configured, all packages are tracked.

## Advanced Configuration

### Custom Database Location Per Repository

```python
from mcpindexer.embeddings import EmbeddingStore

# Different databases for different projects
frontend_store = EmbeddingStore(
    db_path="~/.mcpindexer/frontend_db",
    collection_name="frontend_index"
)

backend_store = EmbeddingStore(
    db_path="~/.mcpindexer/backend_db",
    collection_name="backend_index"
)
```

### Batch Size Tuning

For large repositories, adjust batch size:

```python
result = indexer.index(batch_size=2000)  # Default is 1000
```

**Higher values**: Better performance, more memory usage
**Lower values**: More incremental progress, lower memory

### File Filtering

Exclude specific files or directories:

```python
def my_filter(file_path):
    # Skip test files
    if 'test' in str(file_path):
        return False
    # Skip generated files
    if 'generated' in str(file_path):
        return False
    return True

result = indexer.index(file_filter=my_filter)
```

## Troubleshooting

### Database Location Issues

**Problem**: Can't find database or indices

**Solutions**:
1. Check `MCP_INDEXER_DB_PATH` is set correctly
2. Ensure path has write permissions
3. Use absolute paths, not relative
4. Expand `~` to full home directory path

### PYTHONPATH Issues

**Problem**: `ModuleNotFoundError: No module named 'mcpindexer'`

**Solutions**:
1. Verify PYTHONPATH includes the `src/` directory
2. Use absolute paths
3. Check spelling and capitalization
4. Restart your terminal/IDE after setting

### Permission Errors

**Problem**: Can't write to database directory

**Solutions**:
```bash
# Check permissions
ls -la ~/.mcpindexer/

# Fix permissions
chmod 755 ~/.mcpindexer/
chmod 644 ~/.mcpindexer/*.json
```

## Best Practices

1. **Use the default database location** unless you have a specific reason not to
2. **Set environment variables in your shell profile** (`.bashrc`, `.zshrc`) for persistence
3. **Use absolute paths** in all configuration files
4. **Back up `~/.mcpindexer/`** directory if you have large indices
5. **One database per development environment** (work, personal, etc.)
6. **Configure organization prefixes** to reduce noise from external dependencies

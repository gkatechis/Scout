# Configuration Guide

## Environment Variables

### SCOUT_DB_PATH

Controls where Scout stores its database and embeddings.

**Default**: `~/.scout/db`

**Usage**:
```bash
export SCOUT_DB_PATH=/custom/path/to/db
```

**What it affects**:
- ChromaDB database location
- Embedding storage
- Persistent index data

### SCOUT_MODEL

Controls which sentence-transformer model is used for generating code embeddings.

**Default**: `sentence-transformers/multi-qa-mpnet-base-dot-v1`

**Usage**:
```bash
export SCOUT_MODEL=sentence-transformers/all-MiniLM-L6-v2
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

**Example configurations**:

```bash
# Use default location (recommended)
export SCOUT_DB_PATH=~/.scout/db

# Use project-specific location
export SCOUT_DB_PATH=./project_indexes

# Use shared team location
export SCOUT_DB_PATH=/shared/team/code_indexes
```

### PYTHONPATH

**NOT required** if you used the recommended setup (`./setup.sh` or `pip install -e .`).

**Only needed if**:
- You manually installed dependencies without using `pip install -e .`
- You're running Scout in development mode without package installation

**Usage**:
```bash
export PYTHONPATH=/absolute/path/to/Scout/src
```

**What it does**:
- Allows Python to find the `scout` module when not installed as a package
- Must point to the `src/` directory

## MCP Configuration

### .mcp.json

Used by MCP clients (like Claude Code) to connect to the Scout server.

**Location**: Project root or Claude Code configuration directory

**Example**:
```json
{
  "mcpServers": {
    "scout": {
      "command": "/absolute/path/to/Scout/venv/bin/python3",
      "args": [
        "/absolute/path/to/Scout/src/scout/server.py"
      ],
      "env": {
        "SCOUT_DB_PATH": "~/.scout/db"
      }
    }
  }
}
```

**Configuration fields**:
- `command`: Python interpreter from virtual environment (recommended)
- `args`: Path to the MCP server script
- `env.SCOUT_DB_PATH`: Database location

**Note**: PYTHONPATH is not needed if you used the recommended setup (`./setup.sh` or `pip install -e .`). Only add PYTHONPATH to the `env` section if you're running Scout without package installation.

## Stack Configuration

### ~/.scout/stack.json

Automatically created and maintained by Scout. Tracks indexed repositories.

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

### ~/.scout/dependencies.json

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

You can configure Scout to only track packages from your organization:

```python
from scout.dependency_storage import DependencyStorage

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
from scout.embeddings import EmbeddingStore

# Different databases for different projects
frontend_store = EmbeddingStore(
    db_path="~/.scout/frontend_db",
    collection_name="frontend_index"
)

backend_store = EmbeddingStore(
    db_path="~/.scout/backend_db",
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
1. Check `SCOUT_DB_PATH` is set correctly
2. Ensure path has write permissions
3. Use absolute paths, not relative
4. Expand `~` to full home directory path

### PYTHONPATH Issues

**Problem**: `ModuleNotFoundError: No module named 'scout'`

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
ls -la ~/.scout/

# Fix permissions
chmod 755 ~/.scout/
chmod 644 ~/.scout/*.json
```

## Best Practices

1. **Use the default database location** unless you have a specific reason not to
2. **Set environment variables in your shell profile** (`.bashrc`, `.zshrc`) for persistence
3. **Use absolute paths** in all configuration files
4. **Back up `~/.scout/`** directory if you have large indices
5. **One database per development environment** (work, personal, etc.)
6. **Configure organization prefixes** to reduce noise from external dependencies

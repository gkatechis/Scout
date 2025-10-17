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

Required for running mcpIndexer from source.

**Usage**:
```bash
export PYTHONPATH=/absolute/path/to/mcpIndexer/src
```

**Why it's needed**:
- Allows Python to find the `mcpindexer` module
- Required for running scripts and the MCP server
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
      "command": "python3",
      "args": [
        "/absolute/path/to/mcpIndexer/src/mcpindexer/server.py"
      ],
      "env": {
        "PYTHONPATH": "/absolute/path/to/mcpIndexer/src",
        "MCP_INDEXER_DB_PATH": "~/.mcpindexer/db"
      }
    }
  }
}
```

**Configuration fields**:
- `command`: Python interpreter to use
- `args`: Path to the MCP server script
- `env.PYTHONPATH`: Path to mcpIndexer src directory
- `env.MCP_INDEXER_DB_PATH`: Database location

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

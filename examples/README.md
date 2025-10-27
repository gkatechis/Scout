# Examples

This directory contains example scripts demonstrating how to use mcpIndexer.

## Demo Scripts

### `demo.py`
Complete end-to-end demo showing the full indexing pipeline:
- Parse sample code files (Python and JavaScript)
- Chunk code into semantic units
- Generate embeddings
- Perform semantic searches
- Symbol lookup
- Language-filtered search

Run with:
```bash
python3 examples/demo.py
```

### `test_real_repo.py`
Example of indexing a real repository. Update the repo path to test with your own repositories.

### `test_monolith.py`
Example of indexing a large monolithic repository.

### `test_chunker.py`
Example demonstrating the code chunking functionality.

## Organization-Specific Examples

The following scripts were originally created for Zendesk repositories but can be adapted for any organization:

### `index_all_zendesk.py`
Example script that:
- Discovers all git repositories in a directory
- Indexes each repository
- Skips already-indexed repos
- Provides progress and summary statistics

**To adapt for your organization:**
1. Change the `zendesk_base` path to your repository directory
2. Optionally configure organization prefixes for package filtering

### `reindex_zendesk_monolith.py`
Example of reindexing a specific large repository with progress tracking.

### `reindex_all_with_dependencies.py`
Example showing how to:
- Reindex multiple repositories
- Analyze cross-repository dependencies
- Suggest missing repositories to add

## Usage Pattern

All examples follow this general pattern:

```python
from mcpindexer.indexer import MultiRepoIndexer
from mcpindexer.embeddings import EmbeddingStore

# Initialize store
db_path = os.getenv("MCP_INDEXER_DB_PATH", "~/.mcpindexer/db")
store = EmbeddingStore(db_path=db_path, collection_name="mcp_code_index")

# Create indexer
indexer = MultiRepoIndexer(embedding_store=store)

# Add and index repository
result = indexer.add_repo(
    repo_path="/path/to/repo",
    repo_name="my-repo",
    auto_index=True
)

# Search
results = store.semantic_search("authentication logic", n_results=10)
```

## Running Examples

**Prerequisites**:
1. Complete setup: Run `./setup.sh` from the project root (see [README.md](../README.md))
2. Activate the virtual environment: `source venv/bin/activate`

Then run any example:
```bash
python3 examples/demo.py
```

## Configuration

Examples use the same configuration as the main CLI. See:
- [README.md](../README.md) - Quick start and basic usage
- [docs/CONFIGURATION.md](../docs/CONFIGURATION.md) - Advanced configuration

## Notes

- These are examples and may need modification for your specific use case
- Edit hardcoded paths in scripts to match your local setup
- Examples assume you've completed installation with `pip install -e .`

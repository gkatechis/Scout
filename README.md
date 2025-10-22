# MCP Indexer

Semantic code search indexer for AI tools via the Model Context Protocol (MCP).

## For AI Coding Agents

**If you're an AI agent working on this project**, please read [AGENTS.MD](AGENTS.MD) first. It contains instructions for using Beads issue tracking to manage tasks systematically across sessions.

## Overview

MCP Indexer provides intelligent code search capabilities to any MCP-compatible LLM (Claude, etc.). It indexes your repositories using semantic embeddings, enabling natural language code search, symbol lookups, and cross-repo dependency analysis.

## Features

- **Semantic Search**: Natural language queries find relevant code by meaning, not just keywords

- **Multi-Language Support**: Python, JavaScript, TypeScript, Ruby, Go

- **Cross-Repo Analysis**: Detect dependencies and suggest missing repos

- **Incremental Updates**: Track git commits and reindex only when needed

- **MCP Integration**: Works with any MCP-compatible LLM client

- **Stack Management**: Persistent configuration for repo collections

## Installation

### Prerequisites

- Python 3.8 or higher

- pip

### Automated Setup (Recommended)

1. Clone the repository:

```bash
git clone <https://github.com/gkatechis/mcpIndexer.git>
cd mcpIndexer

```text

2. Run the setup script:

```bash
./setup.sh

```text

This script will:

- Create a virtual environment at `./venv`

- Install all dependencies

- Generate `.mcp.json` configuration with correct paths

- Create the `~/.mcpindexer` directory

- Show you environment variables to add to your shell profile

3. Add environment variables to your shell profile (optional, for CLI usage):

```bash

## Add to ~/.zshrc or ~/.bashrc

export PYTHONPATH="/absolute/path/to/mcpIndexer/src:$PYTHONPATH"
export MCP_INDEXER_DB_PATH=~/.mcpindexer/db

```text

### Manual Setup (Alternative)

1. Clone the repository:

```bash
git clone <https://github.com/gkatechis/mcpIndexer.git>
cd mcpIndexer

```text

2. Create and activate a virtual environment:

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

```text

3. Install dependencies:

```bash
pip install -r requirements.txt

## OR install as editable package:


## pip install -e .


```text

4. Create configuration directory:

```bash
mkdir -p ~/.mcpindexer

```text

5. Configure MCP integration (for Claude Code or other MCP clients):

```bash
cp .mcp.json.example .mcp.json

## Edit .mcp.json and update paths to your installation directory


```text

6. Set up environment variables:

```bash
export PYTHONPATH=/absolute/path/to/mcpIndexer/src
export MCP_INDEXER_DB_PATH=~/.mcpindexer/db  # Optional, defaults to this location

```text

## Quick Start

### 1. Try the Demo

Run the demo to see mcpIndexer in action:

```bash

## If you used setup.sh, activate the virtual environment first:

source venv/bin/activate

python3 examples/demo.py

```text

### 2. Index Your Repositories

```python

import os
from mcpindexer.indexer import MultiRepoIndexer
from mcpindexer.embeddings import EmbeddingStore

## Initialize with your database path

db_path = os.getenv("MCP_INDEXER_DB_PATH", os.path.expanduser("~/.mcpindexer/db"))
store = EmbeddingStore(db_path=db_path, collection_name='mcp_code_index')
indexer = MultiRepoIndexer(store)

## Add and index your repository

indexer.add_repo(
    repo_path='/path/to/your/repo',
    repo_name='my-repo',
    auto_index=True
)

```text

### 3. Use with MCP Clients

Once configured in `.mcp.json`, the MCP server automatically starts when you use an MCP client like Claude Code.

The MCP server exposes 13 tools:

**Search Tools:**

- `semantic_search` - Natural language code search

- `find_definition` - Find where symbols are defined

- `find_references` - Find where symbols are used

- `find_related_code` - Find architecturally related files

**AI-Powered Q&A:**

- `answer_question` - Retrieve relevant code context for questions. The agent will use this context to provide comprehensive answers.

**Repository Management:**

- `add_repo_to_stack` - Add a new repository

- `remove_repo` - Remove a repository

- `list_repos` - List all indexed repos

- `get_repo_stats` - Get detailed repo statistics

- `reindex_repo` - Force reindex a repository

**Cross-Repo Analysis:**

- `get_cross_repo_dependencies` - Find dependencies between repos

- `suggest_missing_repos` - Suggest repos to add based on imports

**Stack Management:**

- `get_stack_status` - Get overall indexing status

## CLI Commands

### Check for Updates

Check which repos need reindexing:

```bash
python3 -m mcpindexer check-updates

```text

### Reindex Changed Repos

Automatically reindex repos with new commits:

```bash
python3 -m mcpindexer reindex-changed

```text

### Stack Status

View current stack status:

```bash
python3 -m mcpindexer status

```text

### Install Git Hooks

Auto-reindex on git pull:

```bash
python3 -m mcpindexer install-hook /path/to/repo

```text

This installs a post-merge hook that triggers reindexing after pulls.

## Usage Examples

### AI-Powered Question Answering

The `answer_question` tool retrieves relevant code context for your questions. When used with an AI agent (like Claude Code), the agent will automatically use this context to provide comprehensive answers.

**How it works:**
1. You ask a question via the MCP tool
2. The tool performs semantic search to find relevant code
3. The tool returns formatted code snippets with metadata
4. The AI agent (Claude Code, etc.) uses this context to answer your question

**Example usage with Claude Code:**

```text
User: "How does authentication work in this codebase?"

Claude Code calls: answer_question(question="How does authentication work in this codebase?")

Tool returns: Code snippets from authentication-related files

Claude Code then: Analyzes the returned code and provides a comprehensive answer

```text

**No API keys needed!** The tool just retrieves context - your AI agent does the analysis.

**Example Questions:**

- "How does authentication work in this codebase?"

- "What database models are used for user management?"

- "Explain the API error handling strategy"

- "Where is logging configured?"

- "How are dependencies managed?"

### Semantic Search

```python

import os
from mcpindexer.embeddings import EmbeddingStore

db_path = os.getenv("MCP_INDEXER_DB_PATH", os.path.expanduser("~/.mcpindexer/db"))
store = EmbeddingStore(db_path=db_path, collection_name='mcp_code_index')

## Natural language queries

results = store.semantic_search(
    query="authentication logic",
    n_results=10
)

for result in results:
    print(f"{result.file_path}:{result.metadata['start_line']}")
    print(f"  {result.symbol_name} - Score: {result.score:.4f}")

```text

### Find Symbol Definitions

```python
results = store.find_by_symbol(
    symbol_name="authenticate_user",
    repo_filter=["my-backend"]
)

```text

### Cross-Repo Dependencies

```python

from mcpindexer.indexer import MultiRepoIndexer

indexer = MultiRepoIndexer(store)

## Find dependencies between repos

cross_deps = indexer.get_cross_repo_dependencies()

## Suggest missing repos to add

suggestions = indexer.suggest_missing_repos()

```text

## Configuration

### Environment Variables

- `MCP_INDEXER_DB_PATH`- Database path (default:`~/.mcpindexer/db`)

- `PYTHONPATH`- Must include the`src/` directory of your installation

### Stack Configuration

Configuration is stored at `~/.mcpindexer/stack.json`:

```json

{
  "version": "1.0",
  "repos": {
    "my-repo": {
      "name": "my-repo",
      "path": "/path/to/repo",
      "status": "indexed",
      "last_indexed": "2025-10-14T12:34:56.789Z",
      "last_commit": "abc123...",
      "files_indexed": 162,
      "chunks_indexed": 302,
      "auto_reindex": true
    }
  }
}

```text

## Architecture

### Components

1. **Parser** (`parser.py`) - Tree-sitter based multi-language AST parsing
2. **Chunker** (`chunker.py`) - Intelligent code chunking respecting AST boundaries
3. **Embeddings** (`embeddings.py`) - ChromaDB + sentence-transformers for semantic search
4. **Indexer** (`indexer.py`) - Orchestrates parsing → chunking → embedding → storage
5. **Dependency Analyzer** (`dependency_analyzer.py`) - Tracks imports and dependencies
6. **Stack Config** (`stack_config.py`) - Persistent configuration management
7. **MCP Server** (`server.py`) - Exposes tools via Model Context Protocol
8. **CLI** (`cli.py`) - Command-line interface

### Indexing Pipeline

```text
Code File → Parser → AST → Chunker → Semantic Chunks
                                            ↓
                                      Embeddings
                                            ↓
                                      ChromaDB Store

```text

## Performance

Based on testing with real-world repos:

- **Speed**: ~56 files/sec

- **Zendesk App Framework**: 162 files, 302 chunks in 1.86s

- **3 Repos**: 255 files, 595 chunks in 4.58s

- **Search Latency**: ~100-200ms per query

## Troubleshooting

### Issue: "ModuleNotFoundError: No module named 'tree_sitter'"

**Solution**: Install dependencies

```bash
pip install -r requirements.txt

```text

### Issue: Slow indexing

**Causes**:

- Large files with many symbols

- Complex nested structures

- First-time embedding generation

**Solutions**:

- Use file filters to skip test/build directories

- Increase chunk size target

- Use GPU-accelerated embeddings (if available)

### Issue: Poor search results

**Causes**:

- Query too generic

- Code not indexed

- Wrong language filter

**Solutions**:

- Use more specific queries ("JWT token validation" vs "auth")

- Check `list_repos` to verify indexing

- Try without language filter

- Increase `n_results` parameter

### Issue: Out of memory

**Causes**:

- Indexing too many repos at once

- Very large monoliths

**Solutions**:

- Index repos individually

- Increase system memory

- Use incremental indexing (git commit-based)

### Issue: Git hooks not triggering

**Causes**:

- Hook not executable

- PYTHONPATH not set

- Hook overwritten

**Solutions**:

```bash

## Check hook exists and is executable

ls -la /path/to/repo/.git/hooks/post-merge

## Make executable

chmod +x /path/to/repo/.git/hooks/post-merge

## Test manually

cd /path/to/repo && .git/hooks/post-merge

```text

### Issue: Stale results after code changes

**Solutions**:

```bash


## Force reindex specific repo

python3 -c "
from mcpindexer.indexer import MultiRepoIndexer, EmbeddingStore
store = EmbeddingStore('./mcp_index_data', 'mcp_code_index')
indexer = MultiRepoIndexer(store)
indexer.repo_indexers['my-repo'].reindex(force=True)
"

## Or use CLI

python3 -m mcpindexer reindex-changed

```text

## Example Queries

### Finding Implementations

- "password hashing"

- "JWT token validation"

- "database connection pool"

- "API rate limiting"

### Finding Patterns

- "error handling"

- "logging configuration"

- "caching strategy"

- "retry logic"

### Finding Components

- "user authentication"

- "payment processing"

- "email sending"

- "file upload handling"

### Architecture Understanding

- "dependency injection setup"

- "middleware configuration"

- "router registration"

- "database migration"

## Testing

```bash


## Run all tests

export PYTHONPATH=/path/to/mcpIndexer/src
python3 -m pytest tests/ -v

## Run specific test file

python3 -m pytest tests/test_embeddings.py -v

## Run example scripts

python3 examples/demo.py

```text

See the `examples/` directory for more usage examples.

## Contributing

The codebase is organized by component:

- `src/mcpindexer/` - Main source code

- `tests/` - Test suite (130+ tests)

- `test_*.py` - Integration test scripts

All components are independently tested with comprehensive coverage.

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Support

For issues or questions, please open an issue on the repository.

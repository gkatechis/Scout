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
git clone <<<<https://github.com/gkatechis/mcpIndexer.git>>>>
cd mcpIndexer

```

2. Run the setup script:

```bash
./setup.sh

```

This script will:

- Create a virtual environment at `./venv`

- Install all dependencies

- Generate `.mcp.json` configuration with correct paths

- Create the `~/.mcpindexer` directory

- Show you environment variables to add to your shell profile

3. Add environment variables to your shell profile (optional, for CLI usage):

```bash

# Add to ~/.zshrc or ~/.bashrc

export PYTHONPATH="/absolute/path/to/mcpIndexer/src:$PYTHONPATH"
export MCP_INDEXER_DB_PATH=~/.mcpindexer/db

```

### Manual Setup (Alternative)

1. Clone the repository:

```bash
git clone <<<<https://github.com/gkatechis/mcpIndexer.git>>>>
cd mcpIndexer

```

2. Create and activate a virtual environment:

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

```

3. Install dependencies:

```bash
pip install -r requirements.txt

# OR install as editable package:

# pip install -e .

```

4. Create configuration directory:

```bash
mkdir -p ~/.mcpindexer

```

5. Configure MCP integration (for Claude Code or other MCP clients):

```bash
cp .mcp.json.example .mcp.json

# Edit .mcp.json and update paths to your installation directory

```

6. Set up environment variables:

```bash
export PYTHONPATH=/absolute/path/to/mcpIndexer/src
export MCP_INDEXER_DB_PATH=~/.mcpindexer/db  # Optional, defaults to this location

```

## Quick Start

### 1. Try the Demo

Run the demo to see mcpIndexer in action:

```bash

# If you used setup.sh, activate the virtual environment first:

source venv/bin/activate

python3 examples/demo.py

```

### 2. Index Your Repositories

```python

import os
from mcpindexer.indexer import MultiRepoIndexer
from mcpindexer.embeddings import EmbeddingStore

# Initialize with your database path

db_path = os.getenv("MCP_INDEXER_DB_PATH", os.path.expanduser("~/.mcpindexer/db"))
store = EmbeddingStore(db_path=db_path, collection_name='mcp_code_index')
indexer = MultiRepoIndexer(store)

# Add and index your repository

indexer.add_repo(
    repo_path='/path/to/your/repo',
    repo_name='my-repo',
    auto_index=True
)

```

### 3. Use with MCP Clients

Once configured in `.mcp.json`, the MCP server automatically starts when you use an MCP client like Claude Code.

## MCP Tools Reference

The MCP server exposes 13 tools organized by functionality:

### AI-Powered Q&A (Recommended for Users)

**`answer_question`** - Ask questions about your codebase and get answers

- **Use when:** You want a natural language answer to a question about your code

- **Returns:** Relevant code snippets + file references + analysis prompt for the AI agent

- **Example:** "How does authentication work?" → Agent analyzes code and explains it

- **Best for:** End users asking questions about codebases

### Search Tools (For Advanced Queries)

**`semantic_search`** - Natural language code search

- **Use when:** You want raw search results to analyze yourself or build upon

- **Returns:** List of code snippets with metadata (file, lines, relevance scores)

- **Example:** "authentication logic" → Returns 10 relevant code snippets

- **Best for:** Programmatic access or when you need full search result details

- **Note:** `answer_question`uses this internally - prefer`answer_question` for Q&A

**`find_definition`** - Find where a symbol is defined

- **Use when:** You know a function/class name and want to find its definition

- **Returns:** File path, line numbers, and definition code

- **Example:** "authenticate_user" → Shows where the function is defined

**`find_references`** - Find all usages of a symbol

- **Use when:** You want to see everywhere a function/class is used

- **Returns:** List of files and lines where the symbol appears

- **Example:** "authenticate_user" → Shows all calls to this function

**`find_related_code`** - Find architecturally related files

- **Use when:** You want to find files that are similar in structure/purpose

- **Returns:** List of related files based on imports, patterns, and architecture

- **Example:** Given "auth/login.py" → Finds other auth-related files

### Repository Management

**`add_repo_to_stack`** - Add a new repository to index

- **Parameters:** `repo_path`(local path),`repo_name` (identifier)

- **Use when:** Adding a new codebase to search

**`remove_repo`** - Remove a repository from the stack

- **Parameters:** `repo_name`

- **Use when:** Removing a codebase from search

**`list_repos`** - List all indexed repositories

- **Returns:** List of repo names, paths, and basic stats

- **Use when:** Checking what's currently indexed

**`get_repo_stats`** - Get detailed repository statistics

- **Parameters:** `repo_name`

- **Returns:** File count, chunk count, languages, dependencies

- **Use when:** Understanding index status for a specific repo

**`reindex_repo`** - Force reindex a repository

- **Parameters:** `repo_name`, `force` (optional)

- **Use when:** Code has changed and you want to refresh the index

### Cross-Repo Analysis

**`get_cross_repo_dependencies`** - Find dependencies between repositories

- **Returns:** Map of which repos depend on which

- **Use when:** Understanding relationships between multiple codebases

**`suggest_missing_repos`** - Suggest repositories to add

- **Returns:** List of repos that are imported but not indexed

- **Use when:** Discovering missing dependencies in your stack

**`get_stack_status`** - Get overall stack status

- **Returns:** Summary of all indexed repos, total files, languages

- **Use when:** Getting an overview of your entire indexed stack

## CLI Commands

### Check for Updates

Check which repos need reindexing:

```bash
mcpindexer check-updates

```

### Reindex Changed Repos

Automatically reindex repos with new commits:

```bash
mcpindexer reindex-changed

```

### Stack Status

View current stack status:

```bash
mcpindexer status

```

### Install Git Hooks

Auto-reindex on git pull:

```bash
mcpindexer install-hook /path/to/repo

```

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

```
User: "How does authentication work in this codebase?"

Claude Code calls: answer_question(question="How does authentication work in this codebase?")

Tool returns: Code snippets from authentication-related files

Claude Code then: Analyzes the returned code and provides a comprehensive answer

```

**No API keys needed!** The tool just retrieves context - your AI agent does the analysis.

**Example Questions:**

- "How does authentication work in this codebase?"

- "What database models are used for user management?"

- "Explain the API error handling strategy"

- "Where is logging configured?"

- "How are dependencies managed?"

### Using Semantic Search (Advanced)

The `semantic_search`tool is lower-level than`answer_question` and returns raw search results. Use it when you need programmatic access to search results or want to build your own analysis on top.

**Via MCP:**

```

## AI agent calls:

semantic_search(query="authentication logic", limit=10)

## Returns:

1. src/auth/login.py:45 (authenticate_user) - Score: 0.92
   [code snippet]
2. src/auth/tokens.py:12 (generate_token) - Score: 0.87
   [code snippet]
...

```

**Via Python API:**

```python

import os
from mcpindexer.embeddings import EmbeddingStore

db_path = os.getenv("MCP_INDEXER_DB_PATH", os.path.expanduser("~/.mcpindexer/db"))
store = EmbeddingStore(db_path=db_path, collection_name='mcp_code_index')

# Natural language queries

results = store.semantic_search(
    query="authentication logic",
    n_results=10
)

for result in results:
    print(f"{result.file_path}:{result.metadata['start_line']}")
    print(f"  {result.symbol_name} - Score: {result.score:.4f}")

```

### Finding Symbol Definitions and References

**Via MCP:**

```

## Find where a symbol is defined:

find_definition(symbol="authenticate_user")

## Find all usages:

find_references(symbol="authenticate_user")

```

**Via Python API:**

```python

# Find definition

results = store.find_by_symbol(
    symbol_name="authenticate_user",
    repo_filter=["my-backend"]
)

```

### Cross-Repo Dependencies

```python

from mcpindexer.indexer import MultiRepoIndexer

indexer = MultiRepoIndexer(store)

# Find dependencies between repos

cross_deps = indexer.get_cross_repo_dependencies()

# Suggest missing repos to add

suggestions = indexer.suggest_missing_repos()

```

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

```

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

```
Code File → Parser → AST → Chunker → Semantic Chunks
                                            ↓
                                      Embeddings
                                            ↓
                                      ChromaDB Store

```

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

```

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

# Check hook exists and is executable

ls -la /path/to/repo/.git/hooks/post-merge

# Make executable

chmod +x /path/to/repo/.git/hooks/post-merge

# Test manually

cd /path/to/repo && .git/hooks/post-merge

```

### Issue: Stale results after code changes

**Solutions**:

```bash

# Force reindex specific repo

python3 -c "
from mcpindexer.indexer import MultiRepoIndexer, EmbeddingStore
store = EmbeddingStore('./mcp_index_data', 'mcp_code_index')
indexer = MultiRepoIndexer(store)
indexer.repo_indexers['my-repo'].reindex(force=True)
"

# Or use CLI

mcpindexer reindex-changed

```

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

# Run all tests

export PYTHONPATH=/path/to/mcpIndexer/src
python3 -m pytest tests/ -v

# Run specific test file

python3 -m pytest tests/test_embeddings.py -v

# Run example scripts

python3 examples/demo.py

```

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

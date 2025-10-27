# MCP Indexer

Semantic code search indexer for AI tools via the Model Context Protocol (MCP).

⚡ **Want to get started quickly?** See [QUICKSTART.md](QUICKSTART.md) for a 5-minute setup guide.

## Documentation

- **[QUICKSTART.md](QUICKSTART.md)** - Get running in 5 minutes

- **[README.md](README.md)** (this file) - Complete documentation and reference

- **[docs/CONFIGURATION.md](docs/CONFIGURATION.md)** - Detailed configuration and advanced options

- **[TESTING.md](TESTING.md)** - Testing guide and pre-release checklist

- **[examples/README.md](examples/README.md)** - Example scripts and usage patterns

- **[AGENTS.MD](AGENTS.MD)** - Instructions for AI coding agents

**Note**: The root directory contains Zendesk-specific documentation files (`ZENDESK_*.md`) that demonstrate mcpIndexer usage with a large organization's codebase. These serve as examples and can be adapted for your organization.

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

**Quick Start:** Most users should use the [Automated Setup](#automated-setup-recommended) below. Use [Manual Setup](#manual-setup-alternative) only if the automated script fails or you need custom configuration.

### Prerequisites

**Python 3.8 or higher** - Check your version:

```bash
python3 --version

```text

If you need to install or upgrade Python:

- **macOS**: `brew install python@3.11` or download from <<<<https://python.org/downloads/>>>>

- **Ubuntu/Debian**: `sudo apt install python3.11 python3.11-venv`

- **Windows**: Download from <<<<https://python.org/downloads/>>>>

**Multiple Python versions?** If you have several versions installed, specify which one to use when creating the virtual environment:

```bash

## Use specific Python version for venv

python3.11 -m venv venv

## or

python3.9 -m venv venv

```text

**Why virtual environments?** They isolate dependencies per project, preventing conflicts between different Python projects on your system.

### Automated Setup (Recommended)

1. Clone the repository:

```bash
git clone <<<<<<<https://github.com/gkatechis/mcpIndexer.git>>>>>>>
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

- Optionally add a shell alias for easy venv activation

**That's it!** No environment variables are required for basic usage.

**Tip**: During setup, you can add a `mcpindexer-shell` alias to easily activate the virtual environment in future terminal sessions.

### Environment Variables (Optional)

Environment variables are **optional** - setup.sh configures sensible defaults.

For advanced configuration (custom database paths, etc.), see [CONFIGURATION.md](docs/CONFIGURATION.md).

### Manual Setup (Alternative)

**Use this method only if:**

- The automated setup script fails

- You need custom Python version or dependency management

- You're integrating mcpIndexer into an existing project

Otherwise, use [Automated Setup](#automated-setup-recommended) above.

<details>
<summary>Click to expand manual setup instructions</summary>

1. Clone the repository:

```bash
git clone <<<<<<<https://github.com/gkatechis/mcpIndexer.git>>>>>>>
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

6. (Optional) Configure environment variables if needed:

See [docs/CONFIGURATION.md](docs/CONFIGURATION.md) for advanced configuration options.

</details>

---

## Quick Start

**Before using any CLI commands, activate the virtual environment:**

```bash
source venv/bin/activate

```text

**Tip**: If you added the shell alias during setup, you can use:

```bash
mcpindexer-shell

```text

You'll need to activate the venv each time you open a new terminal.

### Interactive Setup (Recommended for First-Time Users)

The easiest way to get started is with the interactive wizard:

```bash
mcpindexer init

```text

This will guide you through:

- Verifying your installation

- Adding your first repository

- Running a demo search

- Learning next steps

### 1. Add Repositories to Index

The easiest way to add repositories is using the CLI:

```bash

## Add a local repository

mcpindexer add /path/to/local/repo

## Add a repository from GitHub (auto-clones and indexes)

mcpindexer add <<<https://github.com/user/repo>>>

## Specify a custom name

mcpindexer add <<<https://github.com/user/repo>>> --name my-custom-name

## Clone to a specific directory

mcpindexer add <<<https://github.com/user/repo>>> --clone-dir ~/projects

```text

### 2. Try the Demo

Run the demo to see mcpIndexer in action:

```bash
python3 examples/demo.py

```text

### 3. Index Repositories Programmatically (Alternative)

You can also add repositories using Python:

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

### 4. Use with MCP Clients

Once configured in `.mcp.json`, the MCP server automatically starts when you use an MCP client like Claude Code.

## CLI Commands Reference

Quick reference for all available CLI commands:

```bash

## Getting started

mcpindexer init                           # Interactive setup wizard (recommended)
mcpindexer check                          # Verify installation is working

## Repository management

mcpindexer add <path>                     # Add local repository
mcpindexer add <url>                      # Clone and add from GitHub
mcpindexer add <path> --name <name>       # Add with custom name
mcpindexer status                         # Show stack status

## Keeping repos up to date

mcpindexer check-updates                  # Check which repos need reindexing
mcpindexer reindex-changed                # Reindex repos with new commits

## Recovery and maintenance

mcpindexer recover                        # Recover from interrupted indexing
mcpindexer recover --force                # Force recovery without confirmation

## Git integration

mcpindexer install-hook <repo-path>       # Auto-reindex on git pull

```text

For detailed help on any command:

```bash
mcpindexer --help
mcpindexer <command> --help

```text

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

### Add Repository

Add a repository to the index (local path or GitHub URL):

```bash

## Add local repository

mcpindexer add /path/to/repo

## Add from GitHub (auto-clones)

mcpindexer add <<<https://github.com/user/repo>>>

## With custom name

mcpindexer add <<<https://github.com/user/repo>>> --name my-repo

## Specify clone directory (default: ~/Code)

mcpindexer add <<<https://github.com/user/repo>>> --clone-dir ~/projects

```text

### Check for Updates

Check which repos need reindexing:

```bash
mcpindexer check-updates

```text

### Reindex Changed Repos

Automatically reindex repos with new commits:

```bash
mcpindexer reindex-changed

```text

### Stack Status

View current stack status:

```bash
mcpindexer status

```text

### Install Git Hooks

Auto-reindex on git pull:

```bash
mcpindexer install-hook /path/to/repo

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

### Using Semantic Search (Advanced)

The `semantic_search`tool is lower-level than`answer_question` and returns raw search results. Use it when you need programmatic access to search results or want to build your own analysis on top.

**Via MCP:**

```text

## AI agent calls:

semantic_search(query="authentication logic", limit=10)

## Returns:

1. src/auth/login.py:45 (authenticate_user) - Score: 0.92
   [code snippet]
2. src/auth/tokens.py:12 (generate_token) - Score: 0.87
   [code snippet]
...

```text

**Via Python API:**

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

### Finding Symbol Definitions and References

**Via MCP:**

```text

## Find where a symbol is defined:

find_definition(symbol="authenticate_user")

## Find all usages:

find_references(symbol="authenticate_user")

```text

**Via Python API:**

```python

## Find definition

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

For detailed configuration options including environment variables, custom database locations, MCP setup, and advanced features, see [docs/CONFIGURATION.md](docs/CONFIGURATION.md).

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

### Issue: Python version conflicts or dependency errors

**Symptoms**:

- "ModuleNotFoundError" when running mcpindexer

- "version conflict" errors during installation

- Dependencies fail to install

**Solutions**:

1. **Verify you're using Python 3.8+**:

   ```bash
   python3 --version

```text

2. **Create a fresh virtual environment with a specific Python version**:

   ```bash

   # Remove old venv if it exists
   rm -rf venv

   # Create new venv with specific Python version
   python3.11 -m venv venv  # or python3.9, python3.10, etc.
   source venv/bin/activate

   # Upgrade pip first
   pip install --upgrade pip setuptools wheel

   # Install dependencies
   pip install -e .

```text

3. **Still having issues?** Install from requirements.txt first:

   ```bash
   pip install -r requirements.txt
   pip install -e .

```text

### Issue: "ModuleNotFoundError: No module named 'tree_sitter'"

**Solution**: Make sure virtual environment is activated and dependencies are installed

```bash
source venv/bin/activate
pip install -r requirements.txt

```text

### Debug Logging

For troubleshooting issues, you can enable debug logging with the `--debug`or`--verbose` flags:

```bash

## Enable verbose output (INFO level logging)

mcpindexer --verbose <command>

## Enable debug output (DEBUG level logging, saves to file)

mcpindexer --debug <command>

```text

Debug logs are written to: `~/.mcpindexer/logs/mcpindexer.log`

This is helpful when:

- Investigating indexing failures

- Understanding performance bottlenecks

- Reporting bugs (include log excerpts)

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

- Hook overwritten

- Virtual environment not activated

**Solutions**:

```bash

## Check hook exists and is executable

ls -la /path/to/repo/.git/hooks/post-merge

## Make executable

chmod +x /path/to/repo/.git/hooks/post-merge

## Test manually

cd /path/to/repo && .git/hooks/post-merge

```text

### Issue: Interrupted indexing

**Symptoms**:

- Repository stuck in "indexing" status

- Indexing process was killed or crashed

**Solutions**:

```bash

## Check for stuck repositories

mcpindexer status

## Recover automatically

mcpindexer recover

```text

### Issue: Stale results after code changes

**Solutions**:

```bash

## Force reindex specific repo

python3 -c "
from mcpindexer.indexer import MultiRepoIndexer, EmbeddingStore
import os
db_path = os.path.expanduser('~/.mcpindexer/db')
store = EmbeddingStore(db_path, 'mcp_code_index')
indexer = MultiRepoIndexer(store)
indexer.repo_indexers['my-repo'].reindex(force=True)
"

## Or use CLI

mcpindexer reindex-changed

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

## Activate virtual environment first

source venv/bin/activate

## Run all tests (PYTHONPATH not needed - configured in pyproject.toml)

pytest tests/ -v

## Run specific test file

pytest tests/test_embeddings.py -v

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

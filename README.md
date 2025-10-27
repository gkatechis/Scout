# MCP Indexer

Semantic code search indexer for AI tools via the Model Context Protocol (MCP).

⚡ **Want to get started quickly?** See [QUICKSTART.md](QUICKSTART.md) for a 5-minute setup guide.

## Documentation

- **[QUICKSTART.md](QUICKSTART.md)** - Get running in 5 minutes
- **[README.md](README.md)** (this file) - Overview and reference
- **[docs/CONFIGURATION.md](docs/CONFIGURATION.md)** - Configuration options
- **[docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md)** - Common issues and solutions
- **[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)** - System architecture and internals
- **[TESTING.md](TESTING.md)** - Testing guide
- **[examples/README.md](examples/README.md)** - Example scripts and usage patterns
- **[CONTRIBUTING.md](CONTRIBUTING.md)** - How to contribute
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

**Quick Start:** Most users should use the automated setup script. Use manual setup only if the automated script fails or you need custom configuration.

### Prerequisites

**Python 3.10 or higher** - Check your version:
```bash
python3 --version
```

If you need to install or upgrade Python:
- **macOS**: `brew install python@3.11` or download from https://python.org/downloads/
- **Ubuntu/Debian**: `sudo apt install python3.11 python3.11-venv`
- **Windows**: Download from https://python.org/downloads/

### Automated Setup (Recommended)

1. Clone the repository:
```bash
git clone https://github.com/gkatechis/mcpIndexer.git
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
- Optionally add shell aliases for convenience

Environment variables are **optional** - setup.sh configures sensible defaults. For advanced configuration (custom database paths, etc.), see [CONFIGURATION.md](docs/CONFIGURATION.md).

<details>
<summary><b>Manual Setup (Click to expand)</b></summary>

**Use this method only if:**
- The automated setup script fails
- You need custom Python version or dependency management
- You're integrating mcpIndexer into an existing project

**Steps:**

1. Clone the repository:
```bash
git clone https://github.com/gkatechis/mcpIndexer.git
cd mcpIndexer
```

2. Create and activate a virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -e .
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

6. (Optional) Configure environment variables if needed:
See [docs/CONFIGURATION.md](docs/CONFIGURATION.md) for advanced configuration options.

</details>

## Quick Start

### 1. Activate Virtual Environment

**Before using any commands, activate the virtual environment:**
```bash
source venv/bin/activate
```

You'll need to activate the venv each time you open a new terminal.

### 2. Interactive Setup

The easiest way to get started:
```bash
mcpindexer init
```

This wizard will:
- Verify your installation
- Add your first repository
- Run a demo search
- Explain next steps

### 3. Add Repositories

```bash
# Add a local repository
mcpindexer add /path/to/local/repo

# Add from GitHub (auto-clones and indexes)
mcpindexer add https://github.com/user/repo

# Specify a custom name
mcpindexer add https://github.com/user/repo --name my-custom-name
```

### 4. Use with MCP Clients

Once configured in `.mcp.json`, the MCP server automatically starts when you use an MCP client like Claude Code.

## CLI Commands Reference

```bash
# Getting started
mcpindexer init                           # Interactive setup wizard
mcpindexer check                          # Verify installation

# Repository management
mcpindexer add <path>                     # Add local repository
mcpindexer add <url>                      # Clone and add from GitHub
mcpindexer status                         # Show stack status

# Keeping repos up to date
mcpindexer check-updates                  # Check which repos need reindexing
mcpindexer reindex-changed                # Reindex repos with new commits

# Recovery and maintenance
mcpindexer recover                        # Recover from interrupted indexing

# Git integration
mcpindexer install-hook <repo-path>       # Auto-reindex on git pull
```

For detailed help on any command:
```bash
mcpindexer --help
mcpindexer <command> --help
```

## MCP Tools Reference

The MCP server exposes 13 tools organized by functionality:

### AI-Powered Q&A (Recommended)

**`answer_question`** - Ask questions about your codebase and get answers
- Returns relevant code snippets + file references + analysis prompt for the AI agent
- Example: "How does authentication work?" → Agent analyzes code and explains it
- **Best for:** End users asking questions about codebases

### Search Tools

**`semantic_search`** - Natural language code search
- Returns list of code snippets with metadata (file, lines, relevance scores)
- Example: "authentication logic" → Returns 10 relevant code snippets

**`find_definition`** - Find where a symbol is defined
- Example: "authenticate_user" → Shows where the function is defined

**`find_references`** - Find all usages of a symbol
- Example: "authenticate_user" → Shows all calls to this function

**`find_related_code`** - Find architecturally related files
- Example: Given "auth/login.py" → Finds other auth-related files

### Repository Management

- **`add_repo_to_stack`** - Add a new repository to index
- **`remove_repo`** - Remove a repository from the stack
- **`list_repos`** - List all indexed repositories
- **`get_repo_stats`** - Get detailed repository statistics
- **`reindex_repo`** - Force reindex a repository

### Cross-Repo Analysis

- **`get_cross_repo_dependencies`** - Find dependencies between repositories
- **`suggest_missing_repos`** - Suggest repositories to add
- **`get_stack_status`** - Get overall stack status

For detailed tool documentation and usage examples, see [examples/README.md](examples/README.md).

## Configuration

Configuration is stored at `~/.mcpindexer/stack.json` and tracks all indexed repositories with their metadata.

For detailed configuration options including environment variables, custom database locations, and advanced features, see [docs/CONFIGURATION.md](docs/CONFIGURATION.md).

## Usage Examples

For detailed usage examples and patterns, see:
- **[examples/README.md](examples/README.md)** - Example scripts and usage patterns
- **[examples/demo.py](examples/demo.py)** - Complete end-to-end demo

Quick example:
```python
import os
from mcpindexer.indexer import MultiRepoIndexer
from mcpindexer.embeddings import EmbeddingStore

# Initialize
db_path = os.getenv("MCP_INDEXER_DB_PATH", os.path.expanduser("~/.mcpindexer/db"))
store = EmbeddingStore(db_path=db_path, collection_name='mcp_code_index')
indexer = MultiRepoIndexer(store)

# Add and index your repository
indexer.add_repo(
    repo_path='/path/to/your/repo',
    repo_name='my-repo',
    auto_index=True
)

# Search
results = store.semantic_search("authentication logic", n_results=10)
```

## Troubleshooting

For common issues and solutions, see [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md).

Quick tips:
- Enable debug logging: `mcpindexer --debug <command>`
- Check installation: `mcpindexer check`
- View logs: `~/.mcpindexer/logs/mcpindexer.log`

## Architecture

For details on the internal architecture, components, and indexing pipeline, see [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

## Testing

```bash
# Activate virtual environment first
source venv/bin/activate

# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_embeddings.py -v

# Run example scripts
python3 examples/demo.py
```

See [TESTING.md](TESTING.md) for the complete testing guide.

## Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for:
- Development setup
- Code style guidelines (black, flake8, isort)
- Testing requirements
- Pull request process
- CI/CD pipeline information

## License

[Add your license here]

## Support

- **Documentation**: See the docs listed at the top of this README
- **Issues**: Report bugs or request features via [GitHub Issues](https://github.com/gkatechis/mcpIndexer/issues)
- **Examples**: Check the `examples/` directory for usage patterns

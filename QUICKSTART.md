# Quick Start Guide

Get mcpIndexer running in under 5 minutes.

## What is mcpIndexer

Semantic code search for AI tools via MCP (Model Context Protocol). Index your code repositories and search them using natural language queries in Claude Code or other MCP clients.

## Installation

```bash

## Clone and run setup

git clone <<<https://github.com/gkatechis/mcpIndexer.git>>>
cd mcpIndexer
./setup.sh

```text

The setup script will:

- Create a virtual environment

- Install all dependencies

- Verify the installation automatically

- Generate MCP configuration

## Quick Commands

```bash

## Activate the environment (if not using mcpindexer-shell alias)

source venv/bin/activate

## Index your first repository

mcpindexer add /path/to/your/repo --name my-repo

## Check what's indexed

mcpindexer status

## Verify everything works

mcpindexer check

```text

## Using with Claude Code

1. Copy the generated `.mcp.json` configuration:

   ```bash
   cat .mcp.json

```text

2. Add the `mcpindexer` server block to your Claude Code config:

   - Location: `~/.claude/claude_desktop_config.json`

   - Or merge into existing MCP servers

3. Restart Claude Code

4. Use MCP tools in Claude Code:

   - "Search for authentication code"

   - "Find the definition of UserService"

   - "Show me all API endpoints"

## Try the Demo

```bash

## Run the interactive demo (no setup required)

python3 examples/demo.py

```text

This demonstrates the full indexing pipeline without requiring you to index your own repositories.

## Next Steps

- **Full documentation:** See [README.md](README.md) for detailed usage

- **Configuration options:** See [docs/CONFIGURATION.md](docs/CONFIGURATION.md)

- **Testing:** See [TESTING.md](TESTING.md) for development setup

- **Examples:** See [examples/README.md](examples/README.md) for advanced usage

## Troubleshooting

### Installation fails

- Ensure Python 3.10+ is installed: `python3 --version`

- Check the [Installation section in README.md](README.md#installation)

### Can't find mcpindexer command

- Activate the virtual environment: `source venv/bin/activate`

- Or use the alias (if added during setup): `mcpindexer-shell`

### MCP not working in Claude Code

- Verify config path: `~/.claude/claude_desktop_config.json`

- Check logs: `mcpindexer --debug check`

- See [Configuration docs](docs/CONFIGURATION.md)

## Getting Help

- Issues: [GitHub Issues](https://github.com/gkatechis/mcpIndexer/issues)

- Documentation: [README.md](README.md)

- Examples: [examples/](examples/)

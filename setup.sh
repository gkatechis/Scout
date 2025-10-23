#!/bin/bash
# Quick-start setup script for mcpIndexer

set -e

echo "========================================"
echo "  mcpIndexer Setup"
echo "========================================"
echo ""

# Detect script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
echo "Installation directory: $SCRIPT_DIR"
echo ""

# Check Python version
echo "Checking Python version..."
if ! command -v python3 &> /dev/null; then
    echo "ERROR: python3 not found. Please install Python 3.8 or higher."
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
echo "Found Python $PYTHON_VERSION"

# Check if version is >= 3.8
if ! python3 -c 'import sys; exit(0 if sys.version_info >= (3, 8) else 1)' 2>/dev/null; then
    echo "ERROR: Python 3.8 or higher required. Found $PYTHON_VERSION"
    exit 1
fi
echo "✓ Python version OK"
echo ""

# Create virtual environment
echo "Creating virtual environment..."
if [ -d "$SCRIPT_DIR/venv" ]; then
    echo "Virtual environment already exists. Skipping..."
else
    python3 -m venv "$SCRIPT_DIR/venv"
    echo "✓ Virtual environment created"
fi
echo ""

# Activate virtual environment
echo "Activating virtual environment..."
source "$SCRIPT_DIR/venv/bin/activate"
echo "✓ Virtual environment activated"
echo ""

# Install dependencies
echo "Installing dependencies..."
pip install --upgrade pip setuptools wheel
pip install -r "$SCRIPT_DIR/requirements.txt"
echo "✓ Dependencies installed"
echo ""

# Install mcpindexer as CLI tool
echo "Installing mcpindexer CLI..."
pip install -e "$SCRIPT_DIR"
echo "✓ mcpindexer CLI installed"
echo ""

# Create .mcp.json if it doesn't exist
if [ ! -f "$SCRIPT_DIR/.mcp.json" ]; then
    echo "Creating .mcp.json configuration..."
    cat > "$SCRIPT_DIR/.mcp.json" <<EOF
{
  "mcpServers": {
    "mcpindexer": {
      "command": "python3",
      "args": [
        "$SCRIPT_DIR/src/mcpindexer/server.py"
      ],
      "env": {
        "PYTHONPATH": "$SCRIPT_DIR/src",
        "MCP_INDEXER_DB_PATH": "~/.mcpindexer/db"
      }
    }
  }
}
EOF
    echo "✓ Created .mcp.json"
else
    echo ".mcp.json already exists. Skipping..."
fi
echo ""

# Create .mcpindexer directory
echo "Creating configuration directory..."
mkdir -p ~/.mcpindexer
echo "✓ Created ~/.mcpindexer"
echo ""

# Create shell profile additions
SHELL_CONFIG=""
if [ -f ~/.bashrc ]; then
    SHELL_CONFIG=~/.bashrc
elif [ -f ~/.zshrc ]; then
    SHELL_CONFIG=~/.zshrc
elif [ -f ~/.bash_profile ]; then
    SHELL_CONFIG=~/.bash_profile
fi

if [ -n "$SHELL_CONFIG" ]; then
    echo "========================================"
    echo "  Environment Variables"
    echo "========================================"
    echo ""
    echo "To use mcpIndexer from anywhere, add these lines to your $SHELL_CONFIG:"
    echo ""
    echo "  export PYTHONPATH=\"$SCRIPT_DIR/src:\$PYTHONPATH\""
    echo "  export MCP_INDEXER_DB_PATH=~/.mcpindexer/db"
    echo ""
    echo "Or run this command to add them automatically:"
    echo ""
    echo "  cat >> $SHELL_CONFIG << 'ENVEOF'"
    echo "  # mcpIndexer"
    echo "  export PYTHONPATH=\"$SCRIPT_DIR/src:\$PYTHONPATH\""
    echo "  export MCP_INDEXER_DB_PATH=~/.mcpindexer/db"
    echo "  ENVEOF"
    echo ""
fi

echo "========================================"
echo "  Setup Complete!"
echo "========================================"
echo ""
echo "Next steps:"
echo ""
echo "1. Try the demo:"
echo "   source $SCRIPT_DIR/venv/bin/activate"
echo "   python3 examples/demo.py"
echo ""
echo "2. Configure your MCP client (e.g., Claude Code):"
echo "   Copy the .mcp.json configuration to your client's config directory"
echo ""
echo "3. Index your first repository:"
echo "   python3 -c \""
echo "   import os"
echo "   from mcpindexer.indexer import MultiRepoIndexer"
echo "   from mcpindexer.embeddings import EmbeddingStore"
echo "   db_path = os.path.expanduser('~/.mcpindexer/db')"
echo "   store = EmbeddingStore(db_path=db_path, collection_name='mcp_code_index')"
echo "   indexer = MultiRepoIndexer(store)"
echo "   indexer.add_repo('/path/to/your/repo', 'repo-name', auto_index=True)"
echo "   \""
echo ""
echo "See README.md for more information."
echo ""

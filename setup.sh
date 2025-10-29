#!/bin/bash
# Quick-start setup script for Scout

set -e

echo "========================================"
echo "  Scout Setup"
echo "========================================"
echo ""

# Detect script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
echo "Installation directory: $SCRIPT_DIR"
echo ""

# Check Python version
echo "Checking Python version..."
if ! command -v python3 &> /dev/null; then
    echo "ERROR: python3 not found. Please install Python 3.10 or higher."
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
echo "Found Python $PYTHON_VERSION"

# Check if version is >= 3.10
if ! python3 -c 'import sys; exit(0 if sys.version_info >= (3, 10) else 1)' 2>/dev/null; then
    echo "ERROR: Python 3.10 or higher required. Found $PYTHON_VERSION"
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

# Install scout as CLI tool
echo "Installing scout CLI..."
pip install -e "$SCRIPT_DIR"
echo "✓ scout CLI installed"
echo ""

# Verify CLI installation
echo "Verifying CLI installation..."
if "$SCRIPT_DIR/venv/bin/python3" -m scout --help > /dev/null 2>&1; then
    echo "✓ CLI verified - 'scout' command is available"
    if "$SCRIPT_DIR/venv/bin/scout" --version > /dev/null 2>&1; then
        echo "✓ Direct command works: scout --help"
    fi
else
    echo "⚠ Warning: CLI verification failed"
    echo "  Try: source venv/bin/activate && python3 -m scout --help"
fi
echo ""

# Create .mcp.json if it doesn't exist
if [ ! -f "$SCRIPT_DIR/.mcp.json" ]; then
    echo "Creating .mcp.json configuration..."
    cat > "$SCRIPT_DIR/.mcp.json" <<EOF
{
  "mcpServers": {
    "scout": {
      "command": "$SCRIPT_DIR/venv/bin/python3",
      "args": [
        "$SCRIPT_DIR/src/scout/server.py"
      ],
      "env": {
        "SCOUT_DB_PATH": "~/.scout/db"
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

# Create .scout directory
echo "Creating configuration directory..."
mkdir -p ~/.scout
echo "✓ Created ~/.scout"
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
    echo "  Shell Integration (Optional)"
    echo "========================================"
    echo ""
    echo "Would you like to add a shell alias for easy venv activation?"
    echo "This will add 'scout-shell' command to $SHELL_CONFIG"
    echo ""
    read -p "Add shell alias? (y/n) " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        ALIAS_LINE="alias scout-shell='source $SCRIPT_DIR/venv/bin/activate'"

        # Check if alias already exists
        if grep -q "scout-shell" "$SHELL_CONFIG" 2>/dev/null; then
            echo "⚠ Alias already exists in $SHELL_CONFIG"
        else
            echo "" >> "$SHELL_CONFIG"
            echo "# Scout virtual environment activation" >> "$SHELL_CONFIG"
            echo "$ALIAS_LINE" >> "$SHELL_CONFIG"
            echo "✓ Added 'scout-shell' alias to $SHELL_CONFIG"
            echo ""
            echo "To use immediately, run: source $SHELL_CONFIG"
            echo "Or restart your terminal"
        fi
    else
        echo "Skipped shell alias setup"
    fi
    echo ""
    echo "Environment variables are OPTIONAL for standard usage."
    echo ""
    echo "Set SCOUT_DB_PATH only if you want a custom database location:"
    echo "  export SCOUT_DB_PATH=~/my-custom-path/db"
    echo ""
    echo "PYTHONPATH is NOT needed since pip install -e was used."
    echo ""
fi

echo "========================================"
echo "  Setup Complete!"
echo "========================================"
echo ""
if grep -q "scout-shell" "$SHELL_CONFIG" 2>/dev/null; then
    echo "To use scout, activate the virtual environment with:"
    echo "  scout-shell"
    echo ""
    echo "Or manually:"
    echo "  source $SCRIPT_DIR/venv/bin/activate"
else
    echo "To use scout, activate the virtual environment:"
    echo "  source $SCRIPT_DIR/venv/bin/activate"
fi
echo ""
echo "========================================"
echo "  Verifying Installation"
echo "========================================"
echo ""
echo "Running installation check..."
echo ""

# Run verification check
if scout check; then
    echo ""
    echo "✓ Installation verified successfully!"
else
    echo ""
    echo "⚠ Warning: Installation verification failed"
    echo "You may need to troubleshoot before using scout"
fi

echo ""
echo "Next steps:"
echo ""
echo "1. Try the demo:"
echo "   python3 examples/demo.py"
echo ""
echo "2. Index your first repository:"
echo "   scout add /path/to/your/repo --name repo-name"
echo ""
echo "3. Check status:"
echo "   scout status"
echo ""
echo "4. Configure your MCP client (e.g., Claude Code):"
echo "   A ready-to-use .mcp.json has been created at:"
echo "   $SCRIPT_DIR/.mcp.json"
echo ""
echo "   For Claude Code, copy this configuration to:"
echo "   ~/.claude/claude_desktop_config.json"
echo ""
echo "   Or merge the 'scout' server block into your existing config"
echo ""
echo "For detailed usage, see README.md"
echo ""

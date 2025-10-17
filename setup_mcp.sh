#!/bin/bash
set -e

echo "Setting up MCP Indexer..."
echo ""

# Set environment
export PYTHONPATH=/Users/gkatechis/Code/mcpIndexer/src
export MCP_INDEXER_DB_PATH=/Users/gkatechis/.mcpindexer/db

# Create db directory
mkdir -p /Users/gkatechis/.mcpindexer

echo "Indexing zendesk_app_framework..."
python3 -c "
from mcpindexer.indexer import MultiRepoIndexer
from mcpindexer.embeddings import EmbeddingStore

store = EmbeddingStore('$MCP_INDEXER_DB_PATH', 'mcp_code_index')
indexer = MultiRepoIndexer(store)

result = indexer.add_repo(
    repo_path='/Users/gkatechis/Code/zendesk/apps/zendesk_app_framework',
    repo_name='zendesk_app_framework',
    auto_index=True
)

print(f'✓ Indexed {result.files_processed} files, {result.chunks_indexed} chunks')
"

echo ""
echo "✓ Setup complete!"
echo ""
echo "Now restart Claude Code and open this project (/Users/gkatechis/Code/mcpIndexer)"
echo "Claude will ask to approve the MCP server - click 'Allow'"
echo ""
echo "Then try asking Claude:"
echo '  "Use semantic_search to find code related to event handling"'
echo '  "What does the EventManager class do?"'
echo ""

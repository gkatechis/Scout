#!/usr/bin/env python3
"""Test chunker on User model"""
import sys
sys.path.insert(0, '/Users/gkatechis/Code/mcpIndexer/src')

from mcpindexer.parser import CodeParser
from mcpindexer.chunker import CodeChunker

parser = CodeParser()
parsed = parser.parse_file('/Users/gkatechis/Code/zendesk/zendesk/components/user/app/models/user.rb')

if parsed:
    chunker = CodeChunker(repo_name='test')
    chunks = chunker.chunk_file(parsed)
    print(f'Total chunks: {len(chunks)}')

    # Find chunks with symbol_name='User'
    user_chunks = [c for c in chunks if c.symbol_name == 'User']
    print(f'\nChunks with symbol_name=User: {len(user_chunks)}')

    for chunk in user_chunks:
        print(f'\n  Type: {chunk.chunk_type}')
        print(f'  Lines: {chunk.start_line}-{chunk.end_line}')
        print(f'  First 200 chars of code:')
        print(f'  {chunk.code_text[:200]}')
else:
    print('Failed to parse file')

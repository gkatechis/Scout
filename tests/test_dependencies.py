"""
Test that all dependencies are installed and working correctly.
Each test validates a specific dependency independently.
"""

import pytest


def test_tree_sitter_import():
    """Test tree-sitter can be imported"""
    import tree_sitter

    # Verify Parser class exists
    assert hasattr(tree_sitter, "Parser")
    assert hasattr(tree_sitter, "Language")


def test_tree_sitter_languages():
    """Test all language parsers are available"""
    import tree_sitter_go
    import tree_sitter_javascript
    import tree_sitter_python
    import tree_sitter_ruby
    import tree_sitter_typescript

    # Verify each language parser has a language function
    assert hasattr(tree_sitter_python, "language")
    assert hasattr(tree_sitter_javascript, "language")
    assert hasattr(tree_sitter_typescript, "language_typescript")
    assert hasattr(tree_sitter_typescript, "language_tsx")
    assert hasattr(tree_sitter_ruby, "language")
    assert hasattr(tree_sitter_go, "language")


def test_chromadb_import():
    """Test ChromaDB can be imported and initialized"""
    import chromadb

    # Create an in-memory client (no persistence)
    client = chromadb.Client()
    assert client is not None

    # Test creating a collection
    collection = client.create_collection(name="test_collection")
    assert collection is not None
    assert collection.name == "test_collection"


def test_sentence_transformers_import():
    """Test sentence-transformers can be imported"""
    from sentence_transformers import SentenceTransformer

    # Just test import, we'll test model loading in a separate test
    assert SentenceTransformer is not None


def test_gitpython_import():
    """Test GitPython can be imported"""
    import git

    # Test basic Git functionality
    assert hasattr(git, "Repo")
    assert hasattr(git, "Git")


def test_pydantic_import():
    """Test Pydantic can be imported"""
    from pydantic import BaseModel, Field

    # Create a simple model to verify it works
    class TestModel(BaseModel):
        name: str
        value: int = Field(default=0)

    instance = TestModel(name="test")
    assert instance.name == "test"
    assert instance.value == 0


def test_mcp_import():
    """Test MCP can be imported"""
    import mcp

    # Verify core MCP components are available
    assert hasattr(mcp, "server")
    assert hasattr(mcp, "types")


def test_tree_sitter_basic_parsing():
    """Test tree-sitter can actually parse code"""
    import tree_sitter_python
    from tree_sitter import Language, Parser, Query, QueryCursor

    # Create parser with Language wrapper
    parser = Parser(Language(tree_sitter_python.language()))

    # Parse simple Python code
    code = b"def hello():\n    print('world')"
    tree = parser.parse(code)

    assert tree is not None
    assert tree.root_node is not None
    assert tree.root_node.type == "module"

    # Query for function definitions
    query = Query(
        Language(tree_sitter_python.language()), "(function_definition) @func"
    )
    cursor = QueryCursor(query)
    captures = cursor.captures(tree.root_node)

    assert captures is not None
    assert "func" in captures
    assert len(captures["func"]) == 1  # Should find one function
    assert captures["func"][0].type == "function_definition"


def test_chromadb_embedding_storage():
    """Test ChromaDB can store and retrieve embeddings"""
    import chromadb
    import numpy as np

    client = chromadb.Client()
    collection = client.create_collection(name="test_embeddings")

    # Add some dummy embeddings
    embeddings = [
        [1.0, 2.0, 3.0],
        [4.0, 5.0, 6.0],
    ]

    collection.add(
        embeddings=embeddings, documents=["doc1", "doc2"], ids=["id1", "id2"]
    )

    # Query the collection
    results = collection.query(query_embeddings=[[1.0, 2.0, 3.0]], n_results=1)

    assert results is not None
    assert len(results["ids"]) == 1
    assert results["ids"][0][0] == "id1"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

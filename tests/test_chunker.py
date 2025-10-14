"""
Tests for the code chunking strategy
"""
import pytest
from mcpindexer.chunker import CodeChunker, CodeChunk
from mcpindexer.parser import CodeParser


# Test code samples
SMALL_PYTHON_CODE = '''
def hello():
    return "world"

def goodbye():
    return "farewell"
'''

MEDIUM_PYTHON_CODE = '''
class UserService:
    def __init__(self):
        self.users = []

    def create_user(self, name: str) -> dict:
        user = {"name": name, "id": len(self.users)}
        self.users.append(user)
        return user

    def get_user(self, user_id: int) -> dict:
        return self.users[user_id] if user_id < len(self.users) else None
'''

LARGE_PYTHON_CODE = '''
class ComplexService:
    """A service with many methods"""

    def __init__(self):
        self.data = []
        self.config = {}

    def method_one(self):
        """ """ * 50  # Make it larger
        return "one"

    def method_two(self):
        """ """ * 50
        return "two"

    def method_three(self):
        """ """ * 50
        return "three"
'''


class TestCodeChunker:
    """Tests for CodeChunker class"""

    def setup_method(self):
        """Set up test fixtures"""
        self.parser = CodeParser()
        self.chunker = CodeChunker(repo_name="test-repo")

    def test_chunker_initialization(self):
        """Test chunker initializes correctly"""
        assert self.chunker.repo_name == "test-repo"
        assert self.chunker.chunk_counter == 0

    def test_chunk_simple_functions(self):
        """Test chunking file with simple functions"""
        parsed = self.parser.parse_file("test.py", SMALL_PYTHON_CODE)
        chunks = self.chunker.chunk_file(parsed)

        assert len(chunks) >= 2  # At least 2 functions

        # Check chunk attributes
        for chunk in chunks:
            assert chunk.repo_name == "test-repo"
            assert chunk.file_path == "test.py"
            assert chunk.language == "python"
            assert chunk.chunk_type in ["function", "class", "file"]
            assert chunk.token_count > 0
            assert len(chunk.code_text) > 0

    def test_chunk_class_with_methods(self):
        """Test chunking class with methods"""
        parsed = self.parser.parse_file("test.py", MEDIUM_PYTHON_CODE)
        chunks = self.chunker.chunk_file(parsed)

        assert len(chunks) >= 1

        # Find the class chunk
        class_chunks = [c for c in chunks if c.chunk_type == "class"]
        if class_chunks:
            chunk = class_chunks[0]
            assert chunk.symbol_name == "UserService"
            assert chunk.parent_class is None
            assert "UserService" in chunk.code_text

    def test_chunk_context_text(self):
        """Test that context text is properly formatted"""
        parsed = self.parser.parse_file("test.py", SMALL_PYTHON_CODE)
        chunks = self.chunker.chunk_file(parsed)

        if chunks:
            chunk = chunks[0]
            assert "File: test.py" in chunk.context_text
            # Should contain either Function or Method
            assert any(keyword in chunk.context_text for keyword in ["Function:", "Method:", "Class:"])

    def test_chunk_ids_are_unique(self):
        """Test that each chunk gets a unique ID"""
        parsed = self.parser.parse_file("test.py", SMALL_PYTHON_CODE)
        chunks = self.chunker.chunk_file(parsed)

        chunk_ids = [c.chunk_id for c in chunks]
        assert len(chunk_ids) == len(set(chunk_ids))  # All unique

    def test_chunk_ids_contain_repo_name(self):
        """Test that chunk IDs contain the repo name"""
        parsed = self.parser.parse_file("test.py", SMALL_PYTHON_CODE)
        chunks = self.chunker.chunk_file(parsed)

        for chunk in chunks:
            assert "test-repo" in chunk.chunk_id

    def test_chunk_imports_preserved(self):
        """Test that import information is preserved in chunks"""
        code_with_imports = '''
import os
from typing import List

def process():
    return os.path.join("a", "b")
'''
        parsed = self.parser.parse_file("test.py", code_with_imports)
        chunks = self.chunker.chunk_file(parsed)

        assert len(chunks) > 0
        # At least one chunk should have imports
        assert any(len(c.imports) > 0 for c in chunks)

    def test_token_estimation(self):
        """Test token count estimation"""
        text = "hello " * 100  # 100 words
        tokens = self.chunker._estimate_tokens(text)

        # Should be roughly in the right ballpark
        assert 100 <= tokens <= 200  # Rough estimate

    def test_chunk_within_target_range(self):
        """Test that chunks are generally within target token range"""
        parsed = self.parser.parse_file("test.py", MEDIUM_PYTHON_CODE)
        chunks = self.chunker.chunk_file(parsed)

        for chunk in chunks:
            # Most chunks should be under max (some might exceed if indivisible)
            if chunk.chunk_type != "file":
                assert chunk.token_count <= self.chunker.TARGET_MAX_TOKENS * 1.5  # Allow some overflow

    def test_empty_file_handling(self):
        """Test handling of empty or minimal files"""
        empty_code = "\n\n# Just a comment\n"
        parsed = self.parser.parse_file("test.py", empty_code)
        chunks = self.chunker.chunk_file(parsed)

        # Should create at least one file-level chunk
        assert len(chunks) >= 1
        assert chunks[0].chunk_type == "file"

    def test_chunk_line_numbers(self):
        """Test that chunks have correct line number ranges"""
        parsed = self.parser.parse_file("test.py", SMALL_PYTHON_CODE)
        chunks = self.chunker.chunk_file(parsed)

        for chunk in chunks:
            assert chunk.start_line >= 0
            assert chunk.end_line >= chunk.start_line

    def test_method_parent_class_tracking(self):
        """Test that methods track their parent class"""
        parsed = self.parser.parse_file("test.py", MEDIUM_PYTHON_CODE)
        chunks = self.chunker.chunk_file(parsed)

        # Check if any method chunks have parent_class set
        method_chunks = [c for c in chunks if c.chunk_type == "function" and c.parent_class]
        # Might be 0 if class is kept as one chunk
        if method_chunks:
            assert method_chunks[0].parent_class == "UserService"

    def test_multiple_files_increment_counter(self):
        """Test that chunk counter increments across multiple files"""
        parsed1 = self.parser.parse_file("test1.py", SMALL_PYTHON_CODE)
        chunks1 = self.chunker.chunk_file(parsed1)

        parsed2 = self.parser.parse_file("test2.py", SMALL_PYTHON_CODE)
        chunks2 = self.chunker.chunk_file(parsed2)

        # Counters should be different
        id1 = chunks1[0].chunk_id.split(":")[-1] if chunks1 else "0"
        id2 = chunks2[0].chunk_id.split(":")[-1] if chunks2 else "0"
        assert id1 != id2

    def test_chunk_with_javascript(self):
        """Test chunking JavaScript code"""
        js_code = '''
class UserService {
    constructor() {
        this.users = [];
    }

    createUser(name) {
        return { name, id: this.users.length };
    }
}
'''
        parsed = self.parser.parse_file("test.js", js_code)
        chunks = self.chunker.chunk_file(parsed)

        assert len(chunks) >= 1
        assert chunks[0].language == "javascript"

    def test_chunk_attributes_complete(self):
        """Test that CodeChunk has all required attributes"""
        parsed = self.parser.parse_file("test.py", SMALL_PYTHON_CODE)
        chunks = self.chunker.chunk_file(parsed)

        if chunks:
            chunk = chunks[0]
            assert hasattr(chunk, 'chunk_id')
            assert hasattr(chunk, 'file_path')
            assert hasattr(chunk, 'repo_name')
            assert hasattr(chunk, 'language')
            assert hasattr(chunk, 'chunk_type')
            assert hasattr(chunk, 'code_text')
            assert hasattr(chunk, 'start_line')
            assert hasattr(chunk, 'end_line')
            assert hasattr(chunk, 'symbol_name')
            assert hasattr(chunk, 'parent_class')
            assert hasattr(chunk, 'imports')
            assert hasattr(chunk, 'context_text')
            assert hasattr(chunk, 'token_count')


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
